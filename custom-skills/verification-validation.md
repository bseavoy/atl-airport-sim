# Verification & Validation (V&V)

Two different questions, often confused:

- **Verification — "did we build the model *right*?"** Does the code faithfully
  implement the conceptual model? This is a debugging/correctness question,
  internal to the model.
- **Validation — "did we build the *right* model?"** Does the model represent the
  real system accurately enough *for its intended purpose*? This is a question
  about the model's relationship to reality.

A model can be perfectly verified and completely invalid (a flawless
implementation of wrong assumptions), or valid in concept but wrongly coded.
Credibility requires both. Validation is always relative to purpose: a model
valid for comparing two policies may be invalid for predicting absolute numbers.
There is no such thing as an "absolutely valid" model — only one validated to be
adequate for a stated use.

## Contents
1. Verification techniques
2. Validation techniques
3. How much credibility each technique buys
4. A practical V&V checklist

---

## 1. Verification techniques

Apply several; no single one is sufficient.

- **Structured walkthrough / trace.** Log events, entities, and state changes for
  a small run and trace them by hand against the conceptual model. Does the first
  customer arrive, queue, get served, and depart in the right order with the
  right timestamps? Tracing a handful of entities catches a large share of logic
  errors.
- **Degenerate / boundary tests.** Drive parameters to limits where the answer is
  obvious. Zero arrival rate → empty system. Service rate → ∞ → no queue. One
  server, deterministic times → hand-computable schedule. If the model violates
  the obvious case, it's wrong.
- **Extreme-condition tests.** Overload the system (arrival rate ≫ service rate)
  and confirm the queue grows without bound; starve it and confirm idleness.
  Behavior at extremes is easy to reason about and a sensitive bug detector.
- **Comparison to analytic / closed-form results.** Build the simplest version
  that has a known solution and check the simulation reproduces it. M/M/1, M/M/c
  queues, simple birth-death processes, conserved quantities in ODE models. This
  is the single most convincing verification when available.
- **Consistency / conservation checks.** Entities created = entities in system +
  departed. Mass/energy/probability conserved. Flow in = flow out at steady
  state. Violations reveal leaks in the logic.
- **Unit and regression tests.** Test components in isolation (the distribution
  sampler returns the right mean/variance; the queue discipline orders correctly)
  and lock in known-good outputs so refactors don't silently break behavior.
- **Seed/determinism check.** Same seed → identical output, bit for bit. If not,
  there's uncontrolled randomness or order-dependence to fix before any analysis.
- **Animation / visualization.** Watching entities move (or plotting state over
  time) surfaces logic errors that summary statistics hide — but treat it as a
  bug-finder, never as validation.

---

## 2. Validation techniques

- **Face validity.** Walk the model and its behavior past people who know the real
  system. Do the inputs, logic, and outputs look reasonable to a subject-matter
  expert? Cheap, and catches gross errors early, but it is the *weakest* form of
  evidence — necessary, not sufficient.
- **Input-data validation.** Validate the input distributions independently: were
  they fit to real data, do they pass goodness-of-fit, do they capture
  nonstationarity (time-of-day effects) and correlation? Most "the model is
  wrong" problems are actually "the inputs are wrong."
- **Historical-data / results validation.** Run the model under conditions you
  have real data for and compare output distributions (not just means) to the
  real system — using statistical tests or confidence intervals on the
  difference, not eyeballing. If you used some data to *build* the model, validate
  against *held-out* data.
- **Predictive validation.** The strongest test: use the model to predict the real
  system's behavior under conditions not used in building it, then observe the
  real outcome. Expensive and not always possible, but the most convincing.
- **Sensitivity-based validation.** Vary inputs and confirm the model responds in
  the direction and rough magnitude domain experts expect (more servers → shorter
  waits, and by a plausible amount). Builds confidence even without a real-world
  dataset, and flags structural errors when the response is qualitatively wrong.
- **Turing-style test.** Show experts a mix of real and simulated output without
  labels; if they can't reliably tell which is which, that's strong evidence of
  behavioral validity.
- **Extreme-condition and event validity.** Does the model behave correctly under
  rare/stress conditions, and do the *types* of events it produces match those of
  the real system?

---

## 3. How much credibility each technique buys

Think of credibility as accumulated evidence, weakest to strongest:

1. Face validity / animation — sanity only; necessary, far from sufficient.
2. Degenerate, extreme, and consistency checks — solid verification of internal
   logic.
3. Closed-form comparison — strong verification where a tractable case exists.
4. Historical-data validation on held-out data — strong validation.
5. Predictive validation against new real-world outcomes — strongest.

Stack them. A model defended only by "it looks reasonable" is not credible
regardless of how polished the analysis on top of it is. State explicitly which
of these you actually performed, because the reader's trust should scale with the
evidence, not with the confidence of the presentation.

---

## 4. Practical V&V checklist

Verification:
- [ ] Same seed reproduces identical output.
- [ ] Trace of a few entities matches the conceptual model by hand.
- [ ] Degenerate cases (zero load, infinite service) give the obvious answer.
- [ ] Extreme load behaves correctly (unbounded queue under overload).
- [ ] Simplified version matches a closed-form result where one exists.
- [ ] Conservation/consistency identities hold.
- [ ] Component unit tests and regression tests pass.

Validation (relative to the stated purpose):
- [ ] Input distributions fit to data and pass goodness-of-fit; nonstationarity
      and correlation handled.
- [ ] Output compared to real-system data on held-out conditions, statistically.
- [ ] Sensitivities run in the directions/magnitudes experts expect.
- [ ] Face validity confirmed with someone who knows the real system.
- [ ] The purpose and scope for which the model is considered valid are written
      down — along with where it is *not* to be trusted.
