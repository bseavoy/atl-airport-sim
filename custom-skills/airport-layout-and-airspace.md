# ATL: Airfield, Terminals & Control Structure

The physical and control layout of Hartsfield-Jackson, which determines capacity,
taxi distances, queue points, and who controls each aircraft where.

## Contents
1. The airfield: five parallel runways and flow
2. Arrival/departure segregation and taxi geography
3. Terminals, concourses, and the Plane Train
4. The control stack: ramp, tower, TRACON, Center
5. Deicing facilities
6. Capacity and constraints

---

## 1. The airfield: five parallel runways and flow

ATL has **five parallel east-west runways**, the source of its very high
throughput. They operate in two flow directions:

- **West operation** — landing/departing to the west (runways 26/27/28 ends).
- **East operation** — to the east (8/9/10 ends).

Because the runways are parallel, ATL can run multiple arrival and departure
streams at once. The flow direction (driven by wind/weather) flips which runway
ends are active and reshapes every taxi route and queue point — so "ATL taxi-out"
is meaningless without stating the configuration.

The runways span north and south sides of the midfield terminal complex; the
fifth runway (the southernmost, 10/28, opened in the 2000s) sits across a taxiway
bridge that lets arrivals cross without blocking departures. Approximate layout
north-to-south: 8L/26R, 9L/27R (north side), then the terminal complex, then
9R/27L, 8R/26L, and 10/28 (south side). Always confirm the live config rather than
assuming.

## 2. Arrival/departure segregation and taxi geography

ATL's operating model **segregates arrivals and departures onto different parallel
runways** (e.g. outboard arrivals, inboard departures, or vice versa depending on
config), which is what lets it sustain simultaneous high arrival and departure
rates. Consequences for analysis:

- **Taxi distance depends on concourse + active runway.** A departure off a given
  concourse may face a short or long taxi depending on whether the near or far
  parallel is the active departure runway in the current flow.
- **Departure queues build at specific hold points** fed by specific taxiways;
  ground control taxis aircraft to balance the departure runways and build orderly
  queues. A ground-metering position may open during pushes to manage frequency
  congestion and queue order.
- **The ramp/movement boundary ("spots")** is where Delta ramp control hands
  aircraft to the FAA tower; spot throughput during a bank is a real constraint.

## 3. Terminals, concourses, and the Plane Train

- **Two terminal complexes:** the **Domestic Terminal** (North and South
  landside check-in) and the **Maynard H. Jackson Jr. International Terminal**.
- **Seven concourses in a linear midfield spine:** **T – A – B – C – D – E – F**
  (~190–200 gates total). Domestic flying concentrates on T/A/B/C/D; international
  on E/F (Concourse F is the international/CBP facility). Delta and Delta Connection
  dominate the domestic concourses; regional (small-gauge) flying is heavy on the
  inner concourses.
- **The Plane Train** (automated people mover) and a parallel underground
  pedestrian walkway connect all concourses airside, running continuously — central
  to passenger connection times within a bank.
- Capital work proceeds under the **ATLNext** program (concourse expansion/
  modernization, parking, roadways, deicing) — gate counts and facilities change,
  so verify current numbers.

## 4. The control stack: ramp, tower, TRACON, Center

From the gate outward:

1. **Delta ramp control (non-movement area).** Delta operates ramp towers that
   direct pushbacks and movement on the concourse ramps/apron. Phraseology like
   "Atlanta ramp, Delta 1234, ramp 1 south, taxi" reflects ramp-control direction
   before the FAA handoff. (Some ramp taxiway segments are explicitly
   non-movement, not ATC-controlled.)
2. **ATL ATCT (FAA tower) — movement area.** Ground control (taxiways) and local
   control (runways); a ground-metering position can be opened during congestion.
3. **A80 — Atlanta TRACON.** Terminal arrival/departure sequencing in the Atlanta
   metro airspace.
4. **ZTL — Atlanta ARTCC (Center).** En route control of the surrounding region;
   its TMU coordinates metering and MIT with the ATCSCC.
5. **ATCSCC.** National TMIs (GDP/GS/AFP/CTOP) that bind ATL arrivals/departures.

The handoff seams — ramp↔tower (spots) and tower↔TRACON↔Center — are where ATL
surface and departure delay concentrate during banks.

## 5. Deicing facilities

ATL runs hub-scale deicing. A large centralized **south deicing complex** (a
~$147M facility completed in early 2023) was built to deice many aircraft
simultaneously — designed for several large widebodies or many narrowbodies at
once — to meet the goal of zero cancellations from deicing events, alongside other
deice capacity on the field. Centralized pad deicing protects holdover time but
adds a taxi leg and a queue, so in winter the deice strategy (gate vs. pad,
sequencing, fluid/truck/crew capacity) becomes a dominant driver of taxi-out and
D0.

## 6. Capacity and constraints

- **Capacity side:** the airport's arrival/departure acceptance rates (AAR/ADR)
  under the active config and weather; runway occupancy and crossing constraints;
  spot/ramp throughput; gate availability within a bank.
- **Demand side:** the banked schedule concentrates demand into peaks that test
  every resource at once.
- **Weather:** flow direction changes, reduced-visibility configs, convective
  weather (AFP/CTOP reroutes), and winter deice all cut effective capacity.
- **The binding constraint shifts** across a day between runway, ramp/spots,
  gates, and deice — identify which is binding before proposing a fix.

Confirm live configuration, AAR/ADR, gate counts, and facility status against
current ATL/FAA sources; these are operationally dynamic.
