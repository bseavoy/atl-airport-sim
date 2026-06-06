"""Load and expose ATL airport configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RunwayConfig:
    name: str
    length_ft: int
    width_ft: int
    primary_use: str  # "arrival", "departure", "mixed"
    wake_turbulence_group: str


@dataclass
class ConcourseConfig:
    name: str
    gate_count: int
    gate_prefix: str
    gate_range: tuple
    description: str
    taxi_in_mean_min: float
    taxi_in_std_min: float
    taxi_out_mean_min: float
    taxi_out_std_min: float
    compatible_aircraft: List[str]


@dataclass
class SeparationMinima:
    heavy_behind_heavy_sec: int = 90
    heavy_behind_large_sec: int = 60
    large_behind_heavy_sec: int = 120
    large_behind_large_sec: int = 60
    small_behind_heavy_sec: int = 180
    small_behind_large_sec: int = 90
    default_separation_sec: int = 60


@dataclass
class GroundProgram:
    """
    Configures a ground delay program (GDP) or ground stop (GS) for a
    specific time window.  Effects are applied dynamically during simulation
    based on env.now at the point each aircraft reaches the runway threshold.

    Departure clearance hold: aircraft that complete taxi-out and reach the
    runway threshold during this window receive an additional ATC hold before
    getting take-off clearance.  This represents "taxi and hold" / EDCT
    compliance delays that inflate taxi-out times during GDP events.

    Arrival rate cap: limits how quickly the arrival runway resource accepts
    new aircraft, representing TRACON metering and reduced acceptance rate.
    """
    type: str                         # "GDP" or "GS"
    description: str
    start_min: float                  # Minutes from midnight (local)
    end_min: float

    # Clearance hold added to each departure AT THE RUNWAY THRESHOLD
    dep_clearance_hold_mean_min: float = 0.0
    dep_clearance_hold_std_min: float = 0.0
    dep_clearance_hold_max_min: float = 120.0

    # Arrival acceptance rate cap (per hour); 0 = no cap
    arr_rate_per_hour: float = 0.0


def load_ground_programs(path: str) -> List[GroundProgram]:
    """Load a list of GroundProgram definitions from a JSON file."""
    with open(path, "r") as fh:
        raw = json.load(fh)
    programs = []
    for p in raw.get("programs", []):
        programs.append(GroundProgram(
            type=p.get("type", "GDP"),
            description=p.get("description", ""),
            start_min=float(p["start_min"]),
            end_min=float(p["end_min"]),
            dep_clearance_hold_mean_min=float(p.get("dep_clearance_hold_mean_min", 0.0)),
            dep_clearance_hold_std_min=float(p.get("dep_clearance_hold_std_min", 0.0)),
            dep_clearance_hold_max_min=float(p.get("dep_clearance_hold_max_min", 120.0)),
            arr_rate_per_hour=float(p.get("arr_rate_per_hour", 0.0)),
        ))
    return programs


@dataclass
class AirportConfig:
    airport: str
    name: str
    icao: str
    iata: str
    runways: Dict[str, RunwayConfig]
    concourses: Dict[str, ConcourseConfig]
    separation: SeparationMinima
    nominal_arrival_rate_per_hour: int
    nominal_departure_rate_per_hour: int
    gdp_arrival_rates: Dict[str, int]
    pushback_clearance_mean_min: float
    pushback_clearance_std_min: float
    gate_holdout_mean_min: float
    gate_holdout_std_min: float
    turnaround_narrow_min: int
    turnaround_wide_min: int
    use_lognormal: bool = True
    taxi_in_lognorm_sigma: float = 0.434
    taxi_out_lognorm_sigma: float = 0.356
    departure_max_taxi_queue: int = 25
    arr_schedule_padding_mean_min: float = 0.0
    arr_schedule_padding_std_min: float = 0.0
    # Per-airline schedule padding overrides: {iata_code: (mean_min, std_min)}
    airline_padding_overrides: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    # Congestion-adjusted taxi-out: mean += alpha * queue_depth_at_pushback
    taxi_out_congestion_alpha: float = 0.3
    # Smart gate hold: hold at gate while dep queue >= threshold (Simaiakis 2012)
    congestion_departure_queue_threshold: int = 15
    gate_hold_poll_min: float = 1.0
    # Per-hour multiplier on concourse taxi_out_mean_min before congestion term.
    # Derived from FAA ASPM unimpeded taxi-out ratio (off-peak vs peak baseline).
    # Missing hours default to 1.0 (no scaling).
    hourly_taxi_out_scale: Dict[int, float] = field(default_factory=dict)


def load_config(config_path: Optional[str] = None) -> AirportConfig:
    """Load airport configuration from JSON file.

    Defaults to data/airport/atl_config.json relative to the package root.
    """
    if config_path is None:
        pkg_root = Path(__file__).parent.parent.parent
        config_path = pkg_root / "data" / "airport" / "atl_config.json"

    with open(config_path, "r") as fh:
        raw = json.load(fh)

    runways = {
        k: RunwayConfig(
            name=k,
            length_ft=v["length_ft"],
            width_ft=v.get("width_ft", 150),
            primary_use=v.get("primary_use", "mixed"),
            wake_turbulence_group=v.get("wake_turbulence_group", "mixed"),
        )
        for k, v in raw["runways"].items()
    }

    concourses = {
        k: ConcourseConfig(
            name=k,
            gate_count=v["gate_count"],
            gate_prefix=v["gate_prefix"],
            gate_range=tuple(v["gate_range"]),
            description=v.get("description", ""),
            taxi_in_mean_min=v["taxi_in_mean_min"],
            taxi_in_std_min=v["taxi_in_std_min"],
            taxi_out_mean_min=v["taxi_out_mean_min"],
            taxi_out_std_min=v["taxi_out_std_min"],
            compatible_aircraft=v.get("compatible_aircraft", ["narrow", "wide"]),
        )
        for k, v in raw["concourses"].items()
    }

    sep_raw = raw.get("separation_minima", {})
    separation = SeparationMinima(
        heavy_behind_heavy_sec=sep_raw.get("heavy_behind_heavy_sec", 90),
        heavy_behind_large_sec=sep_raw.get("heavy_behind_large_sec", 60),
        large_behind_heavy_sec=sep_raw.get("large_behind_heavy_sec", 120),
        large_behind_large_sec=sep_raw.get("large_behind_large_sec", 60),
        small_behind_heavy_sec=sep_raw.get("small_behind_heavy_sec", 180),
        small_behind_large_sec=sep_raw.get("small_behind_large_sec", 90),
        default_separation_sec=sep_raw.get("default_separation_sec", 60),
    )

    cap = raw.get("capacity", {})
    gdp_rates = cap.get("gdp_arrival_rates", {"light": 60, "moderate": 45, "severe": 25})

    taxi_dist = raw.get("taxi_distribution", {})

    return AirportConfig(
        airport=raw["airport"],
        name=raw["name"],
        icao=raw.get("icao", "KATL"),
        iata=raw.get("iata", "ATL"),
        runways=runways,
        concourses=concourses,
        separation=separation,
        nominal_arrival_rate_per_hour=cap.get("nominal_arrival_rate_per_hour", 80),
        nominal_departure_rate_per_hour=cap.get("nominal_departure_rate_per_hour", 80),
        gdp_arrival_rates=gdp_rates,
        pushback_clearance_mean_min=raw.get("pushback_clearance_mean_min", 5.0),
        pushback_clearance_std_min=raw.get("pushback_clearance_std_min", 2.0),
        gate_holdout_mean_min=raw.get("gate_holdout_mean_min", 8.0),
        gate_holdout_std_min=raw.get("gate_holdout_std_min", 6.0),
        turnaround_narrow_min=raw.get("turnaround_narrow_min", 45),
        turnaround_wide_min=raw.get("turnaround_wide_min", 60),
        use_lognormal=bool(taxi_dist.get("use_lognormal", True)),
        taxi_in_lognorm_sigma=float(taxi_dist.get("taxi_in_lognorm_sigma", 0.434)),
        taxi_out_lognorm_sigma=float(taxi_dist.get("taxi_out_lognorm_sigma", 0.356)),
        departure_max_taxi_queue=int(raw.get("departure_max_taxi_queue", 25)),
        arr_schedule_padding_mean_min=float(raw.get("arr_schedule_padding_mean_min", 0.0)),
        arr_schedule_padding_std_min=float(raw.get("arr_schedule_padding_std_min", 0.0)),
        airline_padding_overrides={
            k: (float(v[0]), float(v[1]))
            for k, v in raw.get("airline_padding_overrides", {}).items()
        },
        taxi_out_congestion_alpha=float(raw.get("taxi_out_congestion_alpha", 0.3)),
        congestion_departure_queue_threshold=int(raw.get("congestion_departure_queue_threshold", 15)),
        gate_hold_poll_min=float(raw.get("gate_hold_poll_min", 1.0)),
        hourly_taxi_out_scale={
            int(k): float(v)
            for k, v in raw.get("hourly_taxi_out_scale", {}).items()
        },
    )
