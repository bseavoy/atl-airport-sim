from dataclasses import dataclass, field
from typing import List, Optional

import simpy


class Gate(simpy.Resource):
    def __init__(self, env, gate_id, terminal, compatible_aircraft=None):
        super().__init__(env, capacity=1)
        self.gate_id = gate_id
        self.terminal = terminal
        self.compatible_aircraft = compatible_aircraft or []


class Runway(simpy.Resource):
    def __init__(self, env, runway_id, length_ft):
        super().__init__(env, capacity=1)
        self.runway_id = runway_id
        self.length_ft = length_ft
        self.use_count = 0


@dataclass
class Aircraft:
    flight_id: str
    airline: str
    aircraft_type: str
    origin_dest: str
    scheduled_time: float  # minutes from midnight
    operation: str  # ARR or DEP
    gate: Optional[str] = None
    terminal: Optional[str] = None
