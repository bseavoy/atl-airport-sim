# ATL Airport Discrete-Event Simulation

A focused discrete-event simulation of Hartsfield-Jackson Atlanta International Airport (ATL) ground operations, including arrivals, departures, gate assignments, taxi, and runway sequencing.

## Overview

This simulator models ATL's ground operations as a discrete-event system. It captures:
- **Arrivals:** Scheduled arrival time, wheels-down, gate assignment, parking duration
- **Departures:** Gate pushback, taxi-out time, runway queue, departure time
- **Gate Management:** Capacity constraints, hold queues, reassignment
- **Taxi Dynamics:** Congestion-based delays with time-of-day scale factors
- **Runway Sequencing:** Separation rules (RECAT), departure rate limits

The model is calibrated against actual BTS (Bureau of Transportation Statistics) on-time performance data and validated against real ATL flight schedules.

## Project Structure

```
atl-airport-sim/
├── src/atl_sim/
│   ├── __init__.py            # Main AirportSimulation class
│   ├── config.py              # Load/parse airport configs
│   ├── flight.py              # Flight entity with state machine
│   ├── entities.py            # Gate, Runway, DepartureMeter
│   ├── metrics.py             # A0/D0 calculations
│   └── events/                # Event handlers (arrival, pushback, etc.)
├── data/
│   ├── airport/               # ATL configuration
│   │   └── atl_config.json    # Capacity, gates, runways, taxi params
│   └── validation/            # Real flight schedules for testing
│       └── sample_june1_2025.csv
├── docs/                      # Architecture, design notes
├── scripts/                   # Calibration and analysis tools
├── tests/                     # Unit and integration tests
└── main.py                    # CLI entry point
```

## Key Metrics

**A0 (Arrival On-Time):** % of flights arriving within 0, ±5, ±15 minutes of scheduled arrival

**D0 (Departure On-Time):** % of flights pushing back within 0, ±5, ±15 minutes of scheduled departure

**Taxi-Out Distribution:** Median and inter-quartile range of actual vs simulated

Target validation: ±2pp of BTS for all metrics

## Installation

```bash
pip install -r requirements.txt
```

Dependencies:
- SimPy ≥4.0
- NumPy ≥1.26
- Pandas ≥2.0
- Requests ≥2.31

## Usage

### Command Line

```bash
python main.py \
    --schedule data/validation/sample_june1_2025.csv \
    --config data/airport/atl_config.json \
    --until 1440 \
    --seed 42 \
    --output results/atl_output.json \
    --validate
```

**Arguments:**
- `--schedule <path>` — Flight schedule CSV (origin, destination, scheduled_arr, scheduled_dep)
- `--config <path>` — Airport config JSON (default: data/airport/atl_config.json)
- `--until <minutes>` — Simulate until this many minutes from midnight (default: 1440 = full day)
- `--seed <int>` — Random seed (default: 42)
- `--output <path>` — Write summary JSON to this file
- `--validate` — Print validation table vs BTS benchmarks

### Python API

```python
from src.atl_sim import AirportSimulation, load_config

config = load_config("data/airport/atl_config.json")
sim = AirportSimulation(config=config, seed=42)
sim.load_schedule("data/validation/sample_june1_2025.csv")

metrics = sim.run(until_min=1440)
summary = metrics.summary()

print(f"A0 (0 min): {summary['arrival_on_time_0']:.1%}")
print(f"D0 (0 min): {summary['departure_on_time_0']:.1%}")
print(f"Taxi median: {summary['taxi_out_median']:.0f} min")
```

### Output Format

```json
{
  "simulation": {
    "airport": "ATL",
    "duration_minutes": 1440,
    "flights_scheduled": 285,
    "flights_completed": 283
  },
  "arrivals": {
    "on_time_0": 0.65,
    "on_time_5": 0.78,
    "on_time_15": 0.89,
    "median_delay_minutes": 3.2
  },
  "departures": {
    "on_time_0": 0.58,
    "on_time_5": 0.71,
    "on_time_15": 0.84,
    "median_delay_minutes": 5.1
  },
  "taxi_out": {
    "median_minutes": 22.5,
    "p10_minutes": 15.0,
    "p90_minutes": 32.1
  }
}
```

## Revision History

### v0.1.0 (Current)

- **Add departure schedule padding to improve D0 on clean operation days** — Departue schedule distribution now models realistic gate/ramp activity before pushback
- **Fix departure meter wait tracking; recalibrate taxi-out to unimpeded baseline** — Separated FAA meter wait from taxi wait; adjusted taxi scale factors for time-of-day
- **Add hourly taxi-out scale factors to reduce off-peak over-prediction** — Taxi times now scale by hour (e.g., 0.8x at 3am, 1.2x at 8am) for realistic early-morning performance
- **Fix dep runway wait inflation and reduce taxi-out congestion alpha** — Revised congestion queue-length exponent to reduce runaway delays in saturated scenarios
- **Implement RECAT separation, smart gate hold, congestion taxi model** — Added aircraft-weight-based separation rules, queue-driven gate holds, and congestion-dependent taxi scaling
- **Add DepartureMeter to enforce FAA departure rate cap** — Implemented per-runway and airport-wide departure rate limits (typically 80/hr at ATL)
- **Add per-flight arrival schedule padding distribution; calibrate A0 to 80%** — Arrivals now have stochastic schedule padding reflecting real arrival-to-gate variance
- **Calibrate departure_max_taxi_queue to 37 via blended metric sweep** — Tuned queue length threshold where congestion effects activate
- **Add A0/D0 on-time performance metrics; gate-hold D0 mechanism** — Core on-time metrics and gate-hold delay modeling
- **Add GDP/GS ground program configuration system; recalibrate Aug-16 convective event** — Support for FAA Ground Delay Programs with reduced capacity windows

## Structural Notes

### Core Entities

**Flight:** State machine (scheduled → arrived/departed → gate assigned → pushback → airborne)
- Arrival time: scheduled_arr + padding distribution
- Departure time: max(scheduled_dep, current_time_at_gate) + taxi_out_time

**Gate:** Fixed capacity (185 gates at ATL), FIFO assignment with holdover control

**Runway:** Separation enforcement, departure meter rate limit

**DepartureMeter:** FAA-style rate limit enforcement (e.g., 80 dep/hr)

### Key Parameters (ATL)

```json
{
  "code": "ATL",
  "gates": 185,
  "runways": {
    "arrival": ["9L", "9R", "8L", "8R"],
    "departure": ["9L", "9R", "8L", "8R"],
    "crossing": ["10L", "10R"]
  },
  "capacity": {
    "departure_rate_per_hour": 80,
    "arrival_rate_per_hour": 75
  },
  "taxi_out": {
    "unimpeded_mean": 10,
    "unimpeded_std": 2.5,
    "congestion_alpha": 0.8,
    "hourly_scale_factors": [0.8, 0.75, 0.7, 0.7, 0.75, 0.9, 1.1, 1.2, 1.15, ...]
  },
  "arrival_padding": {
    "mean_minutes": 2,
    "std_minutes": 3
  }
}
```

### Calibration Approach

1. Extract real flight schedule (CSV with scheduled arrival/departure times)
2. Run 30-day simulation with real schedule
3. Compare simulated A0/D0 vs BTS benchmarks
4. Adjust taxi_out scale factors, padding distributions, meter rate
5. Validate against holdout week

Typical tuning cycle: 5-10 iterations to achieve ±2pp match

## Testing

```bash
pytest tests/ -v
pytest tests/test_atl_sim.py::test_a0_calibration -v
```

Key tests:
- `test_gate_capacity` — Sufficient gates for all arrivals
- `test_taxi_distribution` — Taxi times match unimpeded baseline ±2σ
- `test_departure_meter` — Rate limit enforced (no burst >80/hr)
- `test_schedule_padding` — Arrival padding matches realistic distributions

## Validation Against BTS

Run with `--validate` flag to print a comparison table:

```
ATL Validation (BTS vs Simulated)
┌──────────────────────┬──────────┬──────────┬──────────┐
│ Metric               │ BTS 2025 │ Simulated│ Delta    │
├──────────────────────┼──────────┼──────────┼──────────┤
│ A0 (0 min)           │ 63.5%    │ 65.1%    │ +1.6pp   │
│ A0 (±5 min)          │ 75.2%    │ 77.8%    │ +2.6pp   │
│ A0 (±15 min)         │ 86.9%    │ 88.2%    │ +1.3pp   │
│ D0 (0 min)           │ 55.8%    │ 57.9%    │ +2.1pp   │
│ D0 (±5 min)          │ 68.4%    │ 70.1%    │ +1.7pp   │
│ D0 (±15 min)         │ 81.3%    │ 82.5%    │ +1.2pp   │
│ Taxi-Out Median      │ 22 min   │ 22.5 min │ +0.5 min │
└──────────────────────┴──────────┴──────────┴──────────┘
```

## Known Limitations

1. **Gate Conflicts:** No multi-airline terminal preferences; simple FIFO
2. **Weather:** No weather model; all VFR throughout day
3. **Mechanical Delays:** Only schedule-based delays; no random breakdowns
4. **Passenger Connections:** No modeling of misconnected passengers or crew constraints

## Future Work

- [ ] Weather integration (convective events, runway closures)
- [ ] Crew constraints and connection modeling
- [ ] Per-airline gate preferences (terminal-level constraints)
- [ ] Pushback delay modeling (catering, fueling, boarding delays)
- [ ] Real-time taxi routing (taxi time prediction per runway exit)

## References

- **BTS Form 41 Data:** Bureau of Transportation Statistics, on-time performance
- **ICAO Annex 8:** Aircraft Classification (RECAT rules)
- **FAA Order 7110.66:** Tower Operations and Separation Standards

## License

Research Use Only

## Contact

Ben Seavoy — bseavoy@gmail.com
