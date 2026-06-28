# Crew Analytics: Metrics, Cost Drivers & Optimization

How the pilot and FA rules turn into numbers — the metrics that measure crew
productivity and cost, the optimization that builds the schedule, and the links
back to operational success (D0/A0). The recurring expert move is to reason from
**credit, not block**, and to treat rules as the constraints that set the cost.

## Contents
1. The three clocks: block, duty, credit
2. Productivity and cost metrics
3. Pairing optimization: objective and constraints
4. Reserve sizing and utilization
5. Premium open time as a signal
6. Crew analytics ↔ operational metrics
7. Data and analysis patterns

---

## 1. The three clocks: block, duty, credit

Every crew metric starts from distinguishing:

- **Block** — flight time produced (the output the airline actually needs).
- **Duty** — time crews are on the clock (report to release).
- **Credit** — time crews are paid = max(block, rigs, guarantees).

The wedge between credit and block is where rules create cost. **Pay-above-block**
(credit ÷ block, often expressed as a percentage over 100%) is the headline crew-
productivity metric: a value near 1.0 means efficient pairings; high values mean
rigs/guarantees/short-duty trips are inflating pay relative to flying produced.

## 2. Productivity and cost metrics

- **Credit ÷ block (pay-to-block ratio).** Primary efficiency measure; lower is
  more efficient for the airline, and rigs are designed to put a floor under it for
  crews.
- **Block (or credit) per duty day / per TAFB day.** How much flying a trip
  produces per day worked or per day away from base — productivity of pairings.
- **Average Line Value (ALV)** and **line vs. guarantee gap.** How close awarded
  lines sit to target, and how much guarantee "make-up" pay is being triggered.
- **Reserve guarantee cost and utilization** (see §4).
- **Premium-pay rate** (share of flying covered by slips/incentive open time) —
  cost and staffing-health signal (see §5).
- **Crew cost per block hour / per ASM / per departure** — rolling crew rules,
  pay rates, rigs, and reserve into unit cost.
- **Deadhead ratio** — repositioning (paid, non-productive) as a share of credit;
  high deadhead signals network/base imbalance.
- **Productivity loss to legality** — block lost to FDP/rest limits, reduced-crew
  constraints, or training/leave footprints.

## 3. Pairing optimization: objective and constraints

Crew scheduling is a large constrained optimization in two stages:

1. **Crew pairing problem** — assemble the month's flying into legal pairings that
   cover every flight at minimum cost (minimize total credit, deadhead, and hotel/
   per-diem, i.e. minimize pay-above-block).
2. **Crew rostering / line construction** — assemble pairings into lines. At Delta
   pilots, this is **PBS** honoring seniority-ordered bid preferences subject to
   line-construction parameters; FAs bid lines under company rules.

The constraints are exactly the rules in the other two references:

- **Legality (hard):** FAR 117 FDP/rest/cumulative limits for pilots; Part 121
  §121.467 rest and §121.391 staffing for FAs. Non-negotiable.
- **Contractual / policy (cost-bearing):** rigs, minimum day, monthly guarantees,
  ALV bounds, reserve rules, deadhead/positioning rules, base/category structure.
- **Coverage:** every flight crewed at required composition; reserve depth to absorb
  disruption.

Good crew analytics evaluates a schedule on all three: is it legal, what does it
cost (pay-above-block, premium, deadhead), and does it cover the operation with
enough resilience.

## 4. Reserve sizing and utilization

Reserve is a coverage-vs-cost trade:

- **Reserve guarantee** is paid whether or not the reserve flies, so idle reserve is
  pure cost; uncovered flying (too little reserve) causes delays and cancellations
  (an operational cost that dwarfs guarantee pay).
- **Reserve utilization** = flown credit ÷ guaranteed credit; very low means
  over-staffed reserve, very high (near saturation) means thin coverage and fragile
  operations.
- **Reserve availability vs. required** (the daily count that gates drops/swaps)
  measures real-time flexibility — when "available < required," the operation
  stiffens (drops denied, junior assignment, premium pickups rise).
- Sizing reserve is a stochastic problem: model sick rates, irregular-ops demand,
  and trip-drop behavior against the guarantee cost to find the coverage that
  minimizes total (guarantee + disruption + premium) cost.

## 5. Premium open time as a signal

Green/white/yellow slips, swap-with-the-pot, and FA incentive open time cover
flying that opened up or that senior crews dropped — at premium rates. Read premium
usage two ways:

- **Cost:** premium pay above base credit — a direct unit-cost driver.
- **Diagnosis:** persistently high premium usage signals structural understaffing,
  thin reserve, schedule instability, or IT/process friction (e.g. drops the system
  can't recover efficiently). Trend it by category/base/fleet and correlate with
  reserve utilization.

## 6. Crew analytics ↔ operational metrics

Crew availability is an operational driver, so crew analytics ties directly to the
operational metrics (A0/D0, taxi-out, completion):

- A crew **timing out** (FDP/rest limit reached) or a **reserve gap** converts into
  a late departure (D0 hit) or a cancellation (completion hit) — often at a hub
  during a bank, where it cascades into connections and A0.
- **Schedule resilience** (block-time buffers, reserve depth, recovery rules)
  trades crew cost for operational reliability — the same A0/D0-protecting logic
  the operation uses, expressed in crew terms.
- **Recovery/reroute rules** determine how fast the airline can re-crew a broken
  operation, directly shaping irregular-ops recovery speed.

When evaluating operational success, attribute crew-caused delay (crew legality,
reserve shortfall, staffing) separately from ATC/weather/ground causes — it's a
distinct, controllable lever.

## 7. Data and analysis patterns

- **Crew management system data** (Delta DBMS via iCrew/eCrew for pilots; the
  inflight equivalents for FAs) — pairings, lines, reserve, assignments, drops/
  swaps, premium pickups.
- **Bid packages / PBS awards** — line values, ALV, reserve line counts, award
  penetration by seniority.
- **Pay/credit records** — block vs. credit vs. duty for pay-above-block, rig
  trigger frequency, premium and deadhead shares.
- **OOOI/ASPM operational data** — to link crew events to D0/A0 outcomes.

Patterns:

- **Always reason in credit.** Convert any "hours" question to block-vs-credit
  before costing it.
- **Decompose pay-above-block** into rig-driven, guarantee-driven, deadhead, and
  premium components — each has a different lever.
- **Normalize by category.** Widebody vs. narrowbody, base, and seat have very
  different rig/guarantee/reserve dynamics; never pool them blindly.
- **Trade coverage against cost explicitly.** Present reserve and buffer decisions
  as (guarantee + premium) cost vs. avoided disruption, not as a single number.
- **Date and source every figure.** PWA values, FA policy, and FARs change; a crew-
  cost result is only as current as the rule set behind it.
