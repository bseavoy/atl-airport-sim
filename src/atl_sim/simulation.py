"""Core SimPy simulation loop for ATL airport operations."""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Dict, List, Optional

import numpy as np
import simpy

from .config import AirportConfig, GroundProgram, load_config
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
        ground_programs: Optional[List[GroundProgram]] = None,
    ):
        self.config = config or load_config(config_path)
        self.rng_py = random.Random(seed)
        self.rng = np.random.default_rng(seed)
        self.env = simpy.Environment()
        self.runway_pool = RunwayPool(self.env, self.config)
        self.gate_pool = GatePool(self.env, self.config)
        self.metrics = SimMetrics()
        self._flights: List[Flight] = []
        self.ground_programs: List[GroundProgram] = ground_programs or []
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
    # Ground program helpers
    # ------------------------------------------------------------------ #

    def _active_program(self, sim_min: float) -> Optional[GroundProgram]:
        """Return the first ground program active at sim_min, or None."""
        for p in self.ground_programs:
            if p.start_min <= sim_min < p.end_min:
                return p
        return None

    def _arr_spacing_overhead(self, program: GroundProgram) -> float:
        """Extra inter-arrival spacing (min) needed to hit the GDP rate cap."""
        if program.arr_rate_per_hour <= 0:
            return 0.0
        nominal = self.config.nominal_arrival_rate_per_hour
        gap_normal = 60.0 / nominal
        gap_gdp = 60.0 / program.arr_rate_per_hour
        return max(0.0, gap_gdp - gap_normal)

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

    def _taxi_out(self, conc, queue_depth: int = 0) -> float:
        cfg = self.config
        base_mean = conc.taxi_out_mean_min if conc else 18.0
        hour = int(self.env.now / 60) % 24
        scale = cfg.hourly_taxi_out_scale.get(hour, 1.0)
        mean = base_mean * scale + cfg.taxi_out_congestion_alpha * queue_depth
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

        # Back-calculate a randomised wheels-on time from the scheduled gate arrival.
        # taxi_in_offset: expected taxi time (same distribution as actual taxi-in)
        # padding: per-flight sample of airline schedule buffer above expected taxi
        # Together they model that scheduled gate arrival = wheels_on + taxi + buffer,
        # so wheels_on = scheduled_gate - taxi_offset - padding_sample.
        taxi_in_offset = self._taxi_in(conc)
        airline_pad = cfg.airline_padding_overrides.get(flight.airline)
        pad_mean = airline_pad[0] if airline_pad is not None else cfg.arr_schedule_padding_mean_min
        pad_std  = airline_pad[1] if airline_pad is not None else cfg.arr_schedule_padding_std_min
        padding = max(0.0, self.rng_py.gauss(pad_mean, pad_std)) if pad_mean > 0 else 0.0
        wheels_on_trigger = max(0.0, flight.scheduled_min - taxi_in_offset - padding)
        yield self.env.timeout(max(0.0, wheels_on_trigger - self.env.now))

        # GDP arrival rate cap: add TRACON metering delay before runway request.
        program = self._active_program(self.env.now)
        if program is not None:
            overhead = self._arr_spacing_overhead(program)
            if overhead > 0.0:
                yield self.env.timeout(
                    max(0.0, float(self.rng.exponential(overhead)))
                )

        yield self.env.process(self.runway_pool.arrival_meter.request_slot())

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
        dep_pad_mean = cfg.dep_schedule_padding_mean_min
        dep_pad_std = cfg.dep_schedule_padding_std_min
        dep_pad = max(0.0, self.rng_py.gauss(dep_pad_mean, dep_pad_std)) if dep_pad_mean > 0 else 0.0
        pushback_ready = max(self.env.now, flight.scheduled_min - gate_holdout - dep_pad)
        yield self.env.timeout(max(0.0, pushback_ready - self.env.now))

        pushback_delay = max(
            0.0,
            self.rng_py.gauss(cfg.pushback_clearance_mean_min, cfg.pushback_clearance_std_min),
        )
        yield self.env.timeout(pushback_delay)

        # Smart gate hold: hold at gate while runway queue exceeds threshold
        gate_hold_start = self.env.now
        yield self.env.process(
            self.runway_pool.smart_gate_hold.wait_for_clearance(self.runway_pool)
        )
        with self.runway_pool.dep_taxi_permits.request() as permit:
            yield permit
            gate_hold_time = self.env.now - gate_hold_start
            pushback_min = self.env.now  # actual gate pushback (permit acquired)

            queue_depth_at_pushback = self.runway_pool.total_dep_queue_depth()
            taxi_out = self._taxi_out(conc, queue_depth=queue_depth_at_pushback)
            yield self.env.timeout(taxi_out)

            # GDP departure clearance hold: aircraft reaches runway threshold
            # but ATC holds it for traffic management / weather.
            clearance_hold = 0.0
            program = self._active_program(self.env.now)
            if program is not None and program.dep_clearance_hold_mean_min > 0:
                clearance_hold = min(
                    program.dep_clearance_hold_max_min,
                    max(0.0, self.rng_py.gauss(
                        program.dep_clearance_hold_mean_min,
                        program.dep_clearance_hold_std_min,
                    )),
                )
                yield self.env.timeout(clearance_hold)

            meter_request_t = self.env.now
            yield self.env.process(self.runway_pool.departure_meter.request_slot())
            meter_wait = self.env.now - meter_request_t
            rwy = self.runway_pool.least_loaded_runway()
            rwy_request_t = self.env.now
            yield self.env.process(rwy.process(aircraft_type=flight.aircraft_type))
            runway_wait = self.env.now - rwy_request_t
            actual_wheels_off = self.env.now

        self.metrics.record_flight(FlightRecord(
            flight_id=flight.flight_id,
            operation="DEP",
            scheduled_min=flight.scheduled_min,
            actual_min=actual_wheels_off,
            taxi_min=taxi_out + clearance_hold + meter_wait,
            gate_delay_min=gate_hold_time,
            pushback_min=pushback_min,
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
