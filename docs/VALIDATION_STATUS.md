# Verification and Validation Status

This document separates software correctness, empirical model validation and exact research reproduction. Passing software tests does not by itself establish clinical validity.

## Latest exhaustive software run

The repository was exercised end-to-end on **30 July 2026** using Python **3.10, 3.11 and 3.12**. The run covered pre-commit, Ruff, configured MyPy checks, all four CLI entry points, base simulation, advanced workflow, benchmark generation, example outputs, README assets, source and wheel builds, clean wheel installation, direct Streamlit startup and Docker health validation.

The strict non-deselected test suite produced:

```text
94 passed, 4 failed
Total package coverage: 77.20%
Documented coverage target: 80%
```

The operational workflows completed successfully, but the complete advanced engine is not yet defect-free.

## Current software status

| Area | Status | Evidence or next requirement |
|---|---|---|
| Deterministic execution | Verified for stable workflows | Fixed-seed tests compare results, patient ledgers and state observations |
| Patient accounting | Verified for stable workflows | Tests enforce `arrivals = completed + abandoned + unfinished` |
| Replication workflow | Verified | Tests verify one result row per replication and deterministic seed handling |
| Base and standard advanced simulation | Verified | End-to-end execution passed on Python 3.10–3.12 |
| CLI and benchmarks | Verified | All installed entry points, base simulation and benchmark workflows executed |
| Package integrity | Verified | Source and wheel distributions built and passed `twine check` |
| Clean wheel installation | Verified | Wheel installed and executed in a new virtual environment |
| Dashboard deployment | Verified | Direct Streamlit and Docker health endpoints returned healthy responses |
| Dynamic capacity reduction | Known defect | Resource target/token accounting failure tracked in [#10](https://github.com/sauravsingla/healthcare-discrete-event-simulation/issues/10) |
| Machine-failure interrupt and repair | Known defect | Unhandled active-scan interruption tracked in [#11](https://github.com/sauravsingla/healthcare-discrete-event-simulation/issues/11) |
| Machine-failure event recording | Known defect | Failure/repair event verification tracked in [#12](https://github.com/sauravsingla/healthcare-discrete-event-simulation/issues/12) |
| Paper scenario registry | Known defect | Hourly-profile and operating-hours mismatch tracked in [#13](https://github.com/sauravsingla/healthcare-discrete-event-simulation/issues/13) |
| Strict test coverage | Below target | 77.20% measured; restore at least 80% under [#14](https://github.com/sauravsingla/healthcare-discrete-event-simulation/issues/14) |
| Static quality | Partially verified | Ruff and pre-commit pass; configured MyPy exclusions remain temporary |
| Independent observational validation | Protocol available | Requires authoritative observations not used for calibration |
| Statistical equivalence testing | Protocol available | Requires agreed target metrics, tolerances and replication count |
| Exact 2020-paper reproduction | Not yet claimed | Authoritative scenario targets remain blank or incompletely transcribed |
| Local clinical pathway validation | Required before use | Clinical experts must confirm pathways, priorities and service rules |
| Workforce and safety validation | Required before use | Local staffing constraints and safety rules must be independently approved |
| Economic optimisation validation | Required before use | Replace illustrative weights with locally approved cost assumptions |
| Production scheduling approval | Out of scope | The repository is a research and decision-support framework |

## Interpretation

### Software verification

Software verification asks whether the implementation behaves consistently with its stated logic. Core execution, packaging and deployment pathways are verified. The four failing advanced-engine tests are publicly tracked and must be corrected before claiming complete software verification.

### Model validation

Model validation asks whether the simulated system adequately represents the real service for the intended decision. This requires independent observations, locally agreed outcome measures, subject-matter review and documented acceptance thresholds.

### Exact reproduction

Exact reproduction asks whether published scenarios and results can be regenerated from authoritative source assumptions. The project does not claim exact reproduction until all required paper targets and assumptions have been transcribed and verified without guessing.

## Minimum requirements before operational use

1. Resolve issues #10–#14 and restore the strict quality gate without test deselection.
2. Confirm patient pathways and priority rules with clinical and operational experts.
3. Calibrate arrival, service, cancellation, no-show, abandonment and downtime distributions using approved evidence.
4. Validate against a holdout period or independent site-level observations.
5. Agree service-level, safety, workforce and cost constraints with accountable stakeholders.
6. Document uncertainty, sensitivity and failure-mode analysis.
7. Complete governance, privacy, safety and change-control review.

See [VALIDATION.md](VALIDATION.md) for the detailed empirical-validation protocol.
