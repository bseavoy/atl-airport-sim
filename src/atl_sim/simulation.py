"""Core SimPy simulation loop for ATL airport operations."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Dict, List, Optional

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
        # Maps departure flight_id → SimPy Event that succeeds when its
        # inbound rotation (same tail) finishes gate turnaround.
        self._rotation_events: Dict[str, simpy.Event] = {}

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def load_schedule(self, csv_path: str) -> None:
        self._flights = load_schedule(csv_path)
        self._build_rotation_map()

    def run(self, until_min: float = 1440.0) -> SimMetrics:
        for flight in self._flights:
            self.env.process(self._flight_process(flight))
        self.env.process(self._gate_sampler(interval_min=15.0))
        self.env.run(until=until_min)
        return self.metrics

    # ------------------------------------------------------------------ #
    # Rotation map
    # ------------------------------------------------------------------ #

    def _build_rotation_map(self) -> None:
        """
        For each tail number, pair consecutive ARR→DEP flights (by scheduled
        time) into rotation chains.  Each pair shares a single SimPy Event:
        the arrival process succeeds it after gate turnaround; the departure
        process yields on it before starting pushback.
        """
        by_tail: Dict[str, List[Flight]] = defaultdict(list)
        for f in self._flights:
            if f.tail_number and f.tail_number not in ("", "nan"):
                by_tail[f.tail_number].append(f)

        # Maps arrival flight_id → event to succeed after turnaround
        self._arr_signals: Dict[str, simpy.Event] = {}
        # Maps departure flight_id → event to wait on before pushback
        self._rotation_events: Dict[str, simpy.Event] = {}

        for tail, flights in by_tail.items():
            flights_sorted = sorted(flights, key=lambda f: f.scheduled_min)
            # Walk through and pair each ARR with the next DEP on the same tail
            i = 0
            while i < len(flights_sorted) - 1:
                if flights_sorted[i].operation == "ARR":
                    arr = flights_sorted[i]
                    # Find the next DEP after this ARR
                    for j in range(i + 1, len(flights_sorted)):
                        if flights_sorted[j].operation == "DEP":
                            dep = flights_sorted[j]
                            ev = self.env.event()
                            self._arr_signals[arr.flight_id] = ev
                            self._rotation_events[dep.flight_id] = ev
                            i = j  # advance past the paired DEP
                            break
                    else:
                        i += 1
                else:
                    i += 1

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

    def _taxi_out(self, conc) -> float:
        cfg = self.config
        mean = conc.taxi_out_mean_min if conc else 18.0
        if cfg.use_lognormal:
            return max(1.0, _lognorm_sample(self.rng, mean, cfg.taxi_out_lognorm_sigma))
        std = conc.taxi_out_std_min if conc else 5.0
        return max(1.0, float(self.rng.normal(mean, std)))

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
            # Aircraft ready — signal any waiting rotation departure
            signal = self._arr_signals.get(flight.flight_id)
            if signal is not None and not signal.triggered:
                signal.succeed(self.env.now)
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

        # Wait for inbound rotation to complete turnaround before committing to
        # gate holdout / pushback prep.  If the aircraft arrives late, this
        # naturally delays the departure without any lookup table.
        rotation_ev = self._rotation_events.get(flight.flight_id)
        if rotation_ev is not None:
            yield rotation_ev

        gate_holdout = max(
            0.0,
            self.rng_py.gauss(cfg.gate_holdout_mean_min, cfg.gate_holdout_std_min),
        )
        pushback_ready = max(self.env.now, flight.scheduled_min - gate_holdout)
        yield self.env.timeout(max(0.0, pushback_ready - self.env.now))

        pushback_delay = max(
            0.0,
            self.rng_py.gauss(cfg.pushback_clearance_mean_min, cfg.pushback_clearance_std_min),
        )
        yield self.env.timeout(pushback_delay)

        gate_hold_start = self.env.now
        with self.runway_pool.dep_taxi_permits.request() as permit:
            yield permit
            gate_hold_time = self.env.now - gate_hold_start

            taxi_out = self._taxi_out(conc)
            yield self.env.timeout(taxi_out)

            rwy = self.runway_pool.least_loaded_runway()
            rwy_request_t = self.env.now
            yield self.env.process(rwy.process(is_heavy=flight.is_heavy))
            runway_wait = self.env.now - rwy_request_t
            actual_wheels_off = self.env.now

        self.metrics.record_flight(FlightRecord(
            flight_id=flight.flight_id,
            operation="DEP",
            scheduled_min=flight.scheduled_min,
            actual_min=actual_wheels_off,
            taxi_min=taxi_out,
            gate_delay_min=gate_hold_time,
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
