"""
Run the sim against a real BTS day file and compare simulated vs actual taxi times.

Usage:
    python scripts/validate_real_day.py data/real_days/2024-07-09_atl.csv
    python scripts/validate_real_day.py --all          # runs all days in manifest
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.atl_sim import AirportSimulation, load_config
from src.atl_sim.config import load_ground_programs

MANIFEST = Path("data/real_days/manifest.json")
CONFIG_PATH = Path("data/atl_config.json")

PEAK_HOURS = {7, 8, 9, 15, 16, 17, 18, 19, 20, 21}


def _stats(vals):
    if not vals:
        return {"mean": None, "std": None, "p50": None, "p95": None}
    a = np.array([v for v in vals if v is not None])
    if len(a) == 0:
        return {"mean": None, "std": None, "p50": None, "p95": None}
    return {
        "mean": round(float(np.mean(a)), 2),
        "std": round(float(np.std(a)), 2),
        "p50": round(float(np.percentile(a, 50)), 2),
        "p95": round(float(np.percentile(a, 95)), 2),
    }


def run_day(csv_path: Path, seed: int = 42, gdp_path: Optional[Path] = None) -> dict:
    config = load_config(str(CONFIG_PATH))
    programs = load_ground_programs(str(gdp_path)) if gdp_path else []
    sim = AirportSimulation(config=config, seed=seed, ground_programs=programs)
    sim.load_schedule(str(csv_path))
    metrics = sim.run(until_min=1500.0)

    real = pd.read_csv(csv_path)
    real["hour"] = real["scheduled_min"].apply(
        lambda x: int(float(x)) // 60 % 24 if pd.notna(x) else None
    )
    real_arr = real[(real["operation"] == "ARR") & real["actual_taxi_min"].notna()]
    real_dep = real[(real["operation"] == "DEP") & real["actual_taxi_min"].notna()]

    sim_arr = [r for r in metrics.records if r.operation == "ARR"]
    sim_dep = [r for r in metrics.records if r.operation == "DEP"]

    # A0 / D0 rates (on-time gate arrival / gate departure)
    arr_ot = real[(real["operation"] == "ARR") & real["actual_min"].notna() & real["scheduled_min"].notna()]
    dep_ot = real[(real["operation"] == "DEP") & real["actual_min"].notna() & real["scheduled_min"].notna()]
    real_a0 = float((arr_ot["actual_min"] <= arr_ot["scheduled_min"]).mean()) if len(arr_ot) else 0.0
    real_d0 = float((dep_ot["actual_min"] <= dep_ot["scheduled_min"]).mean()) if len(dep_ot) else 0.0
    sim_a0 = sum(1 for r in sim_arr if r.gate_in_min is not None and r.gate_in_min <= r.scheduled_min) / len(sim_arr) if sim_arr else 0.0
    sim_d0 = sum(1 for r in sim_dep if r.pushback_min is not None and r.pushback_min <= r.scheduled_min) / len(sim_dep) if sim_dep else 0.0

    # Per-hour actuals
    actual_by_hour: dict = {}
    for h in range(24):
        a_arr = real_arr[real_arr["hour"] == h]["actual_taxi_min"].tolist()
        a_dep = real_dep[real_dep["hour"] == h]["actual_taxi_min"].tolist()
        if a_arr or a_dep:
            actual_by_hour[h] = {
                "arr_taxi": _stats(a_arr),
                "dep_taxi": _stats(a_dep),
            }

    return {
        "date": csv_path.stem.replace("_atl", ""),
        "flights_in_file": len(real),
        "flights_simulated": len(metrics.records),
        "taxi_in": {
            "actual": _stats(real_arr["actual_taxi_min"].tolist()),
            "simulated": _stats([r.taxi_min for r in sim_arr if r.taxi_min]),
        },
        "taxi_out": {
            "actual": _stats(real_dep["actual_taxi_min"].tolist()),
            "simulated": _stats([r.taxi_min for r in sim_dep if r.taxi_min]),
        },
        "runway_wait": {
            "arr": _stats([r.runway_wait_min for r in sim_arr]),
            "dep": _stats([r.runway_wait_min for r in sim_dep]),
        },
        "a0": {"actual": round(real_a0, 4), "simulated": round(sim_a0, 4)},
        "d0": {"actual": round(real_d0, 4), "simulated": round(sim_d0, 4)},
        "by_hour_actual": actual_by_hour,
        "by_hour_sim": metrics.by_hour(),
    }


def print_report(result: dict) -> None:
    date = result["date"]
    W = 74

    print(f"\n{'='*W}")
    print(f"  {date}  |  {result['flights_simulated']}/{result['flights_in_file']} flights simulated")
    print(f"{'='*W}")

    # ── Overall stats ────────────────────────────────────────────────────
    print(f"\n{'Metric':<28} {'Actual':>10} {'Simulated':>10} {'Delta':>8}")
    print(f"{'-'*W}")

    def _row(label, av, sv):
        if av is None or sv is None:
            print(f"{label:<28} {'N/A':>10} {'N/A':>10} {'N/A':>8}")
            return
        delta = sv - av
        flag = " !" if abs(delta) > 3 else ""
        print(f"{label:<28} {av:>10.2f} {sv:>10.2f} {delta:>+8.2f}{flag}")

    ti_a = result["taxi_in"]["actual"]
    ti_s = result["taxi_in"]["simulated"]
    to_a = result["taxi_out"]["actual"]
    to_s = result["taxi_out"]["simulated"]
    rw = result["runway_wait"]

    _row("taxi-in mean (min)", ti_a["mean"], ti_s["mean"])
    _row("taxi-in std (min)",  ti_a["std"],  ti_s["std"])
    _row("taxi-in p50 (min)",  ti_a["p50"],  ti_s["p50"])
    _row("taxi-in p95 (min)",  ti_a["p95"],  ti_s["p95"])
    print(f"{'-'*W}")
    _row("taxi-out mean (min)", to_a["mean"], to_s["mean"])
    _row("taxi-out std (min)",  to_a["std"],  to_s["std"])
    _row("taxi-out p50 (min)",  to_a["p50"],  to_s["p50"])
    _row("taxi-out p95 (min)",  to_a["p95"],  to_s["p95"])
    print(f"{'-'*W}")
    if rw["arr"]["mean"] is not None:
        print(f"{'arr runway wait mean':<28} {'(sim only)':>10} {rw['arr']['mean']:>10.2f}")
        print(f"{'arr runway wait p95':<28} {'(sim only)':>10} {rw['arr']['p95']:>10.2f}")
        print(f"{'dep runway wait mean':<28} {'(sim only)':>10} {rw['dep']['mean']:>10.2f}")
        print(f"{'dep runway wait p95':<28} {'(sim only)':>10} {rw['dep']['p95']:>10.2f}")
    print(f"{'-'*W}")
    a0 = result.get("a0", {})
    d0 = result.get("d0", {})
    if a0:
        a0_act, a0_sim = a0["actual"], a0["simulated"]
        d0_act, d0_sim = d0["actual"], d0["simulated"]
        print(f"{'A0 rate (gate arr on time)':<28} {a0_act:>10.1%} {a0_sim:>10.1%} {a0_sim - a0_act:>+8.1%}")
        print(f"{'D0 rate (gate dep on time)':<28} {d0_act:>10.1%} {d0_sim:>10.1%} {d0_sim - d0_act:>+8.1%}")

    # ── Time-of-day breakdown ────────────────────────────────────────────
    print(f"\n{'--- Time-of-Day Breakdown':^{W}}")
    print(
        f"  {'Hr':>3}  {'Act TI':>7} {'Sim TI':>7} {'ΔTI':>6}  "
        f"{'Act TO':>7} {'Sim TO':>7} {'ΔTO':>6}  "
        f"{'RwyWt':>6}  {'Peak':>4}"
    )
    print(f"  {'-'*68}")

    bh_act = result["by_hour_actual"]
    bh_sim = result["by_hour_sim"]
    all_hours = sorted(set(list(bh_act.keys()) + [int(h) for h in bh_sim.keys()]))

    for h in all_hours:
        if h < 5 or h > 22:
            continue
        act = bh_act.get(h, {})
        sim_h = bh_sim.get(h, {})

        act_ti = act.get("arr_taxi", {}) or {}
        act_to = act.get("dep_taxi", {}) or {}
        sim_ti = sim_h.get("arr_taxi") or {}
        sim_to = sim_h.get("dep_taxi") or {}
        sim_rw_dep = sim_h.get("dep_rwy_wait") or {}

        def _v(d, k):
            v = d.get(k)
            return f"{v:7.1f}" if v is not None else "    N/A"

        def _delta(act_d, sim_d, k):
            av, sv = act_d.get(k), sim_d.get(k)
            if av is None or sv is None:
                return "    N/A"
            d = sv - av
            return f"{d:+6.1f}"

        peak = " ◀" if h in PEAK_HOURS else ""
        rwy_wait_str = _v(sim_rw_dep, "mean")

        print(
            f"  {h:02d}:xx  "
            f"{_v(act_ti,'mean')} {_v(sim_ti,'mean')} {_delta(act_ti,sim_ti,'mean')}  "
            f"{_v(act_to,'mean')} {_v(sim_to,'mean')} {_delta(act_to,sim_to,'mean')}  "
            f"{rwy_wait_str}  {peak}"
        )

    print(f"{'='*W}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("csv", nargs="?", help="Path to a real-day CSV file")
    p.add_argument("--all", action="store_true", help="Run all days in manifest")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--gdp", metavar="FILE",
                   help="Ground programs JSON (e.g. data/ground_programs/2024-08-16_atl.json)")
    p.add_argument("--output", help="Write JSON results to this path")
    args = p.parse_args()

    gdp_path = Path(args.gdp) if args.gdp else None

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

    if gdp_path:
        print(f"Ground programs: {gdp_path}")

    results = []
    for path in paths:
        if not path.exists():
            print(f"Missing: {path}")
            continue
        print(f"Running sim for {path.name}...")
        result = run_day(path, seed=args.seed, gdp_path=gdp_path)
        print_report(result)
        results.append(result)

    if args.output and results:
        Path(args.output).write_text(json.dumps(results, indent=2, default=str))
        print(f"\nResults written to {args.output}")


if __name__ == "__main__":
    main()
