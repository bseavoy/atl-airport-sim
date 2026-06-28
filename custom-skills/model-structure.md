# AnyLogic Model Structure

How an AnyLogic model is organized internally, so you can read, build, and reason
about one — and understand what gets generated into Java on export.

## Contents
1. The model file and project tree
2. Agents and the top-level `Main`
3. The three modeling methods and their building blocks
4. Libraries
5. Data, parameters, variables, and statistics
6. How the model maps to Java
7. Reading an unfamiliar model

---

## 1. The model file and project tree

An AnyLogic model is stored as an `.alp` file (an XML "AnyLogic Project"
describing the model graphically and the Java snippets inside it). Supporting
items (custom Java classes, external jars, 3D objects, databases, resource files)
live alongside it. In the **Projects** view the tree's top item is the model
itself; under it sit **agent types**, **experiments**, and model-level resources.

Everything graphical in the model is ultimately translated to Java and compiled
against the AnyLogic engine — the `.alp` is the source of truth, and the
generated Java is what actually runs.

## 2. Agents and the top-level `Main`

**Agents** are the universal building block (older models call them "active
objects"). An agent type is a class: it has structure (parameters, variables,
functions, statecharts, embedded flowcharts, populations of other agents,
presentation/animation) and behavior. Agents can be nested arbitrarily, giving
the model its hierarchy.

By convention the **top-level agent is named `Main`**. It's the root of the model
that an experiment instantiates and runs. `Main` typically holds the process
flowcharts, the populations of agents, the system-dynamics diagrams, and the
top-level animation. When you run a Simulation experiment, AnyLogic creates an
engine, creates a `Main` root, and starts it.

Populations: an agent type can be instantiated as a **population** (e.g. 10,000
`Customer` agents), which is how agent-based scale is expressed. Agents live in
an **environment/space** that may be continuous, discrete (grid), GIS, or a
network, and may move within it.

## 3. The three modeling methods and their building blocks

AnyLogic is *multimethod*: a single model can mix all three. Choose per the
driver of your question (and see a general simulation-paradigm reference for the
underlying trade-offs).

**Discrete-event / process modeling.** Built with the **Process Modeling Library
(PML)**: entities (agents) flow through a flowchart of blocks — `Source`,
`Queue`, `Delay`, `Seize`/`Release`, `Service`, `SelectOutput`, `Sink`, etc. —
competing for `ResourcePool` resources. This is the queueing/operations workhorse
(manufacturing, logistics, healthcare, call centers). Specialized libraries
extend it: **Material Handling**, **Pedestrian**, **Rail**, **Road Traffic**,
**Fluid**.

**Agent-based.** Agents with their own state and behavior, usually driven by
**statecharts** (states + transitions triggered by timeouts, conditions,
messages, or rates) and **events**. Behavior emerges from interaction across a
population in space or over a network. Use for epidemics, markets, social
dynamics, fleets.

**System dynamics.** Aggregate **stocks** (accumulations), **flows** (rates), and
**dynamic variables** connected by **links** into feedback loops — a continuous
ODE-based view. Use for policy/macro questions with feedback and delays. AnyLogic
integrates these equations with its numerical solvers and can couple them to the
other two methods.

Supporting behavioral elements shared across methods: **events** (one-shot or
recurrent, timeout/rate/condition triggered), **dynamic events**, **statecharts**,
and **functions** (Java methods on the agent).

## 4. Libraries

Libraries supply ready-made blocks. The **Process Modeling Library** is the core
DES toolkit; **Material Handling**, **Pedestrian**, **Rail**, **Road Traffic**,
and **Fluid** libraries add domain blocks and space markup. Users can also build
**custom libraries**. On export, any library and external `.jar` the model
depends on is carried along as a model dependency (this matters for the exported
classpath — see the standalone-java reference).

## 5. Data, parameters, variables, and statistics

- **Parameters** configure an agent and are typically set before/at
  instantiation (and exposed by experiments for variation/optimization). Use
  parameters for "knobs" that don't change moment-to-moment.
- **Variables** hold changing state during a run.
- **Collections**, **datasets**, **statistics**, **histograms**, and **Output**
  elements collect and summarize results. **Output** elements are what experiments
  read as objective/response values.
- **Schedules**, **table functions**, and the built-in or external **databases**
  feed data in.
- Animation/charts (time plots, bar/pie/stack charts) visualize state at runtime;
  they're presentation only and are skipped when running headless.

## 6. How the model maps to Java

A model is fully generated into Java: each agent type becomes a class; the
top-level is the `Main` class; each experiment becomes a class named after it.
Graphical logic (flowchart blocks, statechart states/transitions, SD equations)
and the small Java snippets the modeler types into element properties are woven
into these classes, then compiled against the **AnyLogic engine**
(`com.anylogic.engine.jar`). This is why an exported model is a self-contained
Java application and why model elements are reachable from code (e.g. from a
Custom Experiment or external Java) as fields and methods on `Main`. For exact
generated names and API, inspect the exported `model.jar` or the AnyLogic class
reference rather than guessing.

## 7. Reading an unfamiliar model

1. Open the **experiments** first — the experiment tells you the entry point, the
   top-level agent, the stop condition, and which parameters/outputs matter.
2. Open **`Main`** — see which methods are in play (flowcharts? populations?
   stock-and-flow diagrams?) and how they connect.
3. Trace the **data in** (Source rates, parameters, schedules, DB) and the
   **data out** (Output elements, datasets, statistics) — these define inputs and
   KPIs.
4. Note the **Randomness** setting and **stop time/condition** — they govern
   reproducibility and what one run even represents.
5. Check **model dependencies** (custom jars/libraries) — they must travel with
   any export.
