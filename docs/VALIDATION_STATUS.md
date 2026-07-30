# Verification and Validation Status

This document separates software correctness, empirical model validation and exact research reproduction. Passing software tests does not by itself establish clinical validity.

## Latest exhaustive software run

The repository was exercised end-to-end on **30 July 2026** using Python **3.10, 3.11 and 3.12**. The run covered pre-commit, Ruff, configured MyPy checks, the complete non-deselected test suite, all CLI entry points, base simulation, advanced workflow, benchmark generation, example outputs, README assets, source and wheel builds, clean wheel installation, and Docker dashboard health validation.

The final quality-gate run completed successfully with the documented package coverage requirement of at least **80%** enforced across the supported Python matrix.

## Current software status

| Area | Status | Evidence or next requirement |
|---|---|---|
| Deterministic execution | Verified | Fixed-seed tests compare results, patient ledgers and state observations |
| Patient accounting | Verified | Tests enforce `arrivals = completed + abandoned + unfinished` |
| Replication workflow | Verified | Tests verify one result row per replication and deterministic seed handling |
| Base and advanced simulation | Verified | End-to-end execution passed on Python 3.10–3.12 |
| Dynamic capacity reduction | Verified | Regression coverage confirms resource targets and tokens remain consistent |
| Machine-failure interrupt and repair | Verified | Active-scan interruptions, repair waits and restart behaviour are covered |
| Machine-failure event recording | Verified | Failure counts and downtime are recorded and tested |
| Paper scenario registry | Verified | All eleven registered paper scenarios validate and execute |
| Distribution fitting | Verified | Information criteria and SciPy-compatible goodness-of-fit execution are tested |
| Strict test coverage | Verified | CI enforces at least 80% package coverage without test deselection |
| Static quality | Verified | Pre-commit, Ruff and configured MyPy checks pass |
| CLI and benchmarks | Verified | Installed entry points and bounded benchmark workflows execute |
| Package integrity | Verified | Source and wheel distributions build and pass `twine check` |
| Clean wheel installation | Verified | Built wheel installs and executes in a new virtual environment |
| Dashboard deployment | Verified | Docker image starts and the Streamlit health endpoint responds successfully |
| Independent observational validation | Protocol available | Requires authoritative observations not used for calibration |
| Statistical equivalence testing | Protocol available | Requires agreed target metrics, tolerances and replication count |
| Exact 2020-paper reproduction | Not yet claimed | Authoritative scenario targets remain blank or incompletely transcribed |
| Local clinical pathway validation | Required before use | Clinical experts must confirm pathways, priorities and service rules |
| Workforce and safety validation | Required before use | Local staffing constraints and safety rules must be independently approved |
| Economic optimisation validation | Required before use | Replace illustrative weights with locally approved cost assumptions |
| Production scheduling approval | Out of scope | The repository is a research and decision-support framework |

## Interpretation

### Software verification

Software verification asks whether the implementation behaves consistently with its stated logic. Core execution, advanced-engine regressions, packaging, command-line interfaces and deployment pathways are now covered by the strict automated quality gate.

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

See [VALIDATION.md](VALIDATION.md) for the detailed empirical-validation protocol.
