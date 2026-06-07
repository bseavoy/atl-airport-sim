# Future Simulation Improvements

## Approach 1 — GDP/Ground-Stop Injection from FAA Public Data

**Problem:** On disrupted days (Jul 16, Aug 1, Aug 16, Dec 2, Feb 17, Mar 17, Apr 1), actual D0 drops to 39–56% while the sim produces 71–77%. Actual taxi-out p95 on Aug 16 reaches 52 min while the sim produces ~31 min. GDP/weather events cause queue saturation and clearance holds the baseline model doesn't capture.

**The mechanism already exists:** `GroundProgram` dataclass and `--gdp` flag on `validate_real_day.py` are fully wired. The only missing piece is a data feed.

**Data source:** FAA Aviation System Performance Metrics (ASPM) at aspm.faa.gov publishes historical GDP/GS event logs. For each event you get: airport, type (GDP/GS), start time UTC, end time UTC, and arrival acceptance rate (AAR).

**Implementation steps:**
1. For a given validation date, query ASPM for KATL events and convert to local minutes-from-midnight.
2. Map the AAR to `arr_rate_per_hour`.
3. Set `dep_clearance_hold_mean_min` based on GDP severity: light (~10 min), moderate (~20 min), severe/GS (~35 min). ATL's parallel runways make it more resilient than JFK so these values are lower.
4. Write a `scripts/fetch_gdp.py` that calls ASPM, outputs a GDP JSON file, and passes it to `validate_real_day.py` automatically.

**Expected impact:** On Aug 16 the 20-21:xx taxi-out deltas of -39 and -8 min should tighten to ±10 min.

---

## Approach 3 — Weather-Conditioned Taxi-Out Sigma

**Problem:** On irregular days (Aug 16 taxi-out std = 16 min vs sim 6.7 min), the fixed lognormal sigma doesn't capture fat-tailed weather distributions. The current `taxi_out_lognorm_sigma = 0.356` is calibrated to VMC conditions only.

**Data sources:**
- METAR archives at aviationweather.gov (free, per-airport, hourly)
- FAA ASPM VMC/IMC fraction by hour

**Implementation:**
1. Add `weather_state: str = "VMC"` to `AirportSimulation.__init__` and `validate_real_day.py --weather`.
2. Add `weather_taxi_out_sigma_overrides: Dict[str, float]` to `AirportConfig`:
   ```json
   "weather_taxi_out_sigma_overrides": {
     "VMC": 0.356,
     "IMC": 0.480,
     "LIFR": 0.580
   }
   ```
3. In `_taxi_out()`, replace `cfg.taxi_out_lognorm_sigma` with a lookup keyed on current weather state.
4. Optionally make it time-varying: accept a list of `(start_min, end_min, state)` tuples (same pattern as `GroundProgram`) so sigma shifts mid-simulation as convective weather arrives.

**Calibration note:** ATL's parallel runway geometry reduces weather sensitivity compared to JFK, so the IMC/LIFR sigmas are lower. The 0.480/0.580 values are first-pass estimates; verify against a set of known-IMC days from METAR records.

**Expected impact:** p95 taxi-out on weather days improves from -20 min delta to ±10 min. D0 on outlier days (Aug 16: -13.7%) should improve by 5-8pp once distributional tails are correctly modeled.

---

## Notes on Approach 2 (implemented)

Per-hour baseline scaling (`hourly_taxi_out_scale`) was added to `config.py` and `simulation.py`. ATL calibration uses 0.87 for hours 0-5 and 0.92 for hours 6 and 23, derived from the FAA ASPM ATL unimpeded taxi-out time (~17 min) relative to concourse peak means (~17-22 min). The correction is smaller than JFK because ATL's concourse means are already closer to unimpeded values.
