# AnyLogic Experiments

An **experiment** is what actually runs a model: it specifies the top-level agent,
how parameters are set, the stop condition, randomness, memory, and what is
collected. A model can hold many experiments; each generates its own Java class
named after it, and that class is the entry point (in the IDE and in an exported
app).

## Contents
1. Settings every experiment shares
2. The experiment types and what each needs
3. OptQuest, licensing, and edition limits
4. Choosing the right experiment
5. Common run-time gotchas

---

## 1. Settings every experiment shares

- **Top-level agent** — usually `Main`; the experiment instantiates it as the
  model root.
- **Stop condition** — *Stop at specified time*, *Stop at specified date*, or
  *Never* (run indefinitely / until stopped by code). Terminating vs.
  steady-state intent lives here.
- **Randomness** — *Fixed seed* gives reproducible runs (same seed → identical
  results); *Random seed (unique experiments)* makes every run different. Choose
  deliberately: stochastic studies usually want random seeds across replications,
  while debugging wants a fixed seed. This single setting causes most "won't
  reproduce" / "always identical" confusion.
- **Maximum available memory** (Advanced) — the Java heap for the run. The default
  is small; raise it for large agent populations or built-in-database models, and
  *before exporting* a memory-hungry model.
- **Model time settings** — units, start/stop time or calendar dates.
- **Presentation/animation** — on for interactive runs, irrelevant when running in
  fast/headless mode.

## 2. The experiment types and what each needs

**Simulation.** The basic single run, with animation and the model window. Needs
a top-level agent and a stop condition. Use it to develop, debug, and watch one
realization. (Run it in *Virtual time* to go as fast as possible, or *Real time*
scaled for viewing.)

**Parameter Variation.** Runs the model many times across a set of parameter
values — freeform (you script the combinations), or a uniform/random grid over
ranges. Needs the parameters to vary, their ranges/values, the number of
replications per point (for stochastic models), and the outputs to collect.
The standard tool for sweeping a design space and for replication studies.

**Optimization.** Searches parameter space for the values that
minimize/maximize an objective, using the bundled **OptQuest** engine. Needs:
decision parameters with ranges/types, an **objective function**, optional
**constraints** and **requirements**, and a stopping rule (number of iterations
or automatic). For stochastic models, set replications per iteration so OptQuest
optimizes the mean, not noise.

**Calibration.** A specialized optimization that tunes parameters so model output
matches reference/empirical data (minimizing a discrepancy). Also OptQuest-based.
Needs the parameters to fit, the reference data, and the fitness/discrepancy
definition.

**Monte Carlo.** Runs the model many times with random inputs/seeds to produce the
distribution of an output. Needs the stochastic inputs/seed policy and the output
to characterize. Use for risk/uncertainty propagation.

**Sensitivity Analysis.** Varies one (or more) parameter across a range and shows
how outputs respond, to reveal which inputs drive the result. Needs the
parameter(s), range/step, and outputs.

**Compare Runs.** Lets the user launch multiple runs with different parameter
settings interactively and compare their outputs side by side. Useful for
what-if exploration with a human in the loop.

**Reinforcement Learning.** Configures the model as a training environment —
defining observation, action, and reward — so it can be driven by an external RL
framework, and exported for training. Needs the RL interface (observation/action
schema, reward, done condition) defined in the experiment. This is also the
cleanest built-in path to drive a model step-by-step from external code
(including Python).

**Custom Experiment.** A blank experiment where you write Java directly to control
everything — create the engine, instantiate `Main`, loop over runs, set
parameters, run, read outputs, and implement any bespoke logic. The most flexible
option and the natural entry point when embedding a model in a larger Java
program (see the standalone-java reference). Needs only the Java you write.

## 3. OptQuest, licensing, and edition limits

- **Optimization and Calibration rely on OptQuest**, the metaheuristic optimizer
  bundled with AnyLogic. Availability and scale can depend on edition.
- **Authoring and standalone-Java export require AnyLogic Professional.** **PLE**
  (Personal Learning Edition) and **University Researcher** cannot export
  standalone applications (prohibited by their license agreements) and have other
  limits. Confirm the edition before planning an external-execution workflow.
- Large/long experiments may need elevated *Maximum available memory* and benefit
  from running in fast/virtual time without animation.

## 4. Choosing the right experiment

- Watch one run / debug → **Simulation**
- Sweep parameters or run replications → **Parameter Variation**
- Find best parameters → **Optimization**
- Fit parameters to data → **Calibration**
- Characterize an output distribution under uncertainty → **Monte Carlo**
- See which inputs matter → **Sensitivity Analysis**
- Human-in-the-loop what-if comparison → **Compare Runs**
- Train/connect an RL policy, or drive step-by-step externally → **Reinforcement Learning**
- Anything custom, scripted, or embedded in other Java → **Custom Experiment**

Note the division of labor: AnyLogic experiments *run* the model many ways, but
the statistics of trustworthy conclusions (how many replications for a target
confidence interval, warmup removal for steady-state metrics, comparing
alternatives correctly) are general simulation methodology — apply that on top of
Parameter Variation / Monte Carlo output. Collect results via **Output** elements
and datasets so they're exposed to the experiment and to any external runner.

## 5. Common run-time gotchas

- Results won't reproduce → randomness set to *Random seed*; switch to *Fixed
  seed* (and be aware multithreaded parallelism can still affect ordering).
- Results never change when they should → *Fixed seed* with the same value every
  run.
- `OutOfMemoryError` → raise *Maximum available memory* in the experiment's
  Advanced properties.
- Optimization "converges" to noise → too few replications per iteration on a
  stochastic model; increase them so OptQuest sees the mean.
- Export option greyed out / disallowed → not running Professional.
