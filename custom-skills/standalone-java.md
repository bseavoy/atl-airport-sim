# Standalone Java Export & Running Outside AnyLogic

How AnyLogic exports a model to a standalone Java application, what the exported
project contains, and every way to run it outside the IDE — GUI, headless,
command line, embedded in another Java program, or driven from Python.

> Requires **AnyLogic Professional**. PLE and University Researcher cannot export
> standalone applications. Exported apps run on **JDK 17 or higher**; no AnyLogic
> installation is needed on the target machine.

## Contents
1. How to export
2. Structure of an exported project
3. Running an exported model (GUI and headless)
4. Command-line use
5. Embedding a model in another Java program (Engine API)
6. Driving a model from Python
7. Practical notes and gotchas

---

## 1. How to export

In the IDE: select the model's top item in the **Projects** view →
**Export ▸ To standalone Java application**. In the wizard, pick the
**experiment to export**, a **destination folder**, an optional UI **language**,
and — if the app will run on other operating systems — download the bundled
**Chromium** pack so animation displays cross-platform. Finish.

The chosen experiment determines the app's entry point and default settings.
Export is also scriptable from the command line (see §4) for build pipelines.

## 2. Structure of an exported project

The destination folder contains:

- **`<model name>_windows.bat`** — Windows launcher.
- **`<model name>_mac`** — macOS launcher.
- **`<model name>_linux.sh`** — Linux launcher.
- **`model.jar`** — the compiled model (your agents, `Main`, and the generated
  experiment class).
- **`lib/`** — libraries the model needs, including the AnyLogic engine
  (`com.anylogic.engine.jar`), the database driver, and so on.
- *(optional)* additional **dependency JARs/classes** the model was built against
  (custom libraries, external jars listed in the model's dependencies).
- *(optional)* **`chromium/`** — portable Chromium browsers used to display the
  model animation on Windows/Linux/macOS.
- **`AnyLogic Model User Agreement.pdf`**, **`license.txt`** — the model user
  agreement.
- **`readme.txt`** — brief run instructions.

Mental model: it's an ordinary Java app — `model.jar` plus the jars in `lib/` on
the classpath, launched at a generated main class. The launcher scripts just
assemble that `java` command for each OS.

## 3. Running an exported model (GUI and headless)

**With the model window (default).** Run the OS-specific launcher
(`<model>_windows.bat`, `<model>_linux.sh`, or the macOS file). The model is
executed by the **AnyLogic Engine Runtime** — effectively a small local server
that serves the animation to a browser view on a local port, plus the model
window UI.

**Headless / fast mode (no animation).** For servers, batch runs, and
integration, you run the model without creating the model window, which also runs
it at full speed. There are two routes:

- Make the export entry point a **Custom Experiment** (or RL experiment) whose
  Java runs the engine in fast mode and writes outputs to file/stdout/DB — then
  the launcher runs headless by construction.
- Or embed the model in your own Java program and call the engine's fast-run
  methods (see §5), skipping presentation entirely.

Headless is the right mode for cloud/CI execution and for large replication or
optimization batches where animation is pure overhead.

## 4. Command-line use

The launcher scripts are normal shell/batch scripts, so they run from a terminal
and accept arguments:

```bash
cd "/path/to/Exported models/Call Center"
./Call\ Center_linux.sh arg1 arg2          # Linux
# Call Center_windows.bat arg1 arg2        # Windows
```

Arguments after the script name are passed to the model (read them in the
experiment's startup code). You can also hard-code argument values directly in
the launcher script, placed after the enumeration of the JAR files in the `java`
command.

AnyLogic also supports, from the command line: **exporting** a model to a
standalone app, **opening** a model, and **running a specific experiment** — see
the "Exporting models to Java application" page on `anylogic.help` for the exact
flags, which are useful in automated build/run pipelines.

Changing the entry point: the launcher invokes a generated main class named after
the exported experiment (e.g. `Simulation`). To launch a different experiment
class instead — for example a custom class `MyApplication` — edit the class name
in the `.bat`/`.sh`/`.cmd` accordingly. This is the documented way to point the
exported app at custom launcher logic.

## 5. Embedding a model in another Java program (Engine API)

Because the model is Java, you can call it from your own application: export the
model (conveniently, straight into your Java project's folder), then add
`model.jar` and every jar in `lib/` (especially `com.anylogic.engine.jar`) to
your project's **classpath**. Then drive it through the **Engine API**.

The reliable shape of a headless run (confirm exact signatures against the Engine
API reference and the generated classes in your `model.jar`, since they evolve by
version):

```java
// 1. Create the experiment / engine and the model root (top-level agent Main).
// 2. Set parameters on the root and configure the engine (stop time, seed).
// 3. Run in fast mode (no UI), then read Output elements / fields off the root.
// 4. Stop the engine and repeat for the next replication/parameter set.
```

Two integration modes are documented as how-to models (search "Launching AnyLogic
Model from External Application" on `anylogic.help` / AnyLogic Cloud): one that
shows the model window from the external app, and one that runs the model in fast
mode without a window. Reuse that how-to's code for current, exact API calls
rather than hand-writing signatures.

This is the path for: running many replications in a JVM loop, wiring the model
into a decision-support system or REST service, or controlling it from a larger
optimization harness.

## 6. Driving a model from Python

The user codes primarily in Python; the export itself is unavoidably Java, but
several bridges let Python control or consume AnyLogic models:

- **AnyLogic Cloud Python API** — upload the model to AnyLogic Cloud (public or
  Private Cloud), then start runs, set inputs, and pull outputs from Python via
  the official client. Best when a Cloud deployment is acceptable and you want
  clean programmatic runs without managing the JVM yourself. (See the Cloud
  Python API docs on `anylogic.help`.)
- **RL experiment export** — the Reinforcement Learning experiment exports the
  model as a training environment with an observation/action/reward interface,
  which Python RL tooling can step. Use this for step-by-step interactive control
  (learning or closed-loop testing), not just batch runs.
- **`alpyne`** — a community (third-party) Python library that wraps an exported
  AnyLogic model so Python can run it and exchange data, building on the RL-style
  interface. Useful and popular, but not officially supported — pin versions and
  validate behavior, and prefer the Cloud API or RL export when official support
  matters.
- **Pypeline** — runs Python *inside* an AnyLogic model (the inverse direction);
  relevant if you want the model to call Python (e.g. a trained model or a
  data-science function) during simulation, rather than Python driving the model.

Pick by direction and deployment: Python orchestrating runs → Cloud Python API or
`alpyne`; Python stepping an environment → RL export; model calling Python →
Pypeline.

## 7. Practical notes and gotchas

- **"`java` is not recognized" / nothing happens on launch** → JDK 17+ isn't
  installed or isn't on PATH on the target machine. Exported apps need Java; they
  do not need AnyLogic.
- **Carry all dependencies** → custom libraries and external jars must be present
  in the export (they ship as model dependencies); a missing dependency jar
  breaks the classpath.
- **Memory** → set *Maximum available memory* in the experiment's Advanced
  properties *before* exporting a large or DB-backed model; the launcher's `-Xmx`
  follows from it.
- **Database** → the database log isn't exported; built-in DB data is compacted on
  export. Allocate enough memory for both the model and the DB server if the model
  uses the built-in database.
- **Animation on other OSes** → include the Chromium pack at export time if the
  app must show animation on a different operating system than it was exported on.
- **Reproducibility across machines** → fix the seed in the experiment; be aware
  that parallel/multithreaded execution can still reorder events even with a fixed
  seed.
- **Version sensitivity** → exact file names, generated class names, and Engine
  API signatures can change between AnyLogic releases. Verify against the exported
  `model.jar`, the launcher scripts, and the live docs at `anylogic.help` rather
  than assuming.
