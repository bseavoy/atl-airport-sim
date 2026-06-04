"""Load a flight schedule CSV into Flight objects."""

from __future__ import annotations

import pandas as pd

from .resources import Flight

WEIGHT_CLASS_MAP = {
    "narrow": "Large",
    "wide": "Heavy",
}


def _parse_hhmm(value: str) -> float:
    s = str(value).strip()
    if ":" in s:
        h, m = s.split(":")
        return int(h) * 60 + int(m)
    return float(s)


def load_schedule(csv_path: str) -> list[Flight]:
    df = pd.read_csv(csv_path, dtype=str)
    flights: list[Flight] = []
    for _, row in df.iterrows():
        aircraft_type = row.get("aircraft_type", "narrow").strip().lower()
        weight_class = row.get("aircraft_weight_class", "").strip()
        if not weight_class:
            weight_class = WEIGHT_CLASS_MAP.get(aircraft_type, "Large")
        flights.append(
            Flight(
                flight_id=row["flight_id"],
                airline=row["airline"],
                flight_number=row["flight_number"],
                aircraft_type=aircraft_type,
                tail_number=row.get("tail_number", ""),
                operation=row["operation"].strip().upper(),
                scheduled_min=_parse_hhmm(row["scheduled_time"]),
                origin=row.get("origin", ""),
                destination=row.get("destination", ""),
                gate_assigned=row.get("gate_assigned", ""),
                concourse=row.get("concourse", "A"),
                weight_class=weight_class,
            )
        )
    flights.sort(key=lambda f: f.scheduled_min)
    return flights
