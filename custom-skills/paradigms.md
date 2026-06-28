# Simulation Paradigms

How to choose a paradigm, and how to implement each one correctly in Python.
The wrong paradigm makes a problem awkward or impossible; the right one makes it
natural. Match the paradigm to how the system actually behaves, not to what you
know best.

## Contents
1. Discrete-Event Simulation (DES)
2. Agent-Based Modeling (ABM)
3. System Dynamics (SD)
4. Monte Carlo Simulation
5. Continuous / Numerical Simulation
6. Hybrid models
7. Selection checklist

---

## 1. Discrete-Event Simulation (DES)

**Use when** the system is naturally described as discrete entities (customers,
jobs, parts, packets) moving through processes and competing for limited
resources (servers, machines, beds), where state changes only at distinct event
instants. Canonical domains: queueing systems, manufacturing lines, logistics,
healthcare patient flow, call centers, networks.

**Mental model.** State changes only at events. Time jumps from one event to the
next via a future-event list (event calendar), never tick-by-tick. Between
events nothing changes, so DES is efficient for systems with long idle stretches.

**Key concepts:** entities, attributes, events, the event calendar, resources
with queues, queue discipline (FIFO/priority), and statistics accumulated over
time (e.g. time-average queue length, not simple average of snapshots).

**Python:** SimPy (process-based). Model each entity as a generator that
`yield`s on timeouts and resource requests.

```python
import simpy, numpy as np

def customer(env, server, rng, waits):
    arrive = env.now
    with server.request() as req:
        yield req                                  # wait for a free server
        waits.append(env.now - arrive)             # delay in queue
        yield env.timeout(rng.exponential(1/MU))   # service time

def source(env, server, rng, waits):
    while True:
        yield env.timeout(rng.exponential(1/LAM))  # interarrival
        env.process(customer(env, server, rng, waits))

def run_once(seed, horizon, n_servers=1):
    rng = np.random.default_rng(seed)
    env = simpy.Environment()
    server = simpy.Resource(env, capacity=n_servers)
    waits = []
    env.process(source(env, server, rng, waits))
    env.run(until=horizon)
    return np.mean(waits)        # one replication's mean wait
```

**Pitfalls.**
- *Time-average vs. count-average.* Utilization and mean queue length are
  time-averages (weight by how long the system held each value), not the mean of
  observations. SimPy resource monitoring or your own time-weighted accumulators.
- *Warmup.* Steady-state DES starts empty-and-idle, biasing early observations
  low. Remove the transient (see output-analysis).
- *Validate against theory.* For an M/M/1 queue the mean wait has a closed form
  (Wq = ρ/(μ−λ)); check your sim reproduces it before trusting harder cases.
- *Tie-breaking and event ordering* at identical timestamps must be deterministic
  and intentional.

---

## 2. Agent-Based Modeling (ABM)

**Use when** system behavior *emerges* from many autonomous agents following
local rules and interacting with each other and an environment, and you care
about heterogeneity, adaptation, spatial/network structure, or emergent
macro-patterns you can't write down top-down. Domains: epidemics, traffic, crowd
dynamics, markets, ecology, opinion dynamics, supply networks at the actor level.

**Mental model.** Define agents (state + behavior rules), an environment (grid,
network, or continuous space), and a scheduler that advances agents each step.
Macro behavior is *observed*, not programmed.

**Python:** Mesa. Define an `Agent.step()` and a `Model` with a scheduler and a
`DataCollector`.

```python
import mesa

class Walker(mesa.Agent):
    def step(self):
        # local rule: move, interact with neighbors, update state
        ...

class World(mesa.Model):
    def __init__(self, n, seed=None):
        super().__init__(seed=seed)
        self.grid = mesa.space.MultiGrid(20, 20, torus=True)
        for _ in range(n):
            a = Walker(self)
            self.grid.place_agent(a, (self.random.randrange(20),
                                      self.random.randrange(20)))
        self.datacollector = mesa.DataCollector(model_reporters={...})
    def step(self):
        self.datacollector.collect(self)
        self.agents.shuffle_do("step")
```

**Pitfalls.**
- *Scheduling artifacts.* Synchronous (all agents see the same old state) vs.
  asynchronous (random activation, agents see updates within the step) can change
  results materially. Choose deliberately and report it.
- *Emergence still needs validation.* "It produced a plausible pattern" is not
  validation. Calibrate to data and check the macro-statistics, not just the
  picture.
- *Stochastic and sensitive.* ABMs are noisy and often sensitive to parameters
  and initial conditions — replicate runs and do global sensitivity analysis.
- *Scale.* Cost grows with agents × interactions × steps; profile early.

---

## 3. System Dynamics (SD)

**Use when** you care about aggregate quantities and the *feedback structure*
driving them over time, not individual entities. Stocks (accumulations), flows
(rates), and feedback loops with delays. Domains: population, epidemiology at the
compartment level (SIR), resource depletion, business policy, macro supply chains.

**Mental model.** A system of coupled differential (or difference) equations:
stocks integrate their net inflows. Continuous and deterministic at core (add
noise explicitly if needed). Feedback loops (reinforcing/balancing) and delays
produce the interesting dynamics — overshoot, oscillation, S-curves.

**Python:** integrate the ODEs directly with `scipy.integrate.solve_ivp`.

```python
from scipy.integrate import solve_ivp

def sir(t, y, beta, gamma):
    S, I, R = y
    N = S + I + R
    return [-beta*S*I/N, beta*S*I/N - gamma*I, gamma*I]

sol = solve_ivp(sir, (0, 160), [999, 1, 0], args=(0.3, 0.1),
                dense_output=True, max_step=1.0)
```

**Pitfalls.**
- *No entities, no individual variability* — if heterogeneity or discrete
  resource contention matters, SD is the wrong tool (use ABM or DES).
- *Structure is the model.* Get the feedback loops and delays right; that's where
  SD earns its keep and where it misleads if wrong.
- *Numerical care* with stiff systems and step size; validate against known
  closed-form or conserved quantities (e.g. S+I+R constant above).

---

## 4. Monte Carlo Simulation

**Use when** you need to propagate uncertainty or estimate an expectation,
probability, or distribution via repeated random sampling — risk analysis,
uncertainty quantification, high-dimensional integration, option pricing,
reliability. Often a *component* of the other paradigms (the replication engine)
rather than a standalone model.

**Mental model.** Draw many samples from input distributions, evaluate the
quantity of interest for each, and characterize the resulting output
distribution. Accuracy improves as O(1/√N): to halve the error, quadruple the
samples — which is why variance reduction matters (see output-analysis).

```python
import numpy as np
rng = np.random.default_rng(0)
samples = g(rng.normal(mu, sigma, size=N))   # propagate input uncertainty
est   = samples.mean()
half  = 1.96 * samples.std(ddof=1) / np.sqrt(N)   # 95% CI half-width
```

**Pitfalls.**
- *Report the CI.* The estimate is itself random; without a half-width you can't
  tell signal from sampling noise.
- *Garbage-in.* The output distribution is only as good as the input
  distributions and their correlation structure — fit them, don't guess.
- *Rare events* need importance sampling or stratification; crude Monte Carlo
  wastes nearly all samples estimating a small probability.

---

## 5. Continuous / Numerical Simulation

**Use when** state evolves continuously under physical laws expressed as ODEs or
PDEs — mechanics, circuits, control systems, fluids, heat, chemical kinetics.

**Mental model.** Discretize time (and space for PDEs) and integrate. Solver
choice (explicit vs. implicit, fixed vs. adaptive step) governs stability and
accuracy. Stiff systems demand implicit methods.

**Python:** `scipy.integrate.solve_ivp` (use `method='Radau'`/`'BDF'` for stiff
problems) for ODEs; dedicated frameworks (e.g. FEniCS, py-pde) for PDEs.

**Pitfalls.**
- *Stability and stiffness.* Wrong method or step size gives plausible-looking
  but wrong trajectories — verify with energy/mass conservation or a refined-step
  comparison (Richardson-style convergence check).
- *Tolerance ≠ truth.* Tightening solver tolerance reduces numerical error, not
  model error.

---

## 6. Hybrid models

Real systems often need more than one paradigm: DES for discrete flow with a
continuous sub-process (tank level, temperature) between events; ABM agents whose
internal state follows ODEs; SD policy layer over a DES operational layer.
Combine deliberately and keep the coupling explicit — define exactly when the
continuous part is advanced relative to discrete events, and validate the
interface, which is where hybrid models most often break.

---

## 7. Selection checklist

- Discrete entities competing for resources, with queues? → **DES**
- Behavior emerges from many interacting autonomous actors? → **ABM**
- Aggregate stocks/flows and feedback, no individuals needed? → **SD**
- Propagating uncertainty / estimating a probability or expectation? → **Monte Carlo**
- Continuous physical state under ODE/PDE laws? → **Continuous/numerical**
- More than one of the above is essential? → **Hybrid**, with an explicit interface.

When two paradigms could work, pick the one that represents the *driver of your
KPI* most naturally, and prefer the simpler one unless the question demands the
detail of the richer one.
