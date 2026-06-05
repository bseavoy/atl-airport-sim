"""
Run the sim against a real BTS day file and compare simulated vs actual taxi times.

Usage:
    python scripts/validate_real_day.py data/real_days/2024-07-09_atl.csv
    python scripts/validate_real_day.py --all          # runs all days in manifest
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.atl_sim import AirportSimulation, load_config

MANIFEST = Path("data/real_days/manifest.json")
CONFIG_PATH = Path("data/atl_config.json")


def run_day(csv_path: Path, seed: int = 42) -> dict:
    config = load_config(str(CONFIG_PATH))
    sim = AirportSimulation(config=config, seed=seed)
    sim.load_schedule(str(csv_path))
    metrics = sim.run(until_min=1500.0)  # slight buffer past midnight

    # Ground truth from the real-day file
    real = pd.read_csv(csv_path)
    real_arr = real[(real["operation"] == "ARR") & real["actual_taxi_min"].notna()]
    real_dep = real[(real["operation"] == "DEP") & real["actual_taxi_min"].notna()]

    # Simulated taxi times
    sim_arr = [r.taxi_min for r in metrics.records if r.operation == "ARR" and r.taxi_min]
    sim_dep = [r.taxi_min for r in metrics.records if r.operation == "DEP" and r.taxi_min]

    def _stats(vals):
        if not vals:
            return {"mean": None, "std": None, "p50": None, "p95": None}
        a = np.array(vals)
        return {
            "mean": round(float(np.mean(a)), 2),
            "std": round(float(np.std(a)), 2),
            "p50": round(float(np.percentile(a, 50)), 2),
            "p95": round(float(np.percentile(a, 95)), 2),
        }

    return {
        "date": csv_path.stem.replace("_atl", ""),
        "flights_in_file": len(real),
        "flights_simulated": len(metrics.records),
        "taxi_in": {
            "actual": _stats(real_arr["actual_taxi_min"].tolist()),
            "simulated": _stats(sim_arr),
        },
        "taxi_out": {
            "actual": _stats(real_dep["actual_taxi_min"].tolist()),
            "simulated": _stats(sim_dep),
        },
    }


def print_report(result: dict) -> None:
    date = result["date"]
    print(f"\n{'='*66}")
    print(f"  {date}  |  {result['flights_simulated']}/{result['flights_in_file']} flights simulated")
    print(f"{'='*66}")
    print(f"{'Metric':<28} {'Actual':>10} {'Simulated':>10} {'Delta':>8}")
    print(f"{'-'*66}")

    def _row(label, actual_val, sim_val):
        if actual_val is None or sim_val is None:
            print(f"{label:<28} {'N/A':>10} {'N/A':>10} {'N/A':>8}")
            return
        delta = sim_val - actual_val
        print(f"{label:<28} {actual_val:>10.2f} {sim_val:>10.2f} {delta:>+8.2f}")

    ti_a = result["taxi_in"]["actual"]
    ti_s = result["taxi_in"]["simulated"]
    to_a = result["taxi_out"]["actual"]
    to_s = result["taxi_out"]["simulated"]

    _row("taxi-in mean (min)", ti_a["mean"], ti_s["mean"])
    _row("taxi-in std (min)", ti_a["std"], ti_s["std"])
    _row("taxi-in p50 (min)", ti_a["p50"], ti_s["p50"])
    _row("taxi-in p95 (min)", ti_a["p95"], ti_s["p95"])
    print(f"{'-'*66}")
    _row("taxi-out mean (min)", to_a["mean"], to_s["mean"])
    _row("taxi-out std (min)", to_a["std"], to_s["std"])
    _row("taxi-out p50 (min)", to_a["p50"], to_s["p50"])
    _row("taxi-out p95 (min)", to_a["p95"], to_s["p95"])
    print(f"{'='*66}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv", nargs="?", help="Path to a real-day CSV file")
    p.add_argument("--all", action="store_true", help="Run all days in manifest")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--output", help="Write JSON results to this path")
    args = p.parse_args()

    if args.all:
        if not MANIFEST.exists():
            print("No manifest found — run fetch_bts_data.py first")
            return
        entries = json.loads(MANIFEST.read_text())
        paths = [Path("data/real_days") / e["file"] for e in entries]
    elif args.csv:
        paths = [Path(args.csv)]
    else:
        p.print_help()
        return

    results = []
    for path in paths:
        if not path.exists():
            print(f"Missing: {path}")
            continue
        print(f"Running sim for {path.name}...")
        result = run_day(path, seed=args.seed)
        print_report(result)
        results.append(result)

    if args.output and results:
        Path(args.output).write_text(json.dumps(results, indent=2))
        print(f"\nResults written to {args.output}")


if __name__ == "__main__":
    main()
