"""Collect and summarise simulation metrics."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np


@dataclass
class FlightRecord:
    flight_id: str
    operation: str          # ARR | DEP
    scheduled_min: float
    actual_min: float       # runway time (arr) or wheels-off (dep)
    gate_in_min: float | None = None   # ARR: time gate occupied
    gate_out_min: float | None = None  # DEP: time gate released
    taxi_min: float | None = None
    gate_delay_min: float = 0.0
    concourse: str = ""
    weight_class: str = ""

    @property
    def delay_min(self) -> float:
        return max(0.0, self.actual_min - self.scheduled_min)


@dataclass
class SimMetrics:
    records: List[FlightRecord] = field(default_factory=list)
    runway_queue_samples: List[tuple] = field(default_factory=list)   # (sim_min, queue_len)
    gate_utilisation_samples: List[tuple] = field(default_factory=list)  # (sim_min, concourse, used, cap)

    # ------------------------------------------------------------------ #
    def record_flight(self, rec: FlightRecord) -> None:
        self.records.append(rec)

    def sample_runway_queue(self, sim_min: float, queue_len: int) -> None:
        self.runway_queue_samples.append((sim_min, queue_len))

    def sample_gate_utilisation(self, sim_min: float, concourse: str, used: int, cap: int) -> None:
        self.gate_utilisation_samples.append((sim_min, concourse, used, cap))

    # ------------------------------------------------------------------ #
    def summary(self) -> Dict:
        arrivals = [r for r in self.records if r.operation == "ARR"]
        departures = [r for r in self.records if r.operation == "DEP"]

        def _stats(delays):
            if not delays:
                return {"mean": 0.0, "p50": 0.0, "p95": 0.0, "max": 0.0}
            a = np.array(delays)
            return {
                "mean": float(np.mean(a)),
                "p50": float(np.percentile(a, 50)),
                "p95": float(np.percentile(a, 95)),
                "max": float(np.max(a)),
            }

        arr_delays = [r.delay_min for r in arrivals]
        dep_delays = [r.delay_min for r in departures]

        gate_util: Dict[str, List[float]] = {}
        for _, conc, used, cap in self.gate_utilisation_samples:
            gate_util.setdefault(conc, []).append(used / cap if cap else 0.0)

        return {
            "flights_simulated": len(self.records),
            "arrivals": len(arrivals),
            "departures": len(departures),
            "arrival_delay": _stats(arr_delays),
            "departure_delay": _stats(dep_delays),
            "gate_utilisation": {
                k: round(float(np.mean(v)), 3) for k, v in gate_util.items()
            },
        }
