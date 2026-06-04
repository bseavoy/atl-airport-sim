import pandas as pd

from .resources import Aircraft


def _parse_hhmm(value) -> float:
    s = str(value).strip()
    h, m = s.split(":")
    return int(h) * 60 + int(m)


def load_schedule(csv_path: str):
    df = pd.read_csv(csv_path, dtype=str)
    flights = []
    for _, row in df.iterrows():
        flights.append(
            Aircraft(
                flight_id=row["flight_id"],
                airline=row["airline"],
                aircraft_type=row["aircraft_type"],
                origin_dest=row["origin_dest"],
                scheduled_time=_parse_hhmm(row["scheduled_time"]),
                operation=row["operation"].strip().upper(),
                gate=row.get("gate"),
                terminal=row.get("terminal"),
            )
        )
    flights.sort(key=lambda f: f.scheduled_time)
    return flights
