"""SimPy resource models for ATL: runways, gates, and aircraft entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import simpy

from .config import AirportConfig

WEIGHT_CLASS_BY_TYPE = {"narrow": "Large", "wide": "Heavy", "heavy": "Heavy"}

# FAA RECAT-1 category mapping from BTS weight classes
_RECAT_CATEGORY: Dict[str, str] = {
    "heavy":  "B",   # Upper Heavy  (B747, B777-300, A380)
    "wide":   "C",   # Lower Heavy  (B767, B787, A330, A350)
    "narrow": "D",   # Upper Medium (B737, A320, B757-200)
}

# RECAT-1 departure time-based separation matrix, seconds
# Key: (leader_cat, follower_cat)
_RECAT_SEP_SEC: Dict[tuple, int] = {
    ("A","A"):180, ("A","B"):180, ("A","C"):180, ("A","D"):120, ("A","E"):120, ("A","F"):120,
    ("B","A"):120, ("B","B"):120, ("B","C"):120, ("B","D"): 90, ("B","E"): 90, ("B","F"): 90,
    ("C","A"): 90, ("C","B"): 90, ("C","C"): 90, ("C","D"): 90, ("C","E"): 90, ("C","F"): 90,
    ("D","A"): 90, ("D","B"): 90, ("D","C"): 90, ("D","D"): 90, ("D","E"): 90, ("D","F"): 90,
    ("E","A"): 90, ("E","B"): 90, ("E","C"): 90, ("E","D"): 90, ("E","E"): 90, ("E","F"): 90,
    ("F","A"): 90, ("F","B"): 90, ("F","C"): 90, ("F","D"): 90, ("F","E"): 90, ("F","F"): 90,
}

# Runway occupancy / takeoff-roll duration by aircraft type (minutes)
_TAKEOFF_ROLL_MIN: Dict[str, float] = {
    "heavy":  1.00,   # ~60 sec
    "wide":   0.83,   # ~50 sec
    "narrow": 0.67,   # ~40 sec
}


@dataclass
class Flight:
    flight_id: str
    airline: str
    flight_number: str
    aircraft_type: str   # narrow | wide
    tail_number: str
    operation: str       # ARR | DEP
    scheduled_min: float
    origin: str
    destination: str
    gate_assigned: str
    concourse: str
    weight_class: str = "Large"

    actual_off_block_min: Optional[float] = None
    actual_runway_min: Optional[float] = None
    taxi_out_min: Optional[float] = None
    taxi_in_min: Optional[float] = None
    gate_delay_min: Optional[float] = None
    edct_delay_min: float = 0.0

    @property
    def is_heavy(self) -> bool:
        return self.weight_class in ("Heavy", "Super")


class ArrivalMeter:
    """
    Token-bucket rate limiter enforcing the FAA nominal arrival acceptance rate.

    Arrivals request a slot before competing for the runway resource.  The
    meter releases one slot every (60 / rate_per_hour) minutes, so the total
    landing rate cannot exceed the FAA-rated throughput even on a fully-loaded
    schedule.  When arrivals arrive faster than the rate, they queue here and
    the delay adds to their runway-wait time.
    """

    def __init__(self, env: simpy.Environment, rate_per_hour: float):
        self.env = env
        self._interval_min = 60.0 / max(1.0, rate_per_hour)
        self._mutex = simpy.Resource(env, capacity=1)
        self._next_slot_min: float = 0.0

    def request_slot(self):
        """SimPy process: wait until a metered arrival slot is available."""
        with self._mutex.request() as req:
            yield req
            wait = max(0.0, self._next_slot_min - self.env.now)
            if wait > 0.0:
                yield self.env.timeout(wait)
            self._next_slot_min = self.env.now + self._interval_min


class DepartureMeter:
    """
    Token-bucket rate limiter enforcing the FAA nominal departure rate.

    Departures request a slot before competing for a runway.  The meter
    releases one slot every (60 / rate_per_hour) minutes, capping total
    departure throughput at the FAA-rated runway capacity.  When more
    departures are ready than the runway system can accept, they queue here
    and the delay accumulates in their runway-wait time.
    """

    def __init__(self, env: simpy.Environment, rate_per_hour: float):
        self.env = env
        self._interval_min = 60.0 / max(1.0, rate_per_hour)
        self._mutex = simpy.Resource(env, capacity=1)
        self._next_slot_min: float = 0.0

    def request_slot(self):
        """SimPy process: wait until a metered departure slot is available."""
        with self._mutex.request() as req:
            yield req
            wait = max(0.0, self._next_slot_min - self.env.now)
            if wait > 0.0:
                yield self.env.timeout(wait)
            self._next_slot_min = self.env.now + self._interval_min


class DepartureRunway:
    """One physical departure runway with RECAT-1 pair-wise separation and type-specific ROT."""

    def __init__(
        self,
        env: simpy.Environment,
        runway_id: str,
        min_inter_dep_min: float = 0.0,
    ):
        self.env = env
        self.runway_id = runway_id
        self.resource = simpy.Resource(env, capacity=1)
        self.min_inter_dep_min = min_inter_dep_min
        self._last_recat_cat: str = "D"  # assume medium until first departure

    @property
    def queue_depth(self) -> int:
        return len(self.resource.queue) + self.resource.count

    def process(self, aircraft_type: str):
        follower_cat = _RECAT_CATEGORY.get(aircraft_type, "D")
        sep_sec = _RECAT_SEP_SEC.get((self._last_recat_cat, follower_cat), 90)
        sep_min = max(sep_sec / 60.0, self.min_inter_dep_min)
        roll_min = _TAKEOFF_ROLL_MIN.get(aircraft_type, 0.75)
        with self.resource.request() as req:
            yield req
            yield self.env.timeout(sep_min + roll_min)
            self._last_recat_cat = follower_cat


class SmartGateHold:
    """
    Dynamic gate-hold metering based on Simaiakis & Balakrishnan (MIT 2012).

    Aircraft poll at the gate while the total departure taxi queue exceeds the
    configured threshold.  Unlike the fixed-capacity dep_taxi_permits pool,
    this responds to actual runway queue depth, preventing taxiway overload
    while burning no fuel and generating no crossing conflicts.
    """

    def __init__(self, env: simpy.Environment, threshold: int, poll_min: float = 1.0):
        self.env = env
        self.threshold = threshold
        self.poll_min = poll_min

    def wait_for_clearance(self, runway_pool: "RunwayPool"):
        """SimPy process: hold at gate while total dep queue >= threshold."""
        while runway_pool.total_dep_queue_depth() >= self.threshold:
            yield self.env.timeout(self.poll_min)


class RunwayPool:
    """Arrival pool + independent per-runway departure queues + taxi permits."""

    def __init__(self, env: simpy.Environment, config: AirportConfig):
        self.env = env
        self.config = config

        arr, dep = [], []
        for name, rw in config.runways.items():
            if rw.primary_use == "arrival":
                arr.append(name)
            elif rw.primary_use == "departure":
                dep.append(name)
            else:
                arr.append(name)
                dep.append(name)

        self.arrival = simpy.Resource(env, capacity=max(1, len(arr)))
        self.arrival_names = arr
        self.arrival_meter = ArrivalMeter(env, config.nominal_arrival_rate_per_hour)
        self.departure_meter = DepartureMeter(env, config.nominal_departure_rate_per_hour)

        num_dep = max(1, len(dep))
        _avg_roll_min = 0.75
        min_inter_dep_min = (
            max(0.0, 60.0 * num_dep / config.nominal_departure_rate_per_hour - _avg_roll_min)
            if config.nominal_departure_rate_per_hour > 0
            else 0.0
        )

        self.dep_runways: List[DepartureRunway] = [
            DepartureRunway(env, runway_id=name, min_inter_dep_min=min_inter_dep_min)
            for name in dep
        ]

        max_q = getattr(config, "departure_max_taxi_queue", 25)
        self.dep_taxi_permits = simpy.Resource(env, capacity=max(1, max_q))

        threshold = getattr(config, "congestion_departure_queue_threshold", 15)
        poll_min = getattr(config, "gate_hold_poll_min", 1.0)
        self.smart_gate_hold = SmartGateHold(env, threshold, poll_min)

    # ------------------------------------------------------------------ #
    # Arrival interface (unchanged)
    # ------------------------------------------------------------------ #

    def occupy_arrival(self, runway_occupancy_min: float = 1.0):
        with self.arrival.request() as req:
            yield req
            yield self.env.timeout(runway_occupancy_min)

    # ------------------------------------------------------------------ #
    # Departure interface
    # ------------------------------------------------------------------ #

    def least_loaded_runway(self) -> DepartureRunway:
        """Return the departure runway with the shortest current queue."""
        return min(self.dep_runways, key=lambda r: r.queue_depth)

    def total_dep_queue_depth(self) -> int:
        return sum(r.queue_depth for r in self.dep_runways)


class GatePool:
    """Per-concourse gate pools modeled as SimPy resources."""

    def __init__(self, env: simpy.Environment, config: AirportConfig):
        self.env = env
        self.config = config
        self.pools: Dict[str, simpy.Resource] = {
            name: simpy.Resource(env, capacity=c.gate_count)
            for name, c in config.concourses.items()
        }

    def pool_for(self, concourse: str) -> simpy.Resource:
        return self.pools.get(concourse) or next(iter(self.pools.values()))

    def utilization_capacity(self) -> Dict[str, int]:
        return {name: p.capacity for name, p in self.pools.items()}
