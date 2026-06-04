"""Basic smoke tests for the ATL airport simulation."""

from __future__ import annotations

import os
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _sim(schedule="data/validation/sample_june1_2025.csv", until=720.0, seed=0):
    from src.atl_sim import AirportSimulation, load_config

    config = load_config(os.path.join(REPO_ROOT, "data/airport/atl_config.json"))
    sim = AirportSimulation(config=config, seed=seed)
    sim.load_schedule(os.path.join(REPO_ROOT, schedule))
    return sim.run(until_min=until)


def test_simulation_runs():
    metrics = _sim()
    assert metrics is not None


def test_flights_recorded():
    metrics = _sim()
    assert len(metrics.records) > 0


def test_arrivals_and_departures():
    metrics = _sim()
    ops = {r.operation for r in metrics.records}
    assert "ARR" in ops
    assert "DEP" in ops


def test_no_negative_delays():
    metrics = _sim()
    for rec in metrics.records:
        assert rec.delay_min >= 0, f"{rec.flight_id} has negative delay"


def test_summary_keys():
    metrics = _sim()
    summary = metrics.summary()
    for key in ("flights_simulated", "arrivals", "departures", "arrival_delay", "departure_delay"):
        assert key in summary


def test_gate_utilisation_sampled():
    metrics = _sim()
    summary = metrics.summary()
    assert len(summary["gate_utilisation"]) > 0


def test_full_day():
    metrics = _sim(until=1440.0)
    summary = metrics.summary()
    assert summary["flights_simulated"] > 0
