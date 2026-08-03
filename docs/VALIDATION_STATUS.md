# Verification and Validation Status

This document separates software correctness, empirical model validation and exact research reproduction. Passing software tests does not by itself establish clinical validity.

## Latest exhaustive software run

The latest verified version 1.3.0 quality run completed on **3 August 2026** across Python **3.10, 3.11 and 3.12**. It covered repository-wide pre-commit and Ruff checks, configured MyPy checks, targeted DES regressions, the complete test suite, strict whole-package coverage, all installed CLI entry points, advanced-model smoke execution, benchmark and metadata generation, example outputs, README performance assets, paper-reproduction evidence export, source and wheel builds, `twine check`, clean-wheel installation, Docker build, container health and the Streamlit endpoint.

The verified snapshot contains **210 passed tests**, **91.88% whole-package coverage** and **zero pytest warnings**, above the enforced 80% gate. The public advanced model is approximately 96% covered, the compatibility engine approximately 93%, paper reproduction approximately 92%, dashboard transformation helpers approximately 93%, calibration approximately 96%, configuration approximately 91%, and the primary CLI approximately 84%. Five semantic dashboard transformation tests are included.

## Current software status

| Area | Status | Evidence or next requirement |
|---|---|---|
| Deterministic execution | Verified | Fixed-seed tests compare results, patient ledgers and state observations |
| Patient accounting | Verified | Tests enforce `arrivals = completed + abandoned + unfinished` |
| Replication workflow | Verified | Tests verify one result row per replication and deterministic seed handling |
| Base and advanced simulation | Verified | End-to-end execution passed on Python 3.10–3.12 |
| Priority and FIFO dispatch | Verified | Priority ordering, equal-priority FIFO and simultaneous release are regression tested |
| Event-driven MRI dispatch | Verified | Queue arrivals, scanner releases and availability changes wake dispatch without polling |
| Queue-wait patience | Verified | Active service does not consume patience; exact deadline ordering is regression tested |
| Dynamic capacity reduction | Verified | Resource targets and tokens remain consistent |
| Machine failure and repair | Verified | Active-scan interruption, repair, restart behaviour, counts and unique downtime are covered |
| Maintenance policy | Verified | Fixed-duration-after-release and fixed-calendar-window behaviour are tested |
| Patient/report lifecycle | Verified | Scan completion, reporting completion and unfinished reporting are separated and reconciled |
| Dashboard semantics | Verified | Five transformation tests cover lifecycle, queues, reliability and state summaries |
| Paper scenario registry | Verified | All eleven registered paper scenarios validate and execute |
| Paper reproduction evidence | Verified | CI exports and validates the DOI, 11 scenario intentions, 46 replications, JSON manifest and published-target CSV |
| Distribution fitting | Verified | Information criteria and SciPy-compatible goodness-of-fit execution are tested |
| Strict test coverage | Verified | 91.88% whole-package coverage; minimum 80% enforced without core-engine omission |
| Static quality | Verified | Pre-commit, Ruff and configured MyPy checks pass |
| CLI and benchmarks | Verified | Four installed entry points and bounded benchmark workflows execute |
| Package integrity | Verified | Version 1.3.0 source and wheel distributions build and pass `twine check` |
| Clean wheel installation | Verified | Built wheel installs and executes in a new virtual environment |
| Dashboard deployment | Verified | Docker image starts; Streamlit health and dashboard endpoints respond |
| Independent observational validation | Protocol available | Requires authoritative observations not used for calibration |
| Statistical equivalence testing | Protocol available | Requires agreed target metrics, tolerances and replication count |
| Exact 2020-paper reproduction | Partially established | Published assumptions, controls, targets and scenario intentions are source-backed and machine-readable; bit-for-bit Simul8 equivalence is not claimed where proprietary event-calendar and random-stream details are unavailable |
| Local clinical pathway validation | Required before use | Clinical and operational experts must confirm pathways, priorities and service rules |
| Workforce and safety validation | Required before use | Local staffing constraints and safety rules must be independently approved |
| Economic optimisation validation | Required before use | Illustrative weights must be replaced with locally approved cost assumptions |
| Independent technical/domain review | Required for external assurance | Reviewer identities, findings and dispositions must be recorded |
| Formal GitHub release publication | Release-ready, administrative step pending | Create `v1.3.0`, attach CI-built artifacts and publish changelog |
| Production scheduling approval | Out of scope | The repository is a research and decision-support framework |

## Warning status

The latest verified pytest run reports **zero warnings**. The earlier date-format inference warning was removed through explicit mixed-format month parsing. The two earlier regular-expression capture-group warnings were removed by changing the MRI alternatives to non-capturing groups, with regression evidence confirming unchanged MRI modality selection.

## Architecture status

`healthcare_des.advanced_model` is the canonical public runtime. `advanced_engine` is retained as an explicit compatibility base for the 1.3.x line. It is not monkey-patched at import time. Consolidation or removal requires a major-version deprecation cycle and scenario-equivalence evidence; see `REPOSITORY_GAP_CLOSURE.md`.

MRI dispatch is now event-driven. Queue arrivals, scanner releases, maintenance transitions and failure/repair transitions notify the central dispatcher immediately. Patience expiry is ordered after normal same-timestamp release and dispatch events, so no polling interval or additional timing allowance is required. Boundary regressions verify release before a deadline, release exactly at a deadline and expiry when no scanner becomes available.

## Interpretation

### Software verification

Software verification asks whether the implementation behaves consistently with its stated logic. Core execution, advanced-engine regressions, event-driven dispatch, dashboard transformations, packaging, command-line interfaces, reproduction-evidence export and deployment pathways are covered by the automated quality gate.

### Model validation

Model validation asks whether the simulated system adequately represents a real service for an intended decision. This requires independent observations, locally agreed outcome measures, subject-matter review and documented acceptance thresholds.

### Paper reproduction

The repository now records the published DOI, 46-replication control, random seed, warm-up period, patient mix, distribution families, aggregate targets and all eleven scenario intentions in a validated machine-readable contract. CI exports the JSON manifest and published-target CSV and checks their essential contents.

This materially strengthens reproducibility, but it does not claim bit-for-bit equivalence with the original proprietary Simul8 implementation where exact event-calendar and random-stream details are unavailable.

## Minimum requirements before operational use

1. Confirm patient pathways and priority rules with clinical and operational experts.
2. Calibrate arrival, service, cancellation, no-show, abandonment and downtime distributions using approved evidence.
3. Validate against a locked holdout period or independent site-level observations.
4. Agree service-level, safety, workforce and cost constraints with accountable stakeholders.
5. Document uncertainty, sensitivity and failure-mode analysis.
6. Complete governance, privacy, safety and change-control review.
7. Obtain independent technical and healthcare-domain review with issue disposition.

See [VALIDATION.md](VALIDATION.md) for the empirical-validation protocol and [REPOSITORY_GAP_CLOSURE.md](REPOSITORY_GAP_CLOSURE.md) for the eight-point closure record.
