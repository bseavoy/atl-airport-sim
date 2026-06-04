# Validation Data for ATL Airport Simulation

This directory holds real and synthetic flight data used to validate the simulation model.

## Real Data Sources

### 1. BTS On-Time Performance Data (Primary)

**URL:** https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ

**How to Download:**
1. Visit the URL above and select **Reporting Carrier On-Time Performance (1987–present)**
2. Filter: Year = **2025**, Month = **6 (June)**
3. Select these columns:
   - `FlightDate`
   - `Reporting_Airline` (carrier code)
   - `Flight_Number_Reporting_Airline`
   - `Tail_Number`
   - `Origin` / `Dest`
   - `CRSDepTime`, `DepTime`, `DepDelay`, `DepDelayMinutes`
   - `CRSArrTime`, `ArrTime`, `ArrDelay`, `ArrDelayMinutes`
   - `Cancelled`, `CancellationCode`
   - `TaxiOut`, `TaxiIn`
   - `WheelsOff`, `WheelsOn`
   - `ActualElapsedTime`, `AirTime`
   - `ArrDel15`, `DepDel15`
4. Download as CSV. Filter the result for `Origin == 'ATL' OR Dest == 'ATL'` and `FlightDate == '2025-06-01'`.

**Key Validation Metrics Available:**
- `TaxiOut` — actual gate-to-runway taxi time (minutes)
- `TaxiIn` — actual runway-to-gate taxi time (minutes)
- `DepDelay` / `ArrDelay` — schedule deviation
- `WheelsOff` - `DepTime` = pushback + taxi-out duration

### 2. FAA ASPM (Aviation System Performance Metrics) Taxi Time Data

**URL:** https://aspm.faa.gov/apm/sys/main.asp

**How to Access:**
1. Log in (free registration required) at https://aspm.faa.gov
2. Navigate to **APM → Taxi Time Reports**
3. Select airport **ATL**, date range **June 1–30, 2025**
4. Download the taxi time summary CSV which includes:
   - Mean taxi-out time by hour
   - Mean taxi-in time by hour
   - Congestion metrics

**Key ASPM Columns:**
- `apt` — airport code
- `day` — date
- `hour` — local hour (0–23)
- `taxi_out_avg` — mean taxi-out time for that hour
- `taxi_in_avg` — mean taxi-in time for that hour
- `departures`, `arrivals` — counts

### 3. FlightAware / FlightRadar24 (Optional Gate-Level Detail)

For gate-level validation, FlightAware's AeroAPI (paid) or FlightRadar24 historical data provides:
- Actual gate assignment
- Actual pushback time
- Block-in / block-out times

## Running the Validation Script

```bash
# Install dependencies first
pip install -e .

# Run with BTS data
python validation/validate.py \
  --simulated results/simulation_output.csv \
  --actual data/validation/bts_june1_2025_atl.csv \
  --source bts \
  --output validation_report/

# Run with the synthetic sample (no download needed)
python validation/validate.py \
  --simulated results/simulation_output.csv \
  --actual data/validation/sample_june1_2025.csv \
  --source sample \
  --output validation_report/
```

## Synthetic Sample File

`sample_june1_2025.csv` contains ~20 realistic synthetic flights using real airline codes,
real ATL gate/concourse assignments, and realistic times. Use this to run a quick demo
without downloading the full BTS dataset.

## Expected Accuracy Targets

Based on published ATL ASPM benchmarks:
| Metric | Typical ATL Value | Acceptable Sim Error |
|---|---|---|
| Mean taxi-out (min) | 18–22 min | ±3 min |
| Mean taxi-in (min) | 7–11 min | ±2 min |
| On-time departure rate | 75–85% | ±5 pp |
| Gate utilization | 60–75% | ±10 pp |
