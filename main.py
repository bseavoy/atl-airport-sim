"""CLI entry point for the ATL airport simulation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.atl_sim import AirportSimulation, load_config


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

    if args.output:
        Path(args.output).write_text(json.dumps(summary, indent=2))
        print(f"\nSummary written to {args.output}")


if __name__ == "__main__":
    main()
