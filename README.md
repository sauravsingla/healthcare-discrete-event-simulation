# Healthcare Discrete-Event Simulation

[![CI](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml/badge.svg)](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![SimPy](https://img.shields.io/badge/SimPy-discrete--event%20simulation-2C5F2D)](https://simpy.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.4236%2Fojmsi.2020.84007-blue)](https://doi.org/10.4236/ojmsi.2020.84007)

An open-source Python **healthcare digital twin** for MRI demand forecasting, capacity planning, patient-flow simulation, queue analysis, resource utilisation, Monte Carlo uncertainty analysis and transparent staffing optimisation.

This repository provides a reproducible implementation and extension of:

> Saurav Singla (2020), **Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation**, *Open Journal of Modelling and Simulation*, 8, 88–107.

- [Research paper](https://www.scirp.org/journal/paperinformation?paperid=102869)
- [Presentation](https://www.slideshare.net/slideshow/demand-capacity-modelling-in-healthcare/238573051)
- [DOI](https://doi.org/10.4236/ojmsi.2020.84007)

## Why this project

Radiology services must balance stochastic patient demand against constrained MRI scanners, radiographers, radiologists, clerical capacity and operating hours. A mismatch can create long queues, poor throughput and underused or overloaded resources.

The project combines discrete-event simulation, synthetic demand generation, public aggregate NHS data calibration, scenario analysis and capacity search so researchers can test alternatives without disrupting a live healthcare service.

## Implemented capabilities

- outpatient, inpatient and emergency patient classes;
- emergency-priority MRI access through `simpy.PriorityResource`;
- reception, preparation, MRI scanning and report-interpretation stages;
- configurable scanners, clerks, radiographers and radiologists;
- stochastic arrivals, no-shows and service-time distributions;
- 8-hour, 16-hour and 24-hour scenarios;
- repeated experiments with deterministic random seeds;
- synthetic daily demand with weekday, weekend and Monday effects;
- Monte Carlo uncertainty analysis;
- one-at-a-time sensitivity analysis;
- transparent grid-search capacity optimisation;
- interactive Streamlit digital-twin dashboard;
- CSV outputs for throughput, waiting time, system time and SLA performance;
- calibration from official NHS England monthly diagnostic activity data;
- automated tests, pre-commit checks and Python 3.10–3.12 CI;
- Docker-based reproducible dashboard deployment.

## Public external dataset

The data workflow uses the official NHS England **Monthly Diagnostic Waiting Times and Activity** collection, which publishes provider and commissioner activity for key diagnostic tests including MRI:

https://www.england.nhs.uk/statistics/statistical-work-areas/diagnostics-waiting-times-and-activity/monthly-diagnostics-waiting-times-and-activity/

No patient-level, confidential or employer-owned data is stored in this repository. See [`data/README.md`](data/README.md) for the reproducible preparation process.

## Installation

```bash
git clone https://github.com/sauravsingla/healthcare-discrete-event-simulation.git
cd healthcare-discrete-event-simulation
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev,analysis,dashboard]"
```

## Run a simulation scenario

```bash
healthcare-des --config configs/baseline.yaml --replications 20
```

Run extended-hours and demand-aligned staffing experiments:

```bash
healthcare-des --config configs/extended-hours.yaml --replications 20 \
  --output outputs/extended_hours.csv

healthcare-des --config configs/demand-aligned-staffing.yaml --replications 20 \
  --output outputs/demand_aligned_staffing.csv
```

## Launch the digital-twin dashboard

```bash
streamlit run app.py
```

The dashboard lets users change daily demand, operating hours, MRI machines, radiographers, radiologists, no-show rates and replication counts. It displays mean waiting time, system time, throughput, SLA completion and a ranked capacity search.

Docker users can run:

```bash
docker build -t healthcare-des .
docker run --rm -p 8501:8501 healthcare-des
```

## Synthetic demand generation

```python
from healthcare_des.synthetic import DemandPattern, generate_daily_demand

frame = generate_daily_demand(
    DemandPattern(days=90, base_daily_demand=70, seed=17)
)
```

The generator produces privacy-safe demand with weekday/weekend variation, a Monday surge, trend and Poisson noise.

## Capacity optimisation

```python
from healthcare_des.model import ScenarioConfig
from healthcare_des.optimisation import search_capacity

candidates = search_capacity(
    ScenarioConfig(days=14, daily_demand=70),
    replications=8,
)
print(candidates.head())
```

The optimiser uses an auditable objective based on illustrative machine/staff capacity weights and a waiting-time penalty. These weights are deliberately transparent and should be replaced with locally validated costs before operational use.

## Monte Carlo and sensitivity analysis

```python
from healthcare_des.model import ScenarioConfig
from healthcare_des.sensitivity import monte_carlo, one_at_a_time

base = ScenarioConfig(days=14)
uncertainty = monte_carlo(base, samples=50, replications=4)
sensitivity = one_at_a_time(base, replications=10)
```

These analyses measure how uncertainty in demand, no-shows and scan duration propagates to patient-flow KPIs.

## Calibrate with NHS England data

After downloading and extracting an official NHS diagnostics CSV:

```bash
python scripts/prepare_nhs_diagnostics.py path/to/nhs_extract.csv

healthcare-des --config configs/baseline.yaml \
  --demand-csv data/processed/nhs_mri_activity.csv \
  --replications 20
```

## Key performance indicators

- completed patients and throughput per day;
- mean and 90th-percentile patient time in system;
- total queueing time;
- percentage completed within 120 minutes;
- no-show counts;
- scenario-level demand and capacity comparison;
- uncertainty distributions and capacity-search objective scores.

## Research validation targets

The original paper compared 11 operational scenarios. Its reported findings included:

- MRI waiting-room queue time reducing from approximately 17 minutes to 5 minutes;
- outpatient time in the system reducing by approximately 20 minutes;
- increased outpatient throughput under dedicated-resource and demand-aligned staffing scenarios.

These are treated as **research validation targets**, not automatically claimed as reproduced results. Python outputs must be compared transparently against the original assumptions and public-data calibration.

## Repository structure

```text
.
├── app.py                       # Streamlit digital-twin dashboard
├── configs/                     # reproducible scenario definitions
├── data/                        # public-data instructions; raw data excluded
├── scripts/                     # NHS data preparation utilities
├── src/healthcare_des/          # simulation, synthetic demand, optimisation
├── tests/                       # deterministic and extension tests
├── .github/workflows/ci.yml     # Python 3.10–3.12 CI
├── .pre-commit-config.yaml
├── Dockerfile
├── CITATION.cff
├── LICENSE
└── pyproject.toml
```

## Testing and quality

```bash
ruff check src tests scripts app.py
pytest --cov=healthcare_des --cov-report=term-missing
pre-commit run --all-files
```

## Assumptions and limitations

The implementation focuses on MRI rather than the entire radiology service. It uses public aggregate data and configurable distributions rather than patient-level records. Night demand, shared-resource effects, costs, clinical outcomes and staff interactions require additional evidence before operational use.

The optimisation weights and Monte Carlo parameter ranges are illustrative. They must be calibrated using local operational evidence before decision-making.

This project is a research and decision-support framework. It is not a clinical recommendation or production scheduling system.

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

## Search topics

`healthcare simulation` · `discrete event simulation` · `SimPy` · `MRI capacity planning` · `patient flow` · `queueing theory` · `operations research` · `hospital analytics` · `healthcare digital twin` · `resource optimisation` · `Monte Carlo simulation` · `sensitivity analysis` · `NHS diagnostics` · `Streamlit`

## Author

**Saurav Singla**

- [LinkedIn](https://www.linkedin.com/in/sauravsingla008/)
- [ORCID](https://orcid.org/0000-0002-6404-3988)
