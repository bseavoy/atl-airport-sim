"""
Add concourse assignments to real-day BTS files (which have no gate column).
Uses known ATL terminal assignments by airline and international destination.

Usage:
    python scripts/enrich_concourses.py            # enriches all real_days/*.csv
    python scripts/enrich_concourses.py <file.csv> # single file
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pandas as pd

# ATL concourse assignments by IATA carrier code (2024 ops).
# Source: Hartsfield-Jackson terminal maps + OAG schedule data.
CONCOURSE_BY_AIRLINE: dict[str, list[str]] = {
    # Delta mainline + Delta Connection (all funneled through main complex)
    "DL": ["A", "B", "C", "D"],
    "9E": ["A", "B"],        # Endeavor Air (Delta Connection)
    "OO": ["A", "B"],        # SkyWest (Delta Connection)
    "EV": ["A", "B"],        # ExpressJet (Delta Connection)
    "YX": ["A", "B"],        # Midwest/Republic (Delta Connection)
    "G7": ["A", "B"],        # GoJet (Delta Connection)
    "MQ": ["A", "B"],        # Envoy (American Eagle)
    # Southwest uses its own gates in C/D area
    "WN": ["C", "D"],
    # Legacy carriers
    "AA": ["D"],
    "UA": ["B", "C"],
    # ULCCs & LCCs
    "NK": ["A", "C"],
    "B6": ["A", "B"],
    "F9": ["A", "D"],
    "AS": ["B"],
    "G4": ["C"],             # Allegiant
    "SY": ["C"],             # Sun Country
    "VX": ["B"],             # Virgin America (legacy)
    # Cargo/charter — assign to T or A
    "FX": ["T"],
    "UPS": ["T"],
}

# Airports outside the US / Canada / Mexico that route through Concourse F (intl).
INTL_AIRPORTS = {
    "CDG", "LHR", "FRA", "AMS", "NRT", "HND", "ICN", "PEK", "PVG", "SIN",
    "BKK", "DXB", "DOH", "GRU", "GIG", "EZE", "BOG", "LIM", "SCL", "MEX",
    "CUN", "MBJ", "SJO", "GUA", "HAV", "BCN", "MAD", "FCO", "MUC", "ZRH",
    "BRU", "VIE", "DUB", "CPH", "ARN", "OSL", "HEL", "WAW", "PRG", "BUD",
    "IST", "CAI", "JNB", "NBO", "ADD", "SYD", "MEL", "AKL", "YYZ", "YUL",
    "YVR", "YYC", "CUN", "PUJ", "SDQ", "AUA", "BDA",
}

DEFAULT_CONCOURSES = ["A", "B", "C", "D"]


def assign_concourse(airline: str, origin: str, destination: str, rng: random.Random) -> str:
    other = origin if destination == "ATL" else destination
    if other in INTL_AIRPORTS:
        return "F"
    options = CONCOURSE_BY_AIRLINE.get(airline, DEFAULT_CONCOURSES)
    return rng.choice(options)


def enrich(path: Path, seed: int = 42) -> None:
    rng = random.Random(seed)
    df = pd.read_csv(path)

    if "concourse" in df.columns:
        non_default = (df["concourse"] != "A").sum()
        if non_default > 0:
            print(f"  {path.name}: already enriched, skipping")
            return

    df["concourse"] = df.apply(
        lambda r: assign_concourse(
            str(r.get("airline", "")),
            str(r.get("origin", "")),
            str(r.get("destination", "")),
            rng,
        ),
        axis=1,
    )

    dist = df["concourse"].value_counts().to_dict()
    df.to_csv(path, index=False)
    print(f"  {path.name}: enriched {len(df)} flights — {dist}")


def main():
    base = Path("data/real_days")
    if len(sys.argv) > 1:
        paths = [Path(a) for a in sys.argv[1:]]
    else:
        paths = sorted(base.glob("*_atl.csv"))

    print(f"Enriching {len(paths)} file(s)...")
    for p in paths:
        enrich(p)
    print("Done.")


if __name__ == "__main__":
    main()
