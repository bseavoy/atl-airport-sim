# Custom Skills Manifest

A collection of specialized skills for airport operations, simulation, aviation analytics, and government air traffic management.

**Location:** `/Users/ben_bot/.openclaw/workspace/custom-skills/`

**Source:** Uploaded from NAS Transfer Folder (2026-06-28)

## Available Skills

### 1. Simulation Expert (`simulation-expert.skill`)
**Size:** 18 KB  
**Purpose:** Expert simulation engineer and analyst for discrete-event, agent-based, system-dynamics, Monte Carlo, and continuous simulations.

**Triggers:**
- Designing, building, debugging, validating simulations or stochastic models
- Verification & validation (V&V) work
- Statistical output analysis
- Input distribution fitting
- Model verification and validation
- Warmup/transient removal
- Confidence intervals and replications
- Variance reduction techniques
- Sensitivity analysis and design of experiments
- Surrogate/metamodels and simulation optimization
- "Model this system", "estimate wait time/throughput", "run what-if"

**References included:**
- `paradigms.md` — DES, ABM, system dynamics, Monte Carlo, continuous simulations
- `verification-validation.md` — V&V toolbox and techniques
- `output-analysis.md` — Statistical playbook for simulation output

### 2. Airline Crew Analytics Expert (`airline-crew-analytics-expert.skill`)
**Size:** 13 KB  
**Purpose:** Expert in crew scheduling, duty regulations, fatigue management, and airline crew analytics.

**Supports:**
- Crew pairing optimization
- Duty time calculations (FARs, EASA regulations)
- Fatigue risk assessment
- Crew scheduling simulations
- Regulatory compliance (CIGO, FAA, EASA)
- Crew cost analysis

**Reference document:** `crew-analytics.md`

### 3. Airline Crew Analytics Expert — Additional (`crew-analytics.md`)
Supporting reference with crew analytics methodology and frameworks.

### 4. Airport Ground Ops Expert (`airport-ground-ops-expert.skill`)
**Size:** 8.4 KB  
**Purpose:** Deep expertise in airport ground operations, gate management, taxiway congestion, and runway sequencing.

**Covers:**
- Gate assignment and management
- Taxi-out/taxi-in modeling
- Runway separation and sequencing
- Departure metering
- Congestion analysis
- Ground delay programs (GDP)
- Metrics (A0, D0, taxi times, utilization)

**Reference documents:**
- `metrics-and-analytics.md` — Performance metrics
- `turn-and-ramp.md` — Turnaround and ramp operations

### 5. ATL Operations Expert (`atl-operations-expert.skill`)
**Size:** 8.9 KB  
**Purpose:** Specialized knowledge of Hartsfield-Jackson Atlanta International Airport (ATL) operations.

**Includes:**
- ATL-specific capacity and constraints
- Gate management at ATL
- Runway configuration and separation rules
- Hub operations (Delta hub)
- Network propagation effects
- ATL calibration and validation approaches

**Reference document:** `delta-hub-and-analytics.md`

### 6. AnyLogic Expert (`anylogic-expert.skill`)
**Size:** 13 KB  
**Purpose:** Deep expertise in AnyLogic simulation modeling, both desktop and cloud-based.

**Covers:**
- Discrete-event simulation in AnyLogic
- Agent-based modeling in AnyLogic
- System dynamics in AnyLogic
- Model creation and calibration
- Experimentation and optimization
- Integration with external data
- Java scripting in AnyLogic

**Reference document:** `standalone-java.md` — Java scripting and customization

### 7. US ATM Government Expert (`us-atm-government-expert.skill`)
**Size:** 9.4 KB  
**Purpose:** Expert in US Air Traffic Management operations, FAA regulations, and government ATM systems.

**Covers:**
- FAA regulations and procedures
- CPDLC and next-gen technologies
- Traffic flow management (TFM)
- Ground delay programs (GDP) and ground stops
- Capacity and demand management
- Government ATM planning and forecasting

**Reference documents:**
- `tfm-toolbox.md` — Traffic Flow Management tools
- `delta-pwa-pilot-rules.md` — Pilot procedures and PWA rules

## Supporting Documentation

### Core References
- **`SKILL.md`** — Overview of all skills and frameworks
- **`paradigms.md`** — Simulation paradigm selection guide (DES, ABM, SD, MC)
- **`output-analysis.md`** — Statistical analysis of simulation output
- **`verification-validation.md`** — Model V&V methodology
- **`model-structure.md`** — Conceptual model design

### Domain-Specific
- **`airport-layout-and-airspace.md`** — Airport infrastructure and airspace constraints
- **`crew-analytics.md`** — Airline crew optimization and fatigue
- **`delta-hub-and-analytics.md`** — Delta Air Lines hub operations
- **`delta-pwa-pilot-rules.md`** — Delta pilot procedures (PWA)
- **`flight-attendant-rules.md`** — Flight attendant regulations and duty rules
- **`metrics-and-analytics.md`** — Performance metrics (A0, D0, throughput, utilization)
- **`experiments.md`** — Experimental design and analysis
- **`turn-and-ramp.md`** — Ground turnaround and ramp operations
- **`tfm-toolbox.md`** — Traffic Flow Management tools and techniques
- **`standalone-java.md`** — AnyLogic Java scripting reference

## How to Use These Skills

### Option 1: Direct Skill Invocation (When Implemented)
When the skill system is fully integrated:
```
/simulation-expert — for simulation methodology and design
/airport-ground-ops-expert — for airport operations questions
/atl-operations-expert — for ATL-specific operations
/airline-crew-analytics-expert — for crew scheduling and fatigue
/anylogic-expert — for AnyLogic modeling questions
/us-atm-government-expert — for FAA/government ATM questions
```

### Option 2: Reference Documents
Use the supporting `.md` files for methodology and reference:
- Need simulation paradigm guidance? → Read `paradigms.md`
- Need statistical analysis methods? → Read `output-analysis.md`
- Need to verify a model? → Read `verification-validation.md`
- Need airport operations metrics? → Read `metrics-and-analytics.md`

### Option 3: Project Integration
Copy this folder into your project and reference:
- When building airport simulation models
- When designing airline crew scheduling systems
- When analyzing ground operations
- When working with AnyLogic
- When interfacing with FAA/ATM systems

## Quick Reference: Which Skill for Which Task?

| Task | Skill to Use |
|------|-------------|
| Build/debug a simulation model | **simulation-expert** |
| Design crew scheduling system | **airline-crew-analytics-expert** |
| Model gate operations, taxi times | **airport-ground-ops-expert** |
| ATL-specific operations questions | **atl-operations-expert** |
| AnyLogic modeling or scripting | **anylogic-expert** |
| FAA regulations, government ATM | **us-atm-government-expert** |
| Need methodology docs | See **Supporting Documentation** |

## Installation & Integration

### Current Status
✅ Skills copied to workspace: `/Users/ben_bot/.openclaw/workspace/custom-skills/`

### Next Steps
1. **For OpenClaw/Claude Code integration:** Register these skills in the skill system (may require skill_workshop registration)
2. **For project use:** Copy the entire `custom-skills/` folder into your project root or reference it
3. **For AI assistance:** Mention the relevant skill name in your query (e.g., "As a simulation-expert, help me validate this model")

## Metadata

- **Created:** 2026-06-28
- **Source:** Custom skills uploaded to NAS Transfer Folder
- **Version:** 1.0
- **Format:** .skill files (packaged), .md documentation
- **Coverage:** Airport operations, simulation, aviation, government ATM

---

**Note:** These skills are specialized decision-support tools. Use them in concert with official documentation, regulations (FAA, EASA), and domain expert review for production systems.
