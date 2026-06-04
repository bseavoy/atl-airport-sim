"""SimPy resource models for ATL: runways, gates, and aircraft entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import simpy

from .config import AirportConfig

# Wake-turbulence weight classes used for runway separation.
WEIGHT_CLASS_BY_TYPE = {"narrow": "Large", "wide": "Heavy", "heavy": "Heavy"}


@dataclass
class Flight:
    """A single scheduled flight leg (one arrival or one departure)."""

    flight_id: str
    airline: str
    flight_number: str
    aircraft_type: str  # narrow | wide
    tail_number: str
    operation: str  # ARR | DEP
    scheduled_min: float  # minutes from midnight
    origin: str
    destination: str
    gate_assigned: str
    concourse: str
    weight_class: str = "Large"  # Small | Large | Heavy | Super

    # Filled in during simulation:
    actual_off_block_min: Optional[float] = None
    actual_runway_min: Optional[float] = None
    taxi_out_min: Optional[float] = None
    taxi_in_min: Optional[float] = None
    gate_delay_min: Optional[float] = None
    edct_delay_min: float = 0.0

    @property
    def is_heavy(self) -> bool:
        return self.weight_class in ("Heavy", "Super")


class RunwayPool:
    """Pool of runways split into arrival and departure roles.

    Departures enforce a minimum separation between successive releases, with a
    larger gap behind a heavy aircraft (wake turbulence).
    """

    def __init__(self, env: simpy.Environment, config: AirportConfig):
        self.env = env
        self.config = config
        arr, dep = [], []
        for name, rw in config.runways.items():
            if rw.primary_use == "arrival":
                arr.append(name)
            elif rw.primary_use == "departure":
                dep.append(name)
            else:  # mixed
                arr.append(name)
                dep.append(name)
        self.arrival = simpy.Resource(env, capacity=max(1, len(arr)))
        self.departure = simpy.Resource(env, capacity=max(1, len(dep)))
        self.arrival_names = arr
        self.departure_names = dep
        # Serializes the separation gate so only one departure clears at a time.
        self._dep_release = simpy.Resource(env, capacity=1)
        self._last_dep_was_heavy = False

    def departure_separation_min(self, behind_heavy: bool) -> float:
        sep = self.config.separation
        secs = sep.heavy_behind_heavy_sec if behind_heavy else sep.default_separation_sec
        return secs / 60.0

    def occupy_arrival(self, runway_occupancy_min: float = 1.0):
        """Process: hold an arrival runway for landing rollout."""
        with self.arrival.request() as req:
            yield req
            yield self.env.timeout(runway_occupancy_min)

    def release_departure(self, is_heavy: bool, takeoff_roll_min: float = 0.75):
        """Process: take a departure slot honoring separation minima."""
        with self._dep_release.request() as gate:
            yield gate
            with self.departure.request() as req:
                yield req
                yield self.env.timeout(
                    self.departure_separation_min(self._last_dep_was_heavy)
                )
                yield self.env.timeout(takeoff_roll_min)
                self._last_dep_was_heavy = is_heavy


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
