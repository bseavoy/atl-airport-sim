"""Core SimPy simulation loop for ATL airport operations."""

from __future__ import annotations

import math
import random
from typing import List, Optional

import numpy as np
import simpy

from .config import AirportConfig, load_config
from .metrics import FlightRecord, SimMetrics
from .resources import Flight, GatePool, RunwayPool
from .schedule import load_schedule


def _lognorm_sample(rng: np.random.Generator, mean: float, sigma: float) -> float:
    """Sample from a log-normal with the given mean and log-scale sigma.

    sigma is the std-dev of the underlying normal (shape parameter).
    mu of the underlying normal is derived so E[X] = mean.
    """
    mu = math.log(mean) - 0.5 * sigma ** 2
    return float(np.exp(rng.normal(mu, sigma)))


class AirportSimulation:
    def __init__(
        self,
        config: Optional[AirportConfig] = None,
        config_path: Optional[str] = None,
        seed: int = 42,
    ):
        self.config = config or load_config(config_path)
        self.rng_py = random.Random(seed)
        self.rng = np.random.default_rng(seed)
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
        for flight in self._flights:
            self.env.process(self._flight_process(flight))
        self.env.process(self._gate_sampler(interval_min=15.0))
        self.env.run(until=until_min)
        return self.metrics

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _taxi_in(self, conc) -> float:
        cfg = self.config
        if conc:
            mean = conc.taxi_in_mean_min
        else:
            mean = cfg.pushback_clearance_mean_min
        if cfg.use_lognormal:
            return max(1.0, _lognorm_sample(self.rng, mean, cfg.taxi_in_lognorm_sigma))
        return max(1.0, float(self.rng.normal(mean, conc.taxi_in_std_min if conc else 2.0)))

    def _taxi_out(self, conc, scheduled_min: float) -> float:
        cfg = self.config
        mean = conc.taxi_out_mean_min if conc else 18.0
        hour = int(scheduled_min) // 60 % 24
        multiplier = cfg.taxi_out_hourly_multipliers.get(hour, 1.0)
        effective_mean = mean * multiplier
        if cfg.use_lognormal:
            return max(1.0, _lognorm_sample(self.rng, effective_mean, cfg.taxi_out_lognorm_sigma))
        std = conc.taxi_out_std_min if conc else 5.0
        return max(1.0, float(self.rng.normal(effective_mean, std)))

    # ------------------------------------------------------------------ #
    # SimPy processes
    # ------------------------------------------------------------------ #

    def _flight_process(self, flight: Flight):
        if flight.operation == "ARR":
            yield from self._arrival(flight)
        else:
            yield from self._departure(flight)

    def _arrival(self, flight: Flight):
        cfg = self.config
        conc = cfg.concourses.get(flight.concourse)

        yield self.env.timeout(max(0.0, flight.scheduled_min - self.env.now))

        # Queue for arrival runway — measure wait.
        rwy_request_t = self.env.now
        with self.runway_pool.arrival.request() as req:
            yield req
            runway_wait = self.env.now - rwy_request_t
            runway_time = self.env.now
            yield self.env.timeout(1.0)  # runway roll-out occupancy

        taxi_in = self._taxi_in(conc)
        yield self.env.timeout(taxi_in)

        gate_pool = self.gate_pool.pool_for(flight.concourse)
        turnaround = (
            cfg.turnaround_wide_min if flight.aircraft_type == "wide"
            else cfg.turnaround_narrow_min
        )
        gate_in = self.env.now
        with gate_pool.request() as req:
            yield req
            yield self.env.timeout(turnaround)
        gate_out = self.env.now

        self.metrics.record_flight(FlightRecord(
            flight_id=flight.flight_id,
            operation="ARR",
            scheduled_min=flight.scheduled_min,
            actual_min=runway_time,
            gate_in_min=gate_in,
            gate_out_min=gate_out,
            taxi_min=taxi_in,
            runway_wait_min=runway_wait,
            concourse=flight.concourse,
            weight_class=flight.weight_class,
        ))

    def _departure(self, flight: Flight):
        cfg = self.config
        conc = cfg.concourses.get(flight.concourse)

        gate_holdout = max(
            0.0,
            self.rng_py.gauss(cfg.gate_holdout_mean_min, cfg.gate_holdout_std_min),
        )
        pushback_ready = flight.scheduled_min - gate_holdout
        yield self.env.timeout(max(0.0, pushback_ready - self.env.now))

        pushback_delay = max(
            0.0,
            self.rng_py.gauss(cfg.pushback_clearance_mean_min, cfg.pushback_clearance_std_min),
        )
        yield self.env.timeout(pushback_delay)

        taxi_out = self._taxi_out(conc, flight.scheduled_min)
        yield self.env.timeout(taxi_out)

        # Queue for departure runway — measure wait.
        rwy_request_t = self.env.now
        yield self.env.process(
            self.runway_pool.release_departure(is_heavy=flight.is_heavy)
        )
        runway_wait = self.env.now - rwy_request_t
        actual_wheels_off = self.env.now

        self.metrics.record_flight(FlightRecord(
            flight_id=flight.flight_id,
            operation="DEP",
            scheduled_min=flight.scheduled_min,
            actual_min=actual_wheels_off,
            taxi_min=taxi_out,
            gate_delay_min=max(0.0, actual_wheels_off - flight.scheduled_min),
            runway_wait_min=runway_wait,
            concourse=flight.concourse,
            weight_class=flight.weight_class,
        ))

    def _gate_sampler(self, interval_min: float = 15.0):
        while True:
            yield self.env.timeout(interval_min)
            for name, pool in self.gate_pool.pools.items():
                self.metrics.sample_gate_utilisation(
                    self.env.now, name, pool.count, pool.capacity
                )
