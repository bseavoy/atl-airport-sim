"""CLI entry point for the ATL airport simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from src.atl_sim import AirportSimulation, load_config
from src.atl_sim.config import AirportConfig
from src.atl_sim.metrics import SimMetrics


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="ATL Airport Discrete-Event Simulation")
    p.add_argument(
        "--schedule",
        default="data/validation/sample_june1_2025.csv",
        help="Path to flight schedule CSV",
    )
    p.add_argument(
        "--config",
        default="data/airport/atl_config.json",
        help="Path to airport config JSON",
    )
    p.add_argument(
        "--until",
        type=float,
        default=1440.0,
        help="Simulate up to this many minutes from midnight (default: 1440 = full day)",
    )
    p.add_argument("--seed", type=int, default=42, help="Random seed")
    p.add_argument("--output", help="Write summary JSON to this path")
    p.add_argument("--validate", action="store_true", help="Print validation table vs ATL BTS benchmarks")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    sim = AirportSimulation(config=config, seed=args.seed)
    sim.load_schedule(args.schedule)

    print(f"Running simulation (until={args.until:.0f} min, seed={args.seed})...")
    metrics = sim.run(until_min=args.until)
    summary = metrics.summary()

    print(json.dumps(summary, indent=2))

    if args.validate:
        _print_validation(metrics, config)

    if args.output:
        Path(args.output).write_text(json.dumps(summary, indent=2))
        print(f"\nSummary written to {args.output}")


def _print_validation(metrics: SimMetrics, config: AirportConfig) -> None:
    bench = config  # taxi benchmarks live on the config object via concourse means
    # Collect overall weighted benchmarks from all concourses
    total_gates = sum(c.gate_count for c in config.concourses.values())
    bench_taxi_in_mean = sum(
        c.taxi_in_mean_min * c.gate_count for c in config.concourses.values()
    ) / total_gates
    bench_taxi_in_std = 3.2   # ATL BTS overall
    bench_taxi_out_mean = sum(
        c.taxi_out_mean_min * c.gate_count for c in config.concourses.values()
    ) / total_gates
    bench_taxi_out_std = 7.1  # ATL BTS overall

    arrivals = [r for r in metrics.records if r.operation == "ARR" and r.taxi_min is not None]
    departures = [r for r in metrics.records if r.operation == "DEP" and r.taxi_min is not None]

    sim_ti_mean = float(np.mean([r.taxi_min for r in arrivals])) if arrivals else 0.0
    sim_ti_std  = float(np.std([r.taxi_min for r in arrivals]))  if arrivals else 0.0
    sim_to_mean = float(np.mean([r.taxi_min for r in departures])) if departures else 0.0
    sim_to_std  = float(np.std([r.taxi_min for r in departures]))  if departures else 0.0

    def _verdict(sim_val, target, tol):
        return "PASS" if abs(sim_val - target) <= tol else "FAIL"

    rows = [
        ("taxi-in mean (min)",  sim_ti_mean,  bench_taxi_in_mean,  1.5),
        ("taxi-in std (min)",   sim_ti_std,   bench_taxi_in_std,   1.5),
        ("taxi-out mean (min)", sim_to_mean,  bench_taxi_out_mean, 2.5),
        ("taxi-out std (min)",  sim_to_std,   bench_taxi_out_std,  2.5),
    ]

    print("\n" + "=" * 62)
    print(f"{'VALIDATION':^62}")
    print("=" * 62)
    print(f"{'Metric':<24} {'Simulated':>10} {'Target':>10} {'Dev%':>7} {'':>6}")
    print("-" * 62)
    for label, sim_val, target, tol in rows:
        dev_pct = (sim_val - target) / target * 100 if target else 0.0
        verdict = _verdict(sim_val, target, tol)
        print(f"{label:<24} {sim_val:>10.2f} {target:>10.2f} {dev_pct:>+7.1f}% {verdict:>4}")
    print("=" * 62)


if __name__ == "__main__":
    main()
