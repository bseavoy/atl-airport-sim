"""Core SimPy simulation loop for ATL airport operations."""

from __future__ import annotations

import random
from typing import List, Optional

import numpy as np
import simpy

from .config import AirportConfig, load_config
from .metrics import FlightRecord, SimMetrics
from .resources import Flight, GatePool, RunwayPool
from .schedule import load_schedule


class AirportSimulation:
    def __init__(
        self,
        config: Optional[AirportConfig] = None,
        config_path: Optional[str] = None,
        seed: int = 42,
    ):
        self.config = config or load_config(config_path)
        self.rng = random.Random(seed)
        np.random.seed(seed)
        self.env = simpy.Environment()
        self.runway_pool = RunwayPool(self.env, self.config)
        self.gate_pool = GatePool(self.env, self.config)
        self.metrics = SimMetrics()
        self._flights: List[Flight] = []

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def load_schedule(self, csv_path: str) -> None:
        self._flights = load_schedule(csv_path)

    def run(self, until_min: float = 1440.0) -> SimMetrics:
        """Run simulation up to `until_min` minutes from midnight."""
        for flight in self._flights:
            self.env.process(self._flight_process(flight))

        # Periodic gate-utilisation sampling every 15 minutes.
        self.env.process(self._gate_sampler(interval_min=15.0))

        self.env.run(until=until_min)
        return self.metrics

    # ------------------------------------------------------------------ #
    # Internal processes
    # ------------------------------------------------------------------ #

    def _flight_process(self, flight: Flight):
        if flight.operation == "ARR":
            yield from self._arrival(flight)
        else:
            yield from self._departure(flight)

    def _arrival(self, flight: Flight):
        cfg = self.config
        conc = self.config.concourses.get(flight.concourse)

        # Wait until the scheduled arrival time.
        yield self.env.timeout(max(0.0, flight.scheduled_min - self.env.now))

        # Land: request an arrival runway slot.
        runway_start = self.env.now
        with self.runway_pool.arrival.request() as req:
            yield req
            runway_time = self.env.now
            # Runway occupancy ~1 min (roll-out).
            yield self.env.timeout(1.0)

        # Taxi in.
        if conc:
            taxi_in = max(
                1.0,
                self.rng.gauss(conc.taxi_in_mean_min, conc.taxi_in_std_min),
            )
        else:
            taxi_in = max(1.0, self.rng.gauss(cfg.pushback_clearance_mean_min, 2.0))

        yield self.env.timeout(taxi_in)

        # Occupy gate for turnaround.
        gate_pool = self.gate_pool.pool_for(flight.concourse)
        turnaround = (
            cfg.turnaround_wide_min
            if flight.aircraft_type == "wide"
            else cfg.turnaround_narrow_min
        )
        gate_in = self.env.now
        with gate_pool.request() as req:
            yield req
            yield self.env.timeout(turnaround)
        gate_out = self.env.now

        self.metrics.record_flight(
            FlightRecord(
                flight_id=flight.flight_id,
                operation="ARR",
                scheduled_min=flight.scheduled_min,
                actual_min=runway_time,
                gate_in_min=gate_in,
                gate_out_min=gate_out,
                taxi_min=taxi_in,
                concourse=flight.concourse,
                weight_class=flight.weight_class,
            )
        )

    def _departure(self, flight: Flight):
        cfg = self.config
        conc = self.config.concourses.get(flight.concourse)

        # Gate hold-out before pushback clearance.
        gate_holdout = max(
            0.0,
            self.rng.gauss(cfg.gate_holdout_mean_min, cfg.gate_holdout_std_min),
        )
        pushback_ready = flight.scheduled_min - gate_holdout
        yield self.env.timeout(max(0.0, pushback_ready - self.env.now))

        # Pushback clearance delay.
        pushback_delay = max(
            0.0,
            self.rng.gauss(cfg.pushback_clearance_mean_min, cfg.pushback_clearance_std_min),
        )
        yield self.env.timeout(pushback_delay)

        # Taxi out.
        if conc:
            taxi_out = max(
                1.0,
                self.rng.gauss(conc.taxi_out_mean_min, conc.taxi_out_std_min),
            )
        else:
            taxi_out = max(1.0, self.rng.gauss(18.0, 5.0))

        yield self.env.timeout(taxi_out)

        # Line up and depart with wake-turbulence separation.
        wheels_off = self.env.now
        yield self.env.process(
            self.runway_pool.release_departure(is_heavy=flight.is_heavy)
        )
        actual_wheels_off = self.env.now

        self.metrics.record_flight(
            FlightRecord(
                flight_id=flight.flight_id,
                operation="DEP",
                scheduled_min=flight.scheduled_min,
                actual_min=actual_wheels_off,
                taxi_min=taxi_out,
                gate_delay_min=max(0.0, actual_wheels_off - flight.scheduled_min),
                concourse=flight.concourse,
                weight_class=flight.weight_class,
            )
        )

    def _gate_sampler(self, interval_min: float = 15.0):
        while True:
            yield self.env.timeout(interval_min)
            for name, pool in self.gate_pool.pools.items():
                used = pool.count
                cap = pool.capacity
                self.metrics.sample_gate_utilisation(self.env.now, name, used, cap)
