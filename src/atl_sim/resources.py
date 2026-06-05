"""SimPy resource models for ATL: runways, gates, and aircraft entities."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import simpy

from .config import AirportConfig

WEIGHT_CLASS_BY_TYPE = {"narrow": "Large", "wide": "Heavy", "heavy": "Heavy"}


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


class DepartureRunway:
    """One physical departure runway with its own queue and separation state."""

    def __init__(
        self,
        env: simpy.Environment,
        runway_id: str,
        default_sep_sec: int = 60,
        heavy_sep_sec: int = 90,
        takeoff_roll_min: float = 0.75,
    ):
        self.env = env
        self.runway_id = runway_id
        self.resource = simpy.Resource(env, capacity=1)
        self.default_sep_sec = default_sep_sec
        self.heavy_sep_sec = heavy_sep_sec
        self.takeoff_roll_min = takeoff_roll_min
        self._last_was_heavy = False

    @property
    def queue_depth(self) -> int:
        """Aircraft waiting + currently using this runway."""
        return len(self.resource.queue) + self.resource.count

    def process(self, is_heavy: bool):
        """SimPy process: acquire runway, enforce separation, take off."""
        sep_min = (
            self.heavy_sep_sec if self._last_was_heavy else self.default_sep_sec
        ) / 60.0
        with self.resource.request() as req:
            yield req
            yield self.env.timeout(sep_min + self.takeoff_roll_min)
            self._last_was_heavy = is_heavy


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

        sep = config.separation
        self.dep_runways: List[DepartureRunway] = [
            DepartureRunway(
                env,
                runway_id=name,
                default_sep_sec=sep.default_separation_sec,
                heavy_sep_sec=sep.heavy_behind_heavy_sec,
            )
            for name in dep
        ]

        # Gate-hold permit pool: limits total aircraft in the departure taxi
        # system (taxiing + waiting for runway) across the whole airport.
        # Flights hold at the gate until a permit is free.
        max_q = getattr(config, "departure_max_taxi_queue", 25)
        self.dep_taxi_permits = simpy.Resource(env, capacity=max(1, max_q))

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
