# Healthcare Discrete-Event Simulation

[![CI](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml/badge.svg)](https://github.com/sauravsingla/healthcare-discrete-event-simulation/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Coverage](https://img.shields.io/badge/whole--package%20coverage-91.88%25-brightgreen)](#testing-and-quality)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.4236%2Fojmsi.2020.84007-blue)](https://doi.org/10.4236/ojmsi.2020.84007)
[![Docker](https://img.shields.io/badge/Docker-verified-2496ED?logo=docker&logoColor=white)](#dashboard-and-docker)

A reproducible Python platform for MRI demand forecasting, capacity planning, patient-flow simulation, queue analysis, resource utilisation and uncertainty analysis.

This repository modernises and extends Saurav Singla (2020), **Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation**, *Open Journal of Modelling and Simulation*, 8, 88–107.

- [Research paper](https://www.scirp.org/journal/paperinformation?paperid=102869)
- [DOI](https://doi.org/10.4236/ojmsi.2020.84007)
- [Paper reproduction matrix](docs/PAPER_REPRODUCTION_MATRIX.md)
- [Validation protocol](docs/VALIDATION.md)
- [Validation status](docs/VALIDATION_STATUS.md)
- [Engine guide](docs/ENGINE_GUIDE.md)
- [DES dispatch and lifecycle design](docs/DES_DISPATCH_AND_LIFECYCLE.md)
- [NHS benchmark evidence](docs/benchmarks/nhs/2026-08-02/README.md)

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
| Latest verified tests | **210 passed** |
| Latest whole-package coverage | **91.88%** |
| Supported Python versions | 3.10, 3.11 and 3.12 |
| Package version | **1.3.0** |
| Coverage policy | Whole package, minimum 80% |

The NHS result is an external aggregate forecasting benchmark. It does **not** validate patient-level DES behaviour, clinical safety or local operational readiness.

## Singla 2020 paper reproduction evidence

The repository now implements all seven evidence improvements requested for the 2020 paper. The supported claim is deliberately precise:

> **Source-backed reproduction contract with partial numerical reproduction.**

It does not claim bit-for-bit equivalence with the original Simul8 model because the proprietary model, exact event calendar, Pearson V parameters and original random streams are not available.

### Published numerical targets captured

| Published result | Value |
|---|---:|
| Historical February 2018 demand | **2,089 scans** |
| Simulated monthly demand range | **1,828–1,930 scans** |
| MRI waiting-room queue before improvement | **17 minutes** |
| MRI waiting-room queue after improvement | **5 minutes** |
| Scenario 11 system-time reduction | **20 minutes** |

### Seven implemented reproduction improvements

| Improvement | Repository implementation |
|---|---|
| 1. Missing baseline target | The 17-minute baseline MRI waiting time is exported alongside the 5-minute improved result and 20-minute scenario-11 reduction. |
| 2. Scenario-level comparison | A comparison template and comparison function report paper value, reproduced value, absolute difference, tolerance and pass/fail. |
| 3. Distribution fidelity | Paper-specific samplers implement exponential reception, triangular preparation `(4,5,6)`, normal MRI service `(26.46, 8.0)` and uniform reporting `(6,12)`. Pearson V arrivals remain explicitly unavailable where parameters are not disclosed. |
| 4. MRI parameters | The supported paper baseline applies MRI mean **26.46 minutes** and standard deviation **8.0 minutes**. |
| 5. Resource constraints | Radiographer capacity `4/3/2`, clerk capacity `1/1/1` and consultant capacity `1/1/1` are applied directly. The 90% availability assumption and hard queue capacities of 20 and 25 are exported with explicit unsupported-status notes rather than silently approximated. |
| 6. Evidence index | A machine-readable index maps published evidence concepts to repository fields and generated outputs. |
| 7. Claim wording | The manifest and documentation enforce the qualified partial-reproduction claim and list all unresolved limitations. |

### Eleven-scenario catalogue

All eleven published scenario intentions are indexed. A numerical value is attached only where the currently available paper evidence provides one. Missing values are marked **not numerically disclosed in current evidence** and are never invented.

| Scenario | Published intention |
|---|---|
| 01 | Outpatient arrival profile: 8-hour access |
| 02 | Outpatient arrival profile: 16-hour access |
| 03 | Outpatient arrival profile: 24-hour access |
| 04 | MRI service-time distribution experiment A |
| 05 | MRI service-time distribution experiment B |
| 06 | MRI service-time distribution experiment C |
| 07 | Normal-hours overbooking to offset no-shows |
| 08 | Start/end-of-hour overbooking |
| 09 | Exclusive resources for emergency patients |
| 10 | Exclusive resources for inpatient and emergency patients |
| 11 | Staff capacity changed to match demand by shift |

### Generated reproduction evidence

Run:

```bash
python scripts/export_paper_reproduction_spec.py \
  --output-dir outputs/paper_reproduction \
  --distribution-samples 1000
```

The exporter creates:

- `singla_2020_reproduction_manifest.json`
- `singla_2020_published_targets.csv`
- `singla_2020_scenario_catalog.csv`
- `singla_2020_comparison_template.csv`
- `singla_2020_evidence_index.csv`
- `singla_2020_constraint_status.csv`
- `singla_2020_service_distribution_samples.csv`

CI validates the DOI, all 11 scenarios, 46 replications, seed 17, published targets, evidence schema and generated files.

## Implemented DES capabilities

| Capability | Verified behaviour |
|---|---|
| Patient demand generation | Outpatient appointments, inpatient arrivals and 24-hour emergency arrivals |
| Multi-stage patient flow | Reception, preparation, MRI scanning and reporting |
| MRI priority dispatch | Emergency before inpatient before outpatient, FIFO within priority |
| Event-driven allocation | Queue arrivals, scanner releases and availability changes wake dispatch immediately |
| Exact deadline ordering | Same-timestamp scanner release is processed before patience expiry without extra grace |
| Multiple scanners | One central dispatcher allocates across all available MRI machines |
| Dynamic staffing | Time-varying clerk, radiographer and radiologist capacities |
| Cancellation and no-show | Separate pre-arrival outcomes for booked outpatients |
| Abandonment | Stage-specific queue-wait abandonment |
| Maintenance | Fixed-duration-after-release and fixed-calendar-window policies |
| Failure and repair | Stochastic failure, interruption, repair and optional restart |
| Downtime accounting | Overlapping maintenance and failure intervals counted once |
| Termination policies | Horizon, drain and bounded drain |
| Replications and uncertainty | Deterministic seeds, standard deviations and bootstrap intervals |
| Sensitivity and capacity analysis | Monte Carlo, one-at-a-time sensitivity and ranked capacity alternatives |
| Delivery | Python API, four CLI applications, Streamlit dashboard and Docker |

## MRI dispatch and lifecycle correctness

MRI allocation uses one system-wide priority queue:

1. emergency;
2. inpatient;
3. outpatient;
4. FIFO within each priority class.

Dispatch is event-driven and contains no polling interval or added patience allowance. Queue arrivals, scanner releases, maintenance transitions, failures and repairs wake the dispatcher immediately. Exact patience-deadline ordering is regression tested.

Patient accounting enforces:

```text
arrivals = completed + abandoned + unfinished
```

MRI scan completion and report completion are tracked separately so a scanned patient remains completed even when reporting is unfinished at termination.

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

Run the advanced benchmark:

```bash
healthcare-des-advanced-benchmark \
  --days 7 \
  --replications 3 \
  --output outputs/advanced_benchmark.csv
```

## Command-line applications

```bash
healthcare-des --help
healthcare-des-benchmark --help
healthcare-des-reproduce --help
healthcare-des-advanced-benchmark --help
```

## Dashboard and Docker

```bash
streamlit run app.py
```

```bash
docker build -t healthcare-des .
docker run --rm -p 8501:8501 healthcare-des
```

The Docker workflow verifies image build, startup, health and the Streamlit dashboard endpoint.

## Verification and validation

| Area | Current status |
|---|---|
| Priority and FIFO behaviour | Regression tested |
| Event-driven scanner dispatch | Regression tested, including exact deadline ordering |
| Maintenance, failure and downtime | Regression tested |
| Queue and lifecycle accounting | Explicit and regression tested |
| Paper reproduction contract | Source-backed manifest, targets, scenario catalogue, comparison template and evidence exports |
| Whole-package coverage | **91.88%**, above the 80% gate |
| Multi-version compatibility | Python 3.10, 3.11 and 3.12 |
| Package and CLI verification | Wheel build, installation and CLI smoke tests |
| Dashboard deployment | Docker health and endpoint verification |
| External aggregate benchmark | Official NHS benchmark completed and versioned |
| Patient-level local validation | Required before operational deployment |
| Clinical safety validation | Required locally before operational use |

## Testing and quality

```bash
pre-commit run --all-files
ruff check src tests scripts examples
mypy src/healthcare_des
pytest --cov=healthcare_des --cov-report=term-missing --cov-fail-under=80
python -m build
twine check dist/*
```

Latest merged verification before PR #59:

- **210 tests passed**
- **91.88% whole-package coverage**
- **zero pytest warnings**
- Python 3.10, 3.11 and 3.12 supported
- Ruff, Ruff Format, pre-commit and MyPy enabled
- package and Docker checks enabled

The final totals for PR #59 will be refreshed from its successful CI result before merge if they change.

## Official NHS external benchmark

The transparent `lag_1` baseline achieved **2.2491% national holdout WAPE**, predicting 821,577 MRI activities against 840,480 observed. Median provider WAPE was 13.0128%, with 68.5% of evaluated providers at or below 20% WAPE.

Full evidence is available in [`docs/benchmarks/nhs/2026-08-02/`](docs/benchmarks/nhs/2026-08-02/README.md).

## Assumptions and limitations

The platform focuses on MRI patient flow rather than the entire radiology service. Default assumptions remain illustrative until calibrated against authoritative local evidence.

The paper reproduction evidence does not establish bit-for-bit Simul8 equivalence. The original model, exact event calendar, Pearson V parameters and random streams are unavailable. Scenario-level numerical comparisons are produced only where authoritative published values are available.

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
├── docs/                    # Validation, paper evidence and benchmarks
├── scripts/                 # Benchmarking and evidence export workflows
├── outputs/                 # Generated machine-readable results
├── app.py                   # Streamlit dashboard entry point
├── pyproject.toml           # Package and tooling configuration
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
