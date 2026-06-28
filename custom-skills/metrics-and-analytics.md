# Metrics & Analytics: A Ground-Operations View

How to measure ground performance and tie outcomes back to the turn and the ramp.
The recurring expert move is to separate **propagated** delay (a late inbound)
from **turn-execution** delay, and **carrier-controllable** delay from
ATC/surface-imposed delay — because a station is fairly judged only on what it
controls.

## Contents
1. The OOOI backbone and turn time
2. On-time metrics: D0 / A0 / A14
3. Taxi-out: unimpeded vs. excess, from the ramp
4. Ground drivers of each metric
5. Data sources
6. Analysis patterns

---

## 1. The OOOI backbone and turn time

Operational measurement starts from four timestamps per flight — **OOOI**:
**O**ut (pushback), **O**ff (wheels off), **O**n (wheels on), **I**n (gate in).
For ground operations the key derived quantities are:

- **Turn time** = next-flight Out − this-flight In (ground time at the gate).
- **Taxi-out** = Off − Out.
- **Block** = In − Out.

Turn time is the ground team's primary clock. Compare actual turn against the
**minimum feasible turn** for that gauge/flight type and against scheduled ground
time — a turn that's late because the schedule was too tight is a planning
problem, not an execution one.

## 2. On-time metrics: D0 / A0 / A14

- **D0** — % departing at or before scheduled gate departure (zero late). The
  ground operation's headline metric; overwhelmingly carrier-controllable.
- **A0** — % arriving at the gate at or before schedule (zero late). Partly
  inherited from D0, block-time accuracy, and taxi/airspace.
- **A14** — % within 14 minutes (the DOT/industry "within 15" standard). Looser
  public benchmark.

The D0→A0 linkage is the ground story: a station improves arrival punctuality
mainly by protecting departure punctuality and turn integrity upstream. Watch the
A0-vs-A14 gap (many small misses erode A0 first) and never read on-time without
**completion factor** — cancelling to protect punctuality is not success.

## 3. Taxi-out: unimpeded vs. excess, from the ramp

Taxi-out (Off − Out) splits into:

- **Unimpeded** — nominal taxi under light traffic, by airport/carrier/season.
- **Excess** — actual minus unimpeded; the manageable part.

From the ground side, excess taxi-out is driven by: pushing into a congested ramp
or a long runway queue, ramp/movement-area handoff friction, runway configuration
and gate-to-runway distance, metering/gate-holds, and deice queues. A practical
congestion proxy is **N_pb** — departures already taxiing ahead when a flight
pushes back; excess climbs once the departure runway saturates. Gate-holding /
ramp metering converts runway-queue minutes into gate minutes (better fuel and
predictability) — useful, but it relocates where delay appears, so measure D0 and
taxi together, not in isolation.

## 4. Ground drivers of each metric

- **D0 drivers:** late inbound (propagation), boarding time, bag/cargo load
  completion, catering/fuel sequencing, closeout/paperwork, pushback crew/tug
  availability, ramp-control approval, gate conflicts.
- **A0 drivers:** inherited departure delay, block-time accuracy (padding helps
  A0 at the cost of utilization), taxi-out excess, and en route/airspace (see ATM
  skill).
- **Turn-time drivers:** gauge and flight type, load factor and carry-on volume,
  connection-bag surge in a bank, cleaning scope, crew swaps, gate/tow logistics.
- **Excess-taxi drivers:** surface congestion (N_pb), runway config, ramp layout,
  deice queue, metering.

## 5. Data sources

- **OOOI / ACARS** — the carrier's own timestamps; the ground truth for turn and
  D0 analysis.
- **ASPM** — OOOI-based taxi (incl. unimpeded), on-time, and airport-efficiency
  metrics by airport/carrier/hour; the standard reference for taxi-out.
- **ASQP** — DOT on-time and delay-cause data (the public on-time basis).
- **ASDE-X / surface surveillance** — positions for queue length, ramp congestion,
  and excess-taxi estimation.
- **Station/ramp systems** — gate-management, bag-handling (BHS), boarding, and
  GSE telematics for task-level turn diagnostics.
- **OPSNET / TFMS / advisories** — to fence off ATC/surface-imposed delay from
  ground-controllable delay during attribution.

## 6. Analysis patterns

- **Critical-path the turn.** Reconstruct the task timeline (deplane/clean/board +
  parallel tasks) and find the binding chain; that's where minutes are real.
- **Separate propagation from execution.** Decompose departure delay into inbound
  lateness vs. ground-time overrun; fix them differently (schedule/aircraft
  routing vs. staffing/process).
- **Attribute controllable vs. imposed.** Overlay TMIs, ramp-metering, and deice
  events so surface/ATC delay isn't charged to the ground team — and so genuine
  ground misses aren't excused.
- **Normalize to the bank and config.** A turn during a peak bank in a reduced
  runway configuration isn't comparable to an off-peak turn; control for hour,
  bank, gauge, and config.
- **Trace network effects.** Tie gate/hold-for-connection decisions to downstream
  A0 and misconnects — local on-time can trade against completion and connection
  performance.

Report turn time and D0 with the propagation split and the controllable/imposed
attribution; report taxi-out as unimpeded vs. excess. Numbers without those splits
invite the wrong fix.
