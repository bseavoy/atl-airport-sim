"""Validation helpers: compare simulation output against observed schedule data."""

from __future__ import annotations

import pandas as pd

from src.atl_sim.metrics import SimMetrics


def compare_to_observed(metrics: SimMetrics, observed_csv: str) -> pd.DataFrame:
    """Return a DataFrame comparing simulated vs observed delays.

    The observed CSV must have columns: flight_id, actual_time (HH:MM).
    """
    obs = pd.read_csv(observed_csv, dtype=str)

    def _hhmm(v: str) -> float:
        h, m = str(v).strip().split(":")
        return int(h) * 60 + int(m)

    obs["observed_min"] = obs["actual_time"].apply(_hhmm)
    obs_map = dict(zip(obs["flight_id"], obs["observed_min"]))

    rows = []
    for rec in metrics.records:
        observed = obs_map.get(rec.flight_id)
        rows.append(
            {
                "flight_id": rec.flight_id,
                "operation": rec.operation,
                "scheduled_min": rec.scheduled_min,
                "simulated_min": rec.actual_min,
                "observed_min": observed,
                "sim_delay": rec.delay_min,
                "obs_delay": (observed - rec.scheduled_min) if observed else None,
            }
        )

    return pd.DataFrame(rows)
