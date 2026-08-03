# Healthcare Discrete-Event Simulation

[![CI](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml/badge.svg)](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Coverage](https://img.shields.io/badge/whole--package%20coverage-gate%20%E2%89%A580%25-brightgreen)](#testing-and-quality)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.4236%2Fojmsi.2020.84007-blue)](https://doi.org/10.4236/ojmsi.2020.84007)
[![Docker](https://img.shields.io/badge/Docker-verified-2496ED?logo=docker&logoColor=white)](#dashboard-and-docker)

A reproducible Python platform for MRI demand forecasting, capacity planning, patient-flow simulation, queue analysis, resource utilisation and uncertainty analysis.

This repository modernises and extends Saurav Singla (2020), **Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation**, *Open Journal of Modelling and Simulation*, 8, 88–107.

- [Research paper](https://www.scirp.org/journal/paperinformation?paperid=102869)
- [DOI](https://doi.org/10.4236/ojmsi.2020.84007)
- [Validation protocol](docs/VALIDATION.md)
- [Validation status](docs/VALIDATION_STATUS.md)
- [Engine guide](docs/ENGINE_GUIDE.md)
- [DES dispatch and lifecycle design](docs/DES_DISPATCH_AND_LIFECYCLE.md)
- [NHS benchmark evidence](docs/benchmarks/nhs/2026-08-02/README.md)

<p align="center">
  <img src="docs/assets/dashboard-preview.svg" alt="Healthcare demand and capacity dashboard preview" width="920">
</p>

## Current evidence

| Evidence | Result |
|---|---:|
| Official NHS providers represented | 463 |
| Provider-month MRI observations | 4,979 |
| National holdout actual MRI activity | 840,480 |
| National holdout predicted MRI activity | 821,577 |
| **National holdout WAPE** | **2.2491%** |
| Provider-level median WAPE | 13.0128% |
| Synthetic demand-capacity scenarios | 18 |
| Measured simulation runs | 36 |
| Supported Python versions | 3.10, 3.11 and 3.12 |
| Coverage policy | Whole package, minimum 80% |

The NHS result is an external aggregate forecasting benchmark. It does **not** validate patient-level DES behaviour, clinical safety or local operational readiness.

## What the platform models

| Area | Capability |
|---|---|
| Demand | Outpatient, inpatient and 24-hour emergency arrivals |
| Patient flow | Reception, preparation, MRI scanning and reporting |
| Operational behaviour | System-wide priority dispatch, FIFO within priority, cancellation, no-show, abandonment and unfinished work |
| Capacity | MRI machines, radiographers, radiologists, clerks and dynamic staffing windows |
| Reliability | Planned maintenance, stochastic failure, repair and optional scan restart |
| Measurement | Explicit queue counts by patient type, lifecycle reconciliation and state observations |
| Experimentation | Replications, bootstrap summaries, sensitivity analysis and scenario benchmarking |
| Delivery | Python package, CLI applications, Streamlit dashboard and Docker image |
| Quality | Linting, typing, whole-package coverage, wheel checks, Docker checks and multi-version CI |

## Correctness-hardened DES behaviour

The public advanced implementation is `healthcare_des.advanced_model`. It owns the corrected runtime path directly and does not mutate `advanced_engine` globals at import time. This removes the previous import-order dependency and makes the public API deterministic.

### MRI dispatch

MRI allocation uses one system-wide priority queue:

1. emergency;
2. inpatient;
3. outpatient;
4. FIFO order within each priority class.

Queue metrics are measured from the explicit waiting queue and include total, emergency, inpatient and outpatient counts.

### Urgent-aware capacity reserve

`emergency_capacity_reserve` is an **urgent-demand-aware runtime reservation**, not a permanently idle scanner allocation. Routine patients may use available scanners when no urgent patient is waiting. When urgent demand is queued, the dispatcher protects the configured reserved share from routine allocation.

### Patience and reporting

`abandonment_minutes` is a queue-wait budget. Active service time does not consume patience. MRI scan completion and report completion are tracked separately: a scanned patient remains completed while `report_status` records whether reporting completed or remained unfinished.

### Maintenance and downtime

`maintenance_policy` supports:

- `fixed_duration_after_release`: the full maintenance duration starts after the scanner becomes available;
- `fixed_calendar_window`: maintenance ends at the configured calendar-window end.

Overlapping maintenance and failure blockers are integrated as one unavailable interval, preventing double-counted downtime.

## Patient-flow model

```mermaid
flowchart LR
    A[Booked outpatient] --> B{Advance cancellation?}
    B -->|Yes| C[Cancelled]
    B -->|No| D{No-show?}
    D -->|Yes| E[No-show]
    D -->|No| F[Physical arrival]
    G[Inpatient arrival] --> F
    H[Emergency arrival] --> F
    F --> I[Reception queue and service]
    I --> J[Preparation queue and service]
    J --> K[System-wide priority MRI dispatch]
    K --> L[MRI scan completed]
    L --> M[Reporting queue and service]
    M --> N[Completed with report completed]
    L -. report not completed by termination .-> O[Completed with report unfinished]
    I -. wait budget exhausted .-> P[Abandoned]
    J -. wait budget exhausted .-> P
    K -. wait budget exhausted .-> P
```

The accounting identity is enforced:

```text
arrivals = completed + abandoned + unfinished
```

## Architecture

```mermaid
flowchart LR
    A[Scenario configuration] --> B[Arrival generation]
    B --> C[Staff queues]
    C --> D[Central MRI priority dispatcher]
    D --> E[MRI scanner state machines]
    E --> F[Reporting]
    F --> G[Patient ledger]
    D --> H[Queue and state observations]
    E --> H
    G --> I[KPI and uncertainty summaries]
    H --> I
    I --> J[CLI, benchmarks and dashboard]
```

The public advanced module owns the corrected model, machine classes and run functions. The older `advanced_engine` module remains an internal compatibility base only; importing the public module does not monkey-patch it.

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
    emergency_capacity_reserve=0.15,
    maintenance_policy="fixed_calendar_window",
    termination_policy="bounded_drain",
    max_drain_minutes=720,
    seed=17,
)

result, patients, state = run_advanced_once(config)
print(result)
print(patients["status"].value_counts())
assert result.arrivals == result.completed + result.abandoned + result.unfinished
```

## Command-line applications

```bash
healthcare-des --help
healthcare-des-benchmark --help
healthcare-des-reproduce --help
healthcare-des-advanced-benchmark --help
```

Run an advanced benchmark:

```bash
healthcare-des-advanced-benchmark \
  --days 7 \
  --replications 3 \
  --output outputs/advanced_benchmark.csv
```

## Dashboard and Docker

```bash
streamlit run app.py
```

```bash
docker build -t healthcare-des .
docker run --rm -p 8501:8501 healthcare-des
```

## Verification and validation

The repository distinguishes software verification from external and clinical validation.

| Area | Current status |
|---|---|
| Priority and FIFO behaviour | Regression tested |
| Simultaneous scanner release | Regression tested |
| Maintenance-versus-dispatch timing | Regression tested |
| Timeout-versus-dispatch boundary | Regression tested |
| Repeated scan interruption and repair | Regression tested |
| Import-order independence | Regression tested |
| Queue accounting | Explicit and regression tested |
| Whole-package coverage | Minimum 80%, no core-engine omission |
| Multi-version compatibility | Python 3.10, 3.11 and 3.12 |
| Package and CLI verification | Wheel build, installation and CLI smoke tests |
| Dashboard deployment | Docker build and Streamlit health check |
| External aggregate benchmark | Official NHS benchmark completed and versioned |
| Patient-level local validation | Required before operational deployment |
| Clinical safety validation | Required locally before operational use |

A simplified stable workload also checks approximate consistency with Little's Law. This is a software-verification reference, not a substitute for calibration against real patient-flow data.

## Testing and quality

```bash
pre-commit run --all-files
ruff check src tests scripts examples
mypy src/healthcare_des
pytest --cov=healthcare_des --cov-report=term-missing --cov-fail-under=80
python -m build
twine check dist/*
```

Coverage applies to the complete `healthcare_des` package. The core/compatibility engine is no longer omitted from measurement.

CI exercises Python 3.10, 3.11 and 3.12, repository-wide pre-commit checks, linting, typing, targeted regressions, strict whole-package coverage, installed CLI entry points, benchmark smoke tests, wheel installation, Docker build and the Streamlit health endpoint.

## Official NHS external benchmark

The repository includes an end-to-end external benchmark using official public NHS aggregate data. The selected transparent `lag_1` baseline achieved **2.2491% national holdout WAPE**, predicting 821,577 MRI activities against 840,480 observed.

Provider-level performance is more variable. The median provider WAPE was 13.0128%, with 68.5% of evaluated providers at or below 20% WAPE. Full versioned evidence and provenance are available in [`docs/benchmarks/nhs/2026-08-02/`](docs/benchmarks/nhs/2026-08-02/README.md).

## Assumptions and limitations

The project focuses on MRI patient flow rather than the entire radiology service. Default assumptions are illustrative until calibrated against authoritative local evidence.

The external NHS benchmark evaluates aggregate forecasting and evidence-processing capability. It does not demonstrate patient-level accuracy, causal impact, clinical safety or production scheduling readiness.

Real-world use requires independent validation of local pathways, workforce rules, costs, service targets, safety constraints, data quality and governance requirements.

## Repository structure

```text
.
├── src/healthcare_des/      # Simulation, experiments and analysis
├── tests/                   # Unit, integration and regression tests
├── examples/                # Reproducible usage examples
├── configs/                 # YAML scenario configurations
├── data/                    # Templates and non-sensitive aggregate inputs
├── docs/                    # Validation, benchmark and engine documentation
├── scripts/                 # Benchmarking and public-data workflows
├── outputs/                 # Generated machine-readable results
├── app.py                   # Streamlit dashboard entry point
├── pyproject.toml           # Package, tooling and coverage configuration
└── Dockerfile               # Reproducible container deployment
```

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
