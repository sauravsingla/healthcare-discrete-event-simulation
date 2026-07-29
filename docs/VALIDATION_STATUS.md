# Verification and Validation Status

This document separates software correctness, empirical model validation and exact research reproduction. Passing software tests does not by itself establish clinical validity.

## Status matrix

| Area | Status | Evidence or next requirement |
|---|---|---|
| Deterministic execution | Implemented | Fixed-seed regression tests compare complete results, patient ledgers and state observations |
| Patient accounting | Implemented | Tests enforce `arrivals = completed + abandoned + unfinished` |
| Replication workflow | Implemented | Tests verify one result row per replication and deterministic seed handling |
| Small-data end-to-end sanity | Implemented | One-day scenarios exercise simulation, summaries and benchmark generation |
| Static quality | Implemented | Ruff, mypy and pre-commit checks run in CI |
| Test coverage | Implemented | CI enforces at least 80% package coverage |
| Python compatibility | Implemented | CI tests Python 3.10, 3.11 and 3.12 |
| Package integrity | Implemented | Source and wheel distributions are built and checked |
| Clean wheel installation | Implemented | Built wheel is installed into a new virtual environment and smoke-tested |
| CLI integrity | Implemented | Every installed CLI entry point is executed with `--help` |
| Dashboard deployment | Implemented | Docker image starts and the Streamlit health endpoint is checked |
| Public aggregate-data workflow | Implemented | No patient-level confidential or employer-owned data is required |
| Independent observational validation | Protocol available | Requires authoritative observations not used for calibration |
| Statistical equivalence testing | Protocol available | Requires agreed target metrics, tolerances and replication count |
| Exact 2020-paper reproduction | Not yet claimed | Authoritative scenario targets remain blank or incompletely transcribed |
| Local clinical pathway validation | Required before use | Clinical experts must confirm pathways, priorities and service rules |
| Workforce and safety validation | Required before use | Local staffing constraints and safety rules must be independently approved |
| Economic optimisation validation | Required before use | Replace illustrative weights with locally approved cost assumptions |
| Production scheduling approval | Out of scope | The repository is a research and decision-support framework |

## Interpretation

### Software verification

Software verification asks whether the implementation behaves consistently with its stated logic. This repository addresses that through automated tests, deterministic seeds, accounting identities, static checks, package installation checks and deployment smoke tests.

### Model validation

Model validation asks whether the simulated system adequately represents the real service for the intended decision. This requires independent observations, locally agreed outcome measures, subject-matter review and documented acceptance thresholds.

### Exact reproduction

Exact reproduction asks whether published scenarios and results can be regenerated from authoritative source assumptions. The project does not claim exact reproduction until all required paper targets and assumptions have been transcribed and verified without guessing.

## Minimum requirements before operational use

1. Confirm patient pathways and priority rules with clinical and operational experts.
2. Calibrate arrival, service, cancellation, no-show, abandonment and downtime distributions using approved evidence.
3. Validate against a holdout period or independent site-level observations.
4. Agree service-level, safety, workforce and cost constraints with accountable stakeholders.
5. Document uncertainty, sensitivity and failure-mode analysis.
6. Complete governance, privacy, safety and change-control review.

See [VALIDATION.md](VALIDATION.md) for the detailed protocol.
