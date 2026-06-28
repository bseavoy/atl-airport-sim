# Statistical Output Analysis

A simulation's output is data, and stochastic simulation output is *random* data
with structure (autocorrelation, initialization bias) that defeats naive
statistics. This is where most analyses silently go wrong: a confident number
with a confidence interval that is too narrow, computed from correlated
observations after a biased warmup. Get this right and the rest of the work pays
off; get it wrong and a perfectly built model produces misleading conclusions.

## Contents
1. Input modeling (garbage-in control)
2. Terminating vs. steady-state simulations
3. Removing the initialization transient (warmup)
4. The independence problem: replications and batch means
5. Confidence intervals and choosing the number of runs
6. Comparing alternative systems
7. Variance reduction
8. Sensitivity analysis
9. Surrogate models and simulation optimization
10. Common pitfalls

---

## 1. Input modeling

The output distribution can be no better than the input distributions feeding it.

- **Fit to data, don't assume.** Fit candidate distributions with `scipy.stats`
  (MLE), compare with AIC/BIC, and check goodness-of-fit (Q-Q plots, KS or
  Anderson-Darling). Don't default to normal/uniform out of convenience.
- **Use the empirical distribution or bootstrap** when no parametric form fits, or
  when data is too scarce to fit confidently.
- **Handle nonstationarity.** Arrival rates often vary by time of day → use a
  nonstationary Poisson process (thinning), not a single average rate, or you
  erase the peaks that drive congestion.
- **Handle correlation.** If inputs are correlated (e.g. order size and order
  type), sampling them independently misrepresents the system. Model the joint
  structure (copulas, conditional sampling).
- **Propagate input uncertainty.** With limited data, the fitted parameters are
  themselves uncertain (*epistemic* uncertainty), distinct from the simulation's
  inherent randomness (*aleatory*). To reflect both, bootstrap the input data,
  refit, and run the simulation per bootstrap sample; the spread of results then
  includes input uncertainty. Reporting only aleatory noise overstates precision.

---

## 2. Terminating vs. steady-state simulations

This distinction drives the entire analysis strategy — settle it first.

- **Terminating simulation.** A natural start and stop define the run (a shop open
  9–5, a project from start to delivery, a mission of fixed duration). The
  quantity of interest is over that finite horizon, *including* the startup
  transient — it's part of reality, so **do not** remove warmup. Analysis is by
  **independent replications**: each replication = one independent realization of
  the whole horizon.

- **Steady-state (non-terminating) simulation.** You want long-run behavior of a
  system that conceptually runs indefinitely (a 24/7 server, a continuous
  production line). The initial empty-and-idle state biases early observations, so
  you **must** remove the warmup transient, and you must deal with the strong
  autocorrelation of a long single run.

Picking the wrong frame is a category error: removing warmup from a terminating
model deletes real behavior; *not* removing it from a steady-state model biases
every estimate toward the artificial empty start.

---

## 3. Removing the initialization transient (warmup)

For steady-state metrics only.

**Welch's graphical procedure** (robust default):
1. Run *n* replications, each producing the time series of the metric,
   `Y[i][j]` (replication *i*, observation *j*).
2. Average **across replications** at each position *j*: `Ybar[j] = mean_i Y[i][j]`.
   Averaging across independent reps cuts the noise so the trend is visible.
3. Apply a moving-average window *w* to smooth `Ybar`.
4. Plot the smoothed series and choose the warmup length *l* where it flattens —
   i.e. where the initialization bias has died out. Discard observations before
   *l*.

```python
import numpy as np
def welch(Y, w):                      # Y: (n_reps, n_obs)
    ybar = Y.mean(axis=0)
    k = len(ybar)
    sm = np.empty(k)
    for j in range(k):
        lo, hi = max(0, j-w), min(k, j+w+1)
        sm[j] = ybar[lo:hi].mean()
    return sm                         # plot, pick l where it levels off
```

Alternatives: **MSER-5** (automated, picks the truncation point minimizing the
standard error of the retained mean). Whatever you use, **report the warmup
length you removed** — it's a modeling choice that affects every result.

---

## 4. The independence problem: replications and batch means

Within a single run, consecutive observations are autocorrelated (one customer's
long wait makes the next one's likely long too). So the ordinary sample standard
deviation **understates** true variability, producing confidence intervals that
are too narrow — overconfident and often wrong. Two correct approaches:

**Independent replications (preferred when feasible; required for terminating
simulations).** Run *n* independent replications with **different, non-overlapping
random streams**. Take **one summary value per replication** (e.g. that
replication's mean wait). These *n* values are i.i.d., so ordinary statistics
apply to them. Do *not* pool all raw observations across replications and treat
them as one big i.i.d. sample — only the per-replication summaries are
independent.

```python
import numpy as np
ss = np.random.SeedSequence(12345)
seeds = ss.spawn(n_reps)                     # independent streams
x = np.array([run_once(s) for s in seeds])   # one summary per replication
mean = x.mean()
half = 1.96 * x.std(ddof=1) / np.sqrt(n_reps)  # or t-quantile for small n_reps
```

**Batch means (for a single long steady-state run).** When one long run is
cheaper than many (heavy warmup cost), discard the warmup, then split the
remaining *N* observations into *k* contiguous batches of size *m*. Each batch
mean is approximately independent **if *m* is large enough** that lag-1
autocorrelation between batch means is negligible — check it. Then treat the *k*
batch means as i.i.d. and form a t-CI. Too-small batches → correlated batch means
→ CI still too narrow, which defeats the purpose.

Replications are conceptually cleaner and parallelize trivially (each replication
is embarrassingly parallel); batch means avoids paying the warmup cost repeatedly.

---

## 5. Confidence intervals and choosing the number of runs

**Always report a CI**, not a bare mean. For *n* independent values (replications
or batch means) with sample mean x̄ and sample std *s*:

`CI = x̄ ± t_{n−1, 1−α/2} · s / √n`

Use the *t* quantile (not 1.96) when *n* is small. For a proportion/probability,
use a proportion CI. For a quantile (e.g. 95th-percentile wait), the mean-based CI
doesn't apply — estimate the quantile per replication and CI across replications,
or use order-statistic methods.

**How many runs?** Two strategies:
- *Fixed target half-width ε.* From a pilot of n₀ runs with std s₀, the runs
  needed for absolute half-width ε is roughly `n* ≈ (t · s₀ / ε)²`. Iterate, since
  *s* updates as you add runs.
- *Sequential / relative precision.* Keep adding replications until the half-width
  is within a target fraction of the mean (e.g. half-width ≤ 5% of the mean), then
  stop. Practical and self-tuning.

More runs shrink the CI as 1/√n — diminishing returns, so variance reduction
(below) is often a better lever than brute-force run count.

---

## 6. Comparing alternative systems

The goal is usually to compare configurations, and the right method controls for
the Monte Carlo noise that can otherwise masquerade as a real difference.

- **Two systems — paired-t with Common Random Numbers (CRN).** Run both systems
  with the *same* random number streams across paired replications, so they face
  the same arrivals/service draws. For replication *i*, `D_i = X_i − Y_i`; build a
  t-CI on the mean of `D`. CRN induces positive correlation between X and Y, which
  *reduces* the variance of the difference and sharpens the comparison. (Requires
  careful stream synchronization — assign each stochastic source its own stream so
  the same draws line up across systems.)
- **Unequal variances.** Use the Welch t-interval rather than assuming equal
  variance.
- **Many systems.** Don't run a blizzard of pairwise t-tests — multiplicity
  inflates false positives. Use **Multiple Comparisons with the Best (MCB)** to
  bound each system's gap from the best, or **indifference-zone ranking &
  selection** to pick the best with a guaranteed probability of correct selection
  within a practically meaningful margin.
- **Interpretation.** If CIs overlap, the data don't support claiming a
  difference — say so, rather than ranking on point estimates. A 2% difference
  inside ±10% noise is noise.

---

## 7. Variance reduction

These get a tighter estimate from the *same* number of runs — often more
efficient than simply running more.

- **Common Random Numbers (CRN).** For comparisons: sync streams across systems so
  differences reflect the design change, not different luck. (See §6.)
- **Antithetic variates.** Pair each run using `U` with one using `1−U`; negatively
  correlated pairs reduce the variance of the average. Good for a single-system
  mean.
- **Control variates.** Use a correlated quantity with known mean to adjust the
  estimate, removing part of its variance.
- **Stratified / Latin hypercube sampling.** Cover the input space more evenly than
  crude random sampling, especially in higher dimensions (`scipy.stats.qmc`).
- **Importance sampling.** Essential for **rare events**: sample from a distribution
  that visits the rare region more often, then reweight. Crude Monte Carlo wastes
  almost all effort when the event probability is tiny.

Always verify a variance-reduction scheme is unbiased for your estimator before
trusting the tighter interval — a few techniques are easy to misapply into bias.

---

## 8. Sensitivity analysis

Which inputs actually drive the result? This guides where to invest in data,
flags fragile conclusions, and is itself a form of validation.

- **Local (one-at-a-time).** Perturb each input around a baseline and measure the
  response. Cheap, but misses interactions and is only valid near the baseline —
  don't rely on it alone for nonlinear models.
- **Global, variance-based (Sobol indices).** Attribute output variance to each
  input and to interactions. First-order index `S1` = main effect; total index
  `ST` = main + all interactions; a large `ST − S1` flags interaction effects.
  Use **SALib**:

```python
from SALib.sample import sobol as sobol_sample
from SALib.analyze import sobol as sobol_analyze
problem = {'num_vars': 3, 'names': ['a','b','c'],
           'bounds': [[0,1],[0,1],[0,1]]}
X  = sobol_sample.sample(problem, 1024)
Y  = np.array([model(*row) for row in X])
Si = sobol_analyze.analyze(problem, Y)     # Si['S1'], Si['ST']
```

- **Morris screening.** Cheap global *screening* to find the few influential inputs
  before spending on full Sobol — ideal when each model run is expensive.

Report which inputs the conclusion depends on. A result that hinges on a
poorly-known input is a result to flag, not to ship.

---

## 9. Surrogate models and simulation optimization

- **Surrogate / metamodel.** When each simulation run is expensive, fit a cheap
  approximation of the input→output response (Gaussian process / kriging,
  polynomial response surface, or regression) on a designed set of runs, then use
  the surrogate for fast exploration, optimization, and sensitivity. Always
  validate the surrogate on held-out runs before trusting it, and respect its
  range of validity.
- **Simulation optimization.** Searching for the best configuration when the
  objective is a noisy simulation output. Approaches: **Bayesian optimization**
  (GP surrogate + acquisition function — sample-efficient, ideal for expensive
  runs), metaheuristics (the OptQuest style of scatter search / tabu search),
  sample-average approximation, and stochastic gradient methods. Account for the
  output noise — the apparent best may just be a lucky run, so confirm the chosen
  configuration with extra replications (and ranking & selection from §6).

---

## 10. Common pitfalls (quick reference)

- Reporting one run as the answer — it's one sample of a random variable.
- No confidence interval, or a CI computed from autocorrelated observations
  treated as independent (too narrow → overconfident).
- Forgetting warmup removal for steady-state metrics — biases everything toward
  the empty start. Or removing warmup from a terminating model — deletes real
  behavior.
- Pooling raw observations across replications as if i.i.d. instead of using
  per-replication summaries.
- Batch means with batches too small to be uncorrelated.
- Comparing systems with independent (un-synchronized) streams and missing a real
  difference buried in noise — use CRN.
- Multiple pairwise tests across many systems without multiplicity control.
- Arbitrary input distributions; ignoring nonstationarity, correlation, or input
  (epistemic) uncertainty.
- Confusing precision with accuracy — a tight CI around a wrong (unvalidated)
  model is still wrong.
- Chasing fidelity the decision doesn't need, adding parameters you can't
  estimate.
