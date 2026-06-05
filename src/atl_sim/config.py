"""Load and expose ATL airport configuration."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Any


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
    # Keys are hour-of-day ints (0-23); missing hours default to 1.0
    taxi_out_hourly_multipliers: Dict[int, float] = field(default_factory=dict)
    # Max aircraft allowed in departure taxi system (taxi + runway queue).
    # Arrivals over this limit hold at the gate until a slot opens.
    departure_max_taxi_queue: int = 25


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
    hourly_raw = taxi_dist.get("taxi_out_hourly_multipliers", {})
    hourly_multipliers = {int(k): float(v) for k, v in hourly_raw.items()}

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
        taxi_out_hourly_multipliers=hourly_multipliers,
        departure_max_taxi_queue=int(raw.get("departure_max_taxi_queue", 25)),
    )
