"""Thin adapter: run the full sim via the src.atl_sim package."""

from src.atl_sim import AirportSimulation, load_config

__all__ = ["AirportSimulation", "load_config"]
