# Healthcare Discrete-Event Simulation

[![CI](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml/badge.svg)](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.4236%2Fojmsi.2020.84007-blue)](https://doi.org/10.4236/ojmsi.2020.84007)

An open-source Python healthcare digital twin for MRI demand forecasting, capacity planning, patient-flow simulation, queue analysis, resource utilisation, uncertainty analysis and transparent staffing optimisation.

This repository provides an implementation and research extension of Saurav Singla (2020), **Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation**, *Open Journal of Modelling and Simulation*, 8, 88–107.

- [Research paper](https://www.scirp.org/journal/paperinformation?paperid=102869)
- [DOI](https://doi.org/10.4236/ojmsi.2020.84007)

## Current capabilities

- outpatient, inpatient and 24-hour emergency demand;
- reception, preparation, MRI scanning and reporting stages;
- patient-class priorities and shared MRI dispatching;
- stage-specific queue waits, service time and system time;
- cancellation, no-show, abandonment and unfinished-patient accounting;
- complete per-patient outcome ledger;
- weekday, monthly and hourly demand profiles;
- calendar-based simulation dates;
- dynamic staff-capacity windows;
- MRI maintenance, stochastic failure, repair and optional scan restart;
- capacity-aware outpatient scheduling and controlled overbooking;
- warm-up exclusion and configurable horizon/drain policies;
- operational-hours and 24-hour queue/capacity measures;
- deterministic replicated experiments and bootstrap summaries;
- scenario benchmarking, sensitivity analysis and calibration utilities;
- Streamlit dashboard and Docker deployment;
- linting, type checking, coverage, package-build and release-build workflows.

## Installation

```bash
git clone https://github.com/sauravsingla/healthcare-discrete-event-simulation.git
cd healthcare-discrete-event-simulation
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev,dashboard]"
```

## Corrected advanced engine

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

### Patient lifecycle

```text
booked outpatient
  -> advance cancellation OR expected arrival
  -> no-show OR actual arrival
actual arrival / inpatient / emergency
  -> reception
  -> preparation
  -> shared MRI dispatch
  -> reporting
  -> completed OR abandoned OR unfinished at termination
```

`wait_minutes` is the sum of stage queue waits. `system_minutes` includes waiting and service time. Cancellation and no-show are recorded separately from patients who enter the physical service system.

### Termination policies

- `horizon`: stop at the measurement horizon and report unfinished patients.
- `bounded_drain`: stop arrivals and allow up to `max_drain_minutes` for completion.
- `drain`: stop arrivals and continue while active patients remain.

Use the same policy across scenarios unless termination is itself the experimental factor.

## Existing command-line simulation

```bash
healthcare-des --config configs/baseline.yaml --replications 20
```

The original command-line workflow remains available for the base model and YAML scenarios.

## Multi-scenario benchmark

```bash
healthcare-des-benchmark \
  --config configs/baseline.yaml \
  --replications 20 \
  --output outputs/benchmark.csv
```

For corrected-engine runtime scaling:

```bash
python scripts/benchmark_advanced.py \
  --days 7 \
  --replications 3 \
  --output outputs/advanced_benchmark.csv
```

The scaling benchmark records elapsed runtime, patient-ledger size and state-observation size across demand levels and 1–20 MRI machines. It is a performance diagnostic, not a clinical validation result.

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
- **Operational queue/capacity measures:** state observations restricted to configured opening hours.
- **24-hour measures:** all state observations in the measured period.

The core reconciliation identity is:

```text
arrivals = completed + abandoned + unfinished
```

## Calibration and research validation

The public-data workflow uses aggregate external data and stores no patient-level confidential or employer-owned information. See [`data/README.md`](data/README.md).

The repository distinguishes:

1. software verification;
2. model validation against independent observations;
3. exact paper reproduction.

Blank expected values in `data/paper_targets_template.csv` deliberately indicate that authoritative published targets have not yet been transcribed. They must not be replaced with guessed values.

See [`docs/VALIDATION.md`](docs/VALIDATION.md) for the complete protocol, including holdout validation, statistical equivalence, warm-up handling and reproduction decision rules.

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

## Testing and quality

```bash
ruff check src tests scripts examples
mypy src/healthcare_des
pytest --cov=healthcare_des --cov-report=term-missing --cov-fail-under=80
python -m build
twine check dist/*
```

CI runs these checks on Python 3.10, 3.11 and 3.12, executes an advanced-engine accounting smoke test, and uploads coverage and distribution artifacts from Python 3.12.

A separate tag-triggered release workflow builds and validates source and wheel distributions. It deliberately does not publish to a package index without repository secrets and an explicit release decision.

## Assumptions and limitations

The project focuses on MRI patient flow rather than the entire radiology service. The advanced engine supports hourly demand, appointment schedules, downtime, cancellations, abandonment and dynamic staffing, but their default values remain illustrative until calibrated against authoritative local evidence.

Exact reproduction of the 2020 paper is not yet claimed while published scenario targets remain blank or incompletely transcribed. Real-world use additionally requires independent validation of clinical pathways, workforce rules, costs, safety constraints and governance requirements.

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
