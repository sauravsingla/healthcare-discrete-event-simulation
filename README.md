# Healthcare Discrete-Event Simulation

[![CI](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml/badge.svg)](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Coverage](https://img.shields.io/badge/coverage-gate%20%E2%89%A580%25-brightgreen)](#testing-and-quality)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.4236%2Fojmsi.2020.84007-blue)](https://doi.org/10.4236/ojmsi.2020.84007)
[![Docker](https://img.shields.io/badge/Docker-verified-2496ED?logo=docker&logoColor=white)](#dashboard-and-docker)
[![Research](https://img.shields.io/badge/research-reproducible-6f42c1)](#research-contributions)

A research-grade Python healthcare digital twin for MRI demand forecasting, capacity planning, patient-flow simulation, queue analysis, resource utilisation, uncertainty analysis and transparent staffing optimisation.

This repository implements and extends Saurav Singla (2020), **Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation**, *Open Journal of Modelling and Simulation*, 8, 88–107.

- [Research paper](https://www.scirp.org/journal/paperinformation?paperid=102869)
- [DOI](https://doi.org/10.4236/ojmsi.2020.84007)
- [Validation protocol](docs/VALIDATION.md)
- [Engine guide](docs/ENGINE_GUIDE.md)
- [Validation status](docs/VALIDATION_STATUS.md)
- [Roadmap](docs/ROADMAP.md)

<p align="center">
  <img src="docs/assets/dashboard-preview.svg" alt="Healthcare demand and capacity dashboard preview" width="920">
</p>

## Why this project matters

Healthcare capacity decisions involve uncertain demand, patient priorities, shared resources, equipment downtime and queues that interact over time. This project converts those operational relationships into a reproducible discrete-event simulation so that alternative demand, machine, staffing and scheduling scenarios can be compared transparently before real-world implementation.

The repository is designed as both a research implementation and an auditable decision-support framework. It separates assumptions, simulation logic, generated evidence and validation status so that results can be challenged, reproduced and extended.

## At a glance

| Area | Capability |
|---|---|
| Demand | Outpatient, inpatient and 24-hour emergency arrivals |
| Patient flow | Reception, preparation, MRI scanning and reporting |
| Operational behaviour | Priorities, queues, cancellation, no-show, abandonment and unfinished patients |
| Capacity | MRI machines, radiographers, radiologists, clerks and dynamic staffing windows |
| Reliability | Maintenance, stochastic failure, repair and optional scan restart |
| Experimentation | Replications, bootstrap summaries, sensitivity analysis and scenario benchmarking |
| Public evidence | NHS aggregate-data preparation, provenance and benchmark workflows |
| Delivery | Python package, four CLI entry points, Streamlit dashboard and Docker image |
| Quality | Linting, typing, coverage gate, wheel validation, Docker health checks and multi-version CI |

## Project statistics

| Measure | Current implementation |
|---|---|
| Supported Python versions | 3.10, 3.11 and 3.12 |
| Installed CLI applications | 4 |
| Benchmark design | 18 scenarios and 36 measured runs |
| Benchmark demand levels | 35, 70 and 140 patients per day |
| Benchmark MRI capacities | 1, 2, 4, 8, 12 and 20 machines |
| Coverage requirement | Minimum 80% |
| Delivery targets | Python package, dashboard and Docker image |
| Automated verification | Unit, integration, CLI, package, benchmark and container checks |

## Quick start

```bash
git clone https://github.com/sauravsingla/healthcare-discrete-event-simulation.git
cd healthcare-discrete-event-simulation
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev,dashboard]"
healthcare-des --config configs/baseline.yaml --replications 20
```

Launch the dashboard:

```bash
streamlit run app.py
```

## Research contributions

Relative to a basic patient-flow simulation, this repository adds:

- a richer patient lifecycle with cancellation, no-show, abandonment and unfinished-patient accounting;
- outpatient, inpatient and emergency pathways sharing constrained MRI capacity;
- calendar-aware and hourly demand profiles;
- dynamic staffing and operating windows;
- planned maintenance, stochastic MRI failure, repair and optional scan restart;
- configurable horizon, bounded-drain and full-drain termination policies;
- deterministic replications, bootstrap uncertainty and sensitivity analysis;
- capacity-search and transparent optimisation utilities;
- run-level patient ledgers and system-state observations;
- reproducible performance benchmarking across demand and capacity levels;
- public NHS aggregate-data preparation and evidence provenance workflows;
- package, CLI, dashboard, Docker and continuous-integration delivery.

## System architecture

```mermaid
flowchart LR
    subgraph Inputs[Scenario and evidence inputs]
        A[Demand profiles]
        B[Patient mix and priorities]
        C[Capacity and staffing]
        D[Maintenance and failures]
        E[Public aggregate evidence]
    end

    subgraph Engine[Discrete-event simulation engine]
        F[Arrival and appointment generation]
        G[Event scheduler]
        H[Priority queues]
        I[Resource dispatch]
        J[Lifecycle and termination control]
    end

    subgraph Resources[Healthcare resources]
        K[Clerks]
        L[Radiographers]
        M[MRI machines]
        N[Radiologists]
    end

    subgraph Evidence[Evidence and decision layer]
        O[Patient outcome ledger]
        P[State observations]
        Q[KPI and uncertainty summaries]
        R[Scenario benchmark]
        S[Capacity search]
        T[Streamlit dashboard]
    end

    A --> F
    B --> F
    C --> I
    D --> I
    E --> Q
    F --> G --> H --> I --> J
    I <--> K
    I <--> L
    I <--> M
    I <--> N
    J --> O
    J --> P
    O --> Q
    P --> Q
    Q --> R
    Q --> S
    Q --> T
```

## Patient-flow model

```mermaid
flowchart LR
    A[Booked outpatient] --> B{Advance cancellation?}
    B -->|Yes| C[Cancelled]
    B -->|No| D{No-show?}
    D -->|Yes| E[No-show]
    D -->|No| F[Actual arrival]
    G[Inpatient arrival] --> F
    H[Emergency arrival] --> F
    F --> I[Reception]
    I --> J[Preparation]
    J --> K[Shared MRI dispatch]
    K --> L[Reporting]
    L --> M[Completed]
    I -. patience exhausted .-> N[Abandoned]
    J -. patience exhausted .-> N
    K -. patience exhausted .-> N
    L -. termination .-> O[Unfinished]
```

`wait_minutes` is the sum of stage queue waits. `system_minutes` includes waiting and service time. Cancellation and no-show are recorded separately from patients who enter the physical service system.

## Example decision outputs

A typical experiment produces:

- mean and stage-specific waiting time;
- mean system time;
- throughput per day;
- completion rate and service-level attainment;
- patient-type performance for outpatient, inpatient and emergency pathways;
- clerk, radiographer, MRI and radiologist utilisation;
- cancellation, no-show, abandonment and unfinished-patient counts;
- replication-level uncertainty and 95% confidence intervals;
- ranked capacity and staffing alternatives.

Generate deterministic machine-readable examples with:

```bash
python examples/generate_example_outputs.py
```

The command writes:

```text
outputs/example_replications.csv
outputs/example_summary.csv
outputs/example_capacity_candidates.csv
```

## Reproducible benchmark results

The documentation benchmark exercises the advanced engine across **18 demand-capacity scenarios** and **36 measured simulation runs**.

| Benchmark dimension | Values |
|---|---|
| Measurement horizon | 2 simulated days per run |
| Replications | 2 per scenario |
| Daily demand | 35, 70 and 140 patients |
| MRI capacity | 1, 2, 4, 8, 12 and 20 machines |
| Scenario combinations | 18 |
| Total measured runs | 36 |
| Random seed | 17, with deterministic replication offsets |
| Bootstrap samples | 100 per run |

| Verification item | Status |
|---|---|
| All demand-capacity combinations executed | ✅ |
| Two deterministic replications per scenario | ✅ |
| Runtime and output volume recorded | ✅ |
| Lifecycle reconciliation checked | ✅ |
| Expected benchmark files validated in CI | ✅ |

Every scenario preserves:

```text
arrivals = completed + abandoned + unfinished
```

<p align="center">
  <img src="docs/assets/generated/benchmark_matrix.svg" alt="Advanced-engine benchmark scenario matrix" width="820">
</p>

<p align="center">
  <img src="docs/assets/generated/benchmark_workflow.svg" alt="Reproducible benchmark workflow" width="820">
</p>

<p align="center">
  <img src="docs/assets/generated/benchmark_outputs.svg" alt="Benchmark outputs and validation checks" width="820">
</p>

Reproduce the documentation benchmark with:

```bash
python scripts/generate_readme_assets.py
```

The complete run-level results are written to:

```text
outputs/readme_advanced_benchmark.csv
```

For a configurable benchmark:

```bash
healthcare-des-advanced-benchmark \
  --days 7 \
  --replications 3 \
  --output outputs/advanced_benchmark.csv
```

> **Interpretation note:** elapsed time depends on the processor, operating system, Python environment and concurrent workload. The benchmark demonstrates reproducible scaling behaviour and output growth; it does not claim universal execution speed or clinical effectiveness.

## Which engine should I use?

| Engine | Intended use | Status |
|---|---|---|
| Base engine | Original YAML-driven workflow, standard scenario comparison and dashboard | Maintained for compatibility and straightforward experiments |
| Advanced engine | Rich lifecycle accounting, hourly demand, dynamic staffing, downtime, appointment schedules and configurable draining | Recommended for new research extensions |

See [docs/ENGINE_GUIDE.md](docs/ENGINE_GUIDE.md) for detailed distinctions and migration guidance.

## Advanced engine example

```python
from dataclasses import replace
from healthcare_des import AdvancedScenarioConfig, run_advanced_once

config = replace(
    AdvancedScenarioConfig(),
    name="advanced-example",
    days=14,
    warmup_days=2,
    daily_demand=70,
    mri_machines=4,
    termination_policy="bounded_drain",
    max_drain_minutes=720,
    seed=17,
)

result, patients, state = run_advanced_once(config)
print(result)
print(patients["status"].value_counts())
assert result.arrivals == result.completed + result.abandoned + result.unfinished
```

A complete example is available in [`examples/advanced_workflow.py`](examples/advanced_workflow.py).

## Termination policies

- `horizon`: stop at the measurement horizon and report unfinished patients.
- `bounded_drain`: stop arrivals and allow up to `max_drain_minutes` for completion.
- `drain`: stop arrivals and continue while active patients remain.

Use the same policy across scenarios unless termination is itself the experimental factor.

## Repository structure

```text
.
├── src/healthcare_des/      # Simulation engines, experiments and analysis
├── tests/                   # Unit, integration and regression tests
├── examples/                # Reproducible usage examples
├── configs/                 # YAML scenario configurations
├── data/                    # Templates and non-sensitive aggregate inputs
├── docs/                    # Validation, engine and roadmap documentation
├── scripts/                 # Benchmarking and public-data preparation workflows
├── outputs/                 # Generated machine-readable results
├── app.py                   # Streamlit dashboard entry point
├── pyproject.toml           # Package metadata, dependencies and CLI definitions
└── Dockerfile               # Reproducible container deployment
```

## Command-line applications

```bash
healthcare-des --help
healthcare-des-benchmark --help
healthcare-des-reproduce --help
healthcare-des-advanced-benchmark --help
```

Standard scenario run:

```bash
healthcare-des --config configs/baseline.yaml --replications 20
```

Multi-scenario benchmark:

```bash
healthcare-des-benchmark \
  --config configs/baseline.yaml \
  --replications 20 \
  --output outputs/benchmark.csv
```

## KPI definitions

- **Booked:** outpatient appointments created before cancellation and no-show resolution.
- **Cancelled:** appointments cancelled before the scheduled arrival.
- **Expected arrivals:** booked appointments remaining after advance cancellation.
- **No-shows:** expected outpatients who do not enter the service system.
- **Arrivals:** patients who enter the simulated service system.
- **Completed:** arrivals finishing all stages.
- **Abandoned:** arrivals leaving before completion after exhausting patience.
- **Unfinished:** arrivals still active when the selected termination policy ends.
- **Completion rate:** completed divided by actual arrivals.
- **Stage waits:** queue delay before reception, preparation, MRI and reporting.
- **Total wait:** sum of stage-specific queue waits.
- **System time:** elapsed time from actual arrival to final outcome.
- **Operational measures:** state observations restricted to configured opening hours.
- **24-hour measures:** all state observations in the measured period.

## Verification and validation status

| Area | Current status |
|---|---|
| Software verification | Deterministic tests, accounting checks and CI implemented |
| Multi-version compatibility | Tested on Python 3.10, 3.11 and 3.12 |
| Package and CLI verification | Wheel build, clean installation and CLI smoke tests implemented |
| Dashboard deployment verification | Docker build and Streamlit health endpoint tested in CI |
| Repeated-experiment reproducibility | Fixed-seed and replication checks implemented |
| Public aggregate-data workflow | Preparation, provenance and benchmark utilities implemented |
| Independent observational validation | Protocol available; requires authoritative external observations |
| Exact 2020-paper reproduction | Not claimed while authoritative targets remain incomplete |
| Clinical deployment validation | Must be completed locally before operational use |

The public-data workflow uses aggregate external data and stores no patient-level confidential or employer-owned information. Blank expected values in `data/paper_targets_template.csv` deliberately indicate that authoritative published targets have not yet been transcribed and must not be replaced with guessed values.

See [`docs/VALIDATION.md`](docs/VALIDATION.md) and [`docs/VALIDATION_STATUS.md`](docs/VALIDATION_STATUS.md) for holdout validation, statistical equivalence, warm-up handling and reproduction decision rules.

## Capacity optimisation

```python
from healthcare_des.model import ScenarioConfig
from healthcare_des.optimisation import search_capacity

candidates = search_capacity(
    ScenarioConfig(days=14, warmup_days=2, daily_demand=70),
    replications=8,
)
print(candidates.head())
```

The optimiser uses illustrative weights. Replace them with locally validated cost, safety and workforce assumptions before operational use.

## Monte Carlo and sensitivity analysis

```python
from healthcare_des.model import ScenarioConfig
from healthcare_des.sensitivity import monte_carlo, one_at_a_time

base = ScenarioConfig(days=14, warmup_days=2)
uncertainty = monte_carlo(base, samples=50, replications=4)
sensitivity = one_at_a_time(base, replications=10)
```

## Dashboard and Docker

```bash
streamlit run app.py
```

```bash
docker build -t healthcare-des .
docker run --rm -p 8501:8501 healthcare-des
```

The dashboard exposes scenario controls, KPI cards, confidence intervals, replication uncertainty, resource utilisation, patient-type performance, scenario comparison and capacity search.

## Testing and quality

```bash
pre-commit run --all-files
ruff check src tests scripts examples
mypy src/healthcare_des
pytest --cov=healthcare_des --cov-report=term-missing --cov-fail-under=80
python -m build
twine check dist/*
```

CI runs quality checks on Python 3.10, 3.11 and 3.12. It exercises installed CLI entry points, validates advanced-engine accounting, runs a bounded benchmark with output assertions, builds and installs the wheel in a clean environment, builds the Docker image, starts the container and verifies the Streamlit health endpoint.

A separate tag-triggered release workflow builds and validates source and wheel distributions. It deliberately does not publish to a package index without repository secrets and an explicit release decision.

## Roadmap

The detailed roadmap is maintained in [`docs/ROADMAP.md`](docs/ROADMAP.md). Priority directions include:

- stronger calibration against authoritative public and local operational evidence;
- multi-site and multi-modality healthcare simulation;
- FHIR-compatible integration interfaces;
- expanded cost, workforce and service-level optimisation;
- comparative scheduling policies and learning-based decision support;
- optional acceleration for large scenario portfolios;
- versioned releases and independently reproducible benchmark artefacts.

## Assumptions and limitations

The project focuses on MRI patient flow rather than the entire radiology service. The advanced engine supports hourly demand, appointment schedules, downtime, cancellations, abandonment and dynamic staffing, but default values remain illustrative until calibrated against authoritative local evidence.

Exact reproduction of the 2020 paper is not claimed while published scenario targets remain blank or incompletely transcribed. Real-world use additionally requires independent validation of clinical pathways, workforce rules, costs, safety constraints and governance requirements.

The model is a research and decision-support framework. It is not a clinical recommendation or a production scheduling system.

## Citation

```bibtex
@article{singla2020demand,
  title={Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation},
  author={Singla, Saurav},
  journal={Open Journal of Modelling and Simulation},
  volume={8},
  pages={88--107},
  year={2020},
  doi={10.4236/ojmsi.2020.84007}
}
```

## Author

**Saurav Singla**

- [LinkedIn](https://www.linkedin.com/in/sauravsingla008/)
- [ORCID](https://orcid.org/0000-0002-6404-3988)
