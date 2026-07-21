# Healthcare Discrete-Event Simulation

[![CI](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml/badge.svg)](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![SimPy](https://img.shields.io/badge/SimPy-discrete--event%20simulation-2C5F2D)](https://simpy.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.4236%2Fojmsi.2020.84007-blue)](https://doi.org/10.4236/ojmsi.2020.84007)

An open-source Python framework for **healthcare demand forecasting, MRI capacity planning, patient-flow simulation, queue analysis, resource utilisation and scenario comparison** using SimPy.

This repository provides a reproducible implementation and extension of:

> Saurav Singla (2020), **Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation**, *Open Journal of Modelling and Simulation*, 8, 88–107.

- [Research paper](https://www.scirp.org/journal/paperinformation?paperid=102869)
- [Presentation](https://www.slideshare.net/slideshow/demand-capacity-modelling-in-healthcare/238573051)
- [DOI](https://doi.org/10.4236/ojmsi.2020.84007)

## Why this project

Radiology services must balance stochastic patient demand against constrained MRI scanners, radiographers, radiologists, clerical capacity and operating hours. A mismatch can create long queues, poor throughput and underused or overloaded resources.

The model allows researchers and operational teams to test alternative configurations without disrupting a live healthcare service.

## Implemented model

The Python simulation currently includes:

- outpatient, inpatient and emergency patient classes;
- emergency-priority MRI access through `simpy.PriorityResource`;
- reception, preparation, MRI scanning and report-interpretation stages;
- configurable scanners, clerks, radiographers and radiologists;
- stochastic arrivals, no-shows and service-time distributions;
- 8-hour, 16-hour and 24-hour scenarios;
- repeated experiments with deterministic random seeds;
- CSV outputs for throughput, waiting time, system time and SLA performance;
- calibration from official NHS England monthly diagnostic activity data.

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
pip install -e ".[dev,analysis]"
```

## Run a scenario

```bash
healthcare-des --config configs/baseline.yaml --replications 20
```

Run the extended-hours and demand-aligned staffing experiments:

```bash
healthcare-des --config configs/extended-hours.yaml --replications 20 \
  --output outputs/extended_hours.csv

healthcare-des --config configs/demand-aligned-staffing.yaml --replications 20 \
  --output outputs/demand_aligned_staffing.csv
```

The CLI prints a JSON summary and stores replication-level results as CSV.

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
- scenario-level demand and capacity comparison.

## Research validation targets

The original paper compared 11 operational scenarios. Its reported findings included:

- MRI waiting-room queue time reducing from approximately 17 minutes to 5 minutes;
- outpatient time in the system reducing by approximately 20 minutes;
- increased outpatient throughput under dedicated-resource and demand-aligned staffing scenarios.

These are treated as **research validation targets**, not automatically claimed as reproduced results. Python outputs must be compared transparently against the original assumptions and public-data calibration.

## Repository structure

```text
.
├── configs/                    # reproducible scenario definitions
├── data/                       # public-data instructions; raw data excluded
├── scripts/                    # NHS data preparation utilities
├── src/healthcare_des/         # simulation engine, config and CLI
├── tests/                      # deterministic model tests
├── .github/workflows/ci.yml    # Python 3.10–3.12 CI
├── CITATION.cff
├── LICENSE
└── pyproject.toml
```

## Testing

```bash
ruff check src tests scripts
pytest --cov=healthcare_des --cov-report=term-missing
```

## Assumptions and limitations

The implementation focuses on MRI rather than the entire radiology service. It uses public aggregate data and configurable distributions rather than patient-level records. Night demand, shared-resource effects, costs, clinical outcomes and staff interactions require additional evidence before operational use.

This project is a research and decision-support framework. It is not a clinical recommendation system.

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

`healthcare simulation` · `discrete event simulation` · `SimPy` · `MRI capacity planning` · `patient flow` · `queueing theory` · `operations research` · `hospital analytics` · `healthcare digital twin` · `resource optimisation` · `NHS diagnostics`

## Author

**Saurav Singla**

- [LinkedIn](https://www.linkedin.com/in/sauravsingla008/)
- [ORCID](https://orcid.org/0000-0002-6404-3988)
