# The FAA Traffic Flow Management Toolbox

How the FAA balances capacity and demand in the NAS: who does it, and the
initiatives they use. Every initiative is a response to a demand/capacity
imbalance somewhere — an airport, a fix, a sector, or a volume of airspace.

## Contents
1. The facilities and who controls what
2. Collaborative Decision Making (CDM)
3. Terminal initiatives: GDP and Ground Stops
4. En route initiatives: AFP and CTOP
5. Tactical tools: TBFM/metering, MIT/MINIT, reroutes, Playbook
6. The TMI priority hierarchy
7. Surface management and TBO/NextGen
8. Core systems and terms

---

## 1. The facilities and who controls what

- **ATCSCC** (Air Traffic Control System Command Center) — the national nerve
  center. Owns the strategic picture, approves and issues national TMIs
  (GDP/AFP/CTOP/GS), publishes advisories, and runs the planning telcons. The
  approval authority for interfacility flow operations.
- **ARTCC (Center)** — en route control of a large region (e.g. ZTL = Atlanta
  Center). Its Traffic Management Unit (TMU/TMCs, supervised by an STMC) monitors
  and balances flows, implements MIT/metering, and coordinates with the ATCSCC.
- **TRACON** — terminal approach/departure control around busy metro areas (e.g.
  A80 = Atlanta TRACON). Sequences arrivals and departures, absorbs some metering
  delay via vectoring/speed.
- **ATCT (Tower)** — the airport's movement area: runways and taxiways. Issues
  taxi, takeoff, and landing clearances; runs ground/local/ground-metering
  positions.
- **Airline / ramp control** — the *non-movement* area (ramp/gates) is controlled
  by the airline or airport ramp tower, not the FAA. The handoff between ramp
  control and FAA ground control at the movement-area boundary is a key surface
  coordination point (and a place taxi-out delay hides).

## 2. Collaborative Decision Making (CDM)

CDM is the framework that makes the rest work: the FAA and flight operators share
a common operational picture (demand and capacity via TFMS, surfaced through the
Flight Schedule Monitor, FSM, and the Aggregate Demand List, ADL). Crucially, when
the FAA assigns delay to a carrier's flights, the **carrier decides which of its
flights take that delay** — via substitution (swap a slot to a more important
flight), cancellation (free a slot), and compression (recover unused slots). This
is why operational success is partly a carrier skill, not just an FAA outcome.

## 3. Terminal initiatives: GDP and Ground Stops

**Ground Delay Program (GDP).** When an airport's arrival demand exceeds its
(often weather-reduced) acceptance rate, the FAA assigns **EDCTs** (wheels-up
times) to inbound flights so they absorb the delay *on the ground at their origin*
rather than holding in the air. Modeled and managed in FSM. Under-delivery
(arriving below the stated rate) is a known inefficiency; techniques like
front-loading/Blanket Adjustment try to keep the arrival stream full.

**Ground Stop (GS).** A harder, usually shorter measure that halts departures to a
destination (or via a constraint) entirely — used for sudden capacity collapse
(weather, an incident, a saturated airport). A GS supersedes other TMIs for the
affected flights.

## 4. En route initiatives: AFP and CTOP

**Airspace Flow Program (AFP).** Targets an en route constraint (e.g. a line of
convective weather) defined by a Flow Constrained Area (FCA). It identifies
flights filed through that airspace and meters them with EDCTs — like a GDP, but
for a volume of airspace instead of an airport, so it can touch many origin/
destination pairs at once. Operators can avoid the EDCT by **rerouting** around
the FCA (trading ground delay for extra flight miles/time).

**Collaborative Trajectory Options Program (CTOP).** A more advanced TMI that
manages one or more FCAs and lets each operator submit a **Trajectory Options Set
(TOS)** — a ranked list of route/altitude/speed options each weighted by how much
ground delay the operator would accept to use it. CTOP then assigns each flight a
delay and/or reroute honoring those preferences. It's the most "collaborative"
initiative: the operator's TOS quality directly affects its outcome.

## 5. Tactical tools: TBFM/metering, MIT/MINIT, reroutes, Playbook

- **TBFM / metering (time-based flow management).** Schedules aircraft to a
  runway threshold or meter point with the least delay, absorbing it via
  ground/airborne speed and vectoring. Arrival metering, departure scheduling,
  and (increasingly) surface and terminal metering all live here. Distinct from
  TFMS programs and generally higher priority than EDCTs.
- **Miles-in-Trail (MIT) / Minutes-in-Trail (MINIT).** Required spacing between
  aircraft on the same route/fix/sector (often 10+ nm vs. the 5 nm en route
  minimum) to make a flow manageable or to merge traffic. A very common, low-
  visibility source of departure restriction.
- **Reroutes / Coded Departure Routes / National Playbook.** Pre-coordinated route
  sets used when weather or volume closes normal routings. PDRR/ABRR let ATC amend
  departure clearances quickly to mitigate constraints.
- **Capping/tunneling, LAADR.** Altitude restrictions used to keep flows clear of
  constrained airspace.

## 6. The TMI priority hierarchy

When more than one initiative could capture a flight, a set order decides which
binds (knowing this tells you the *actual* constraint on a delayed flight):

1. **Ground Stops** — supersede everything.
2. **TBFM / metering required times** — take priority over EDCTs.
3. **GDP EDCTs** — take priority over AFP/CTOP EDCTs.
4. **AFP / CTOP EDCTs**.

## 7. Surface management and TBO/NextGen

- **Trajectory-Based Operations (TBO) / NextGen.** The strategic direction:
  manage flights by time along their trajectory (TBM), use Performance-Based
  Navigation (PBN), and collaborate on preferred trajectories — to raise
  throughput, efficiency, and predictability.
- **TFDM (Terminal Flight Data Manager).** The FAA's surface program (FAA Order
  JO 7210.637): electronic flight data plus surface metering that holds aircraft
  at the gate when a runway queue is building, cutting **excess taxi-out time**
  and fuel burn while preserving throughput. Builds on earlier collaborative
  surface work (CDQM — Collaborative Departure Queue Management; CDS;
  surface-CDM; the SMA effort piloted at Atlanta in the 1990s).

## 8. Core systems and terms

- **TFMS** (Traffic Flow Management System) — the central system that ingests
  flight data, forecasts demand, and executes TMIs. **FSM** — the tool used to
  model/run GDPs and AFPs. **ADL** — the shared demand list.
- **EDCT** — assigned wheels-up time (±5 min compliance) in GDP/AFP/CTOP.
- **FEA/FCA** — Flow Evaluation Area (monitor) / Flow Constrained Area (control)
  lines drawn around a constraint; an FCA can become an AFP/CTOP.
- **OIS / NAS Status / advisories** — fly.faa.gov, where active TMIs and
  airport/airspace status are published in near-real time.
- **EDCT vs. "controlled" vs. "exempt"** — flights inside a program's scope/time
  window get controlled times; flights already airborne or outside scope are
  often exempt.

Confirm version-level details (TFMS sustainment releases, TFDM site deployment,
order revisions) against current FAA documentation — these change.
