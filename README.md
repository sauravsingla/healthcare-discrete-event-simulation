# Healthcare Discrete-Event Simulation

[![CI](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml/badge.svg)](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.4236%2Fojmsi.2020.84007-blue)](https://doi.org/10.4236/ojmsi.2020.84007)

An open-source Python healthcare digital twin for MRI demand forecasting, capacity planning, patient-flow simulation, queue analysis, resource utilisation, uncertainty analysis and transparent staffing optimisation.

This repository provides a reproducible implementation and extension of Saurav Singla (2020), **Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation**, *Open Journal of Modelling and Simulation*, 8, 88–107.

- [Research paper](https://www.scirp.org/journal/paperinformation?paperid=102869)
- [DOI](https://doi.org/10.4236/ojmsi.2020.84007)

## Implemented capabilities

- outpatient, inpatient and emergency patient classes;
- emergency-priority MRI access through `simpy.PriorityResource`;
- reception, preparation, MRI scanning and reporting stages;
- configurable scanners, clerks, radiographers and radiologists;
- deterministic replicated experiments;
- stage-specific queue waiting times;
- scheduled-capacity resource utilisation;
- patient-type waiting, system-time and SLA metrics;
- warm-up periods for steady-state analysis;
- unfinished-work and completion-rate reporting;
- optional drain-until-empty execution;
- 95% confidence intervals across replications;
- multi-scenario benchmarking;
- Monte Carlo and sensitivity analysis;
- transparent capacity optimisation;
- Streamlit dashboard and Docker deployment;
- NHS England aggregate-data calibration workflow;
- linting, static type checking, coverage enforcement and package-build CI.

## Installation

```bash
git clone https://github.com/sauravsingla/healthcare-discrete-event-simulation.git
cd healthcare-discrete-event-simulation
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev,analysis,dashboard]"
```

## Run a simulation

```bash
healthcare-des --config configs/baseline.yaml --replications 20
```

Scenario YAML files may include:

```yaml
name: baseline
days: 30
warmup_days: 3
drain_until_empty: false
operating_hours: 8
daily_demand: 70
mri_machines: 4
clerks: 1
radiographers: 4
radiologists: 1
```

`warmup_days` generates patients before the measurement window and excludes them from reported KPIs. `drain_until_empty: true` allows all eligible arrivals to finish before results are calculated.

## Run the multi-scenario benchmark

```bash
healthcare-des-benchmark \
  --config configs/baseline.yaml \
  --replications 20 \
  --output outputs/benchmark.csv
```

The default benchmark compares baseline, lower and higher demand, high no-show rates, added MRI/radiographer/radiologist capacity, and reduced capacity.

For each scenario it reports means and uncertainty for:

- total and stage-specific waiting time;
- mean and P90 system time;
- throughput and completion rate;
- percentage completed within 120 minutes;
- unfinished patients;
- clerk, radiographer, MRI and radiologist utilisation;
- outpatient, inpatient and emergency performance;
- standard deviation and normal 95% confidence intervals.

### Interpreting benchmark results

A lower mean wait is not automatically the best option if it requires disproportionate capacity. Sustained utilisation close to or above 100% of scheduled capacity signals overtime or an unstable operating plan. Small differences whose confidence intervals overlap should be treated cautiously. Local cost, safety, workforce and clinical constraints must be considered before operational use.

## KPI definitions

- **Arrivals:** measured-window patient requests, including outpatient no-shows.
- **Completed:** measured arrivals that finish all four stages before the run ends.
- **Unfinished:** eligible measured arrivals still in progress when a fixed-horizon run closes.
- **Completion rate:** completed patients divided by arrivals excluding no-shows.
- **Stage waits:** reception, preparation, MRI and reporting queue delays.
- **Utilisation:** measured busy service minutes divided by scheduled operating minutes multiplied by resource capacity. Values above 100% indicate service extending beyond scheduled capacity.
- **Patient-type KPIs:** wait, system time and 120-minute SLA calculated separately for outpatient, inpatient and emergency patients.
- **95% confidence interval:** replication mean ± 1.96 standard errors; use more replications for decision-grade comparisons.

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

The optimiser uses transparent illustrative capacity weights and a waiting-time penalty. Replace these weights with locally validated costs before operational use.

## Monte Carlo and sensitivity analysis

```python
from healthcare_des.model import ScenarioConfig
from healthcare_des.sensitivity import monte_carlo, one_at_a_time

base = ScenarioConfig(days=14, warmup_days=2)
uncertainty = monte_carlo(base, samples=50, replications=4)
sensitivity = one_at_a_time(base, replications=10)
```

## Dashboard

```bash
streamlit run app.py
```

Docker:

```bash
docker build -t healthcare-des .
docker run --rm -p 8501:8501 healthcare-des
```

## Public external dataset

The calibration workflow uses the official NHS England **Monthly Diagnostic Waiting Times and Activity** collection. No patient-level, confidential or employer-owned data is stored in this repository. See [`data/README.md`](data/README.md).

## Research validation

The original paper compared 11 operational scenarios and reported substantial queue and system-time improvements under selected staffing arrangements. These are validation targets, not automatically claimed as reproduced results. A rigorous reproduction should record the exact configuration, random seeds, replication count, software version and differences from the original assumptions.

## Testing and quality

```bash
ruff check src tests scripts
mypy src/healthcare_des
pytest --cov=healthcare_des --cov-report=term-missing --cov-fail-under=80
python -m build
twine check dist/*
```

CI executes these checks on Python 3.10, 3.11 and 3.12.

## Assumptions and limitations

The implementation focuses on MRI rather than the entire radiology service. Arrivals are currently generated from a constant exponential rate during operating hours. Appointment-slot structures, hourly demand profiles, equipment downtime, staff breaks, abandonment, cancellations, shared-resource effects, clinical outcomes and local costs require additional evidence before operational use.

The model is a research and decision-support framework. It is not a clinical recommendation or production scheduling system.

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
