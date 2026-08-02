# Repository Maturity and Validation Programme

This document distinguishes completed engineering work from evidence-dependent research milestones. It prevents planned work from being described as already validated and gives contributors measurable acceptance criteria.

## Current strengths

- Tested Python package and command-line interfaces.
- Base and advanced discrete-event simulation engines.
- Deterministic replications and patient-accounting reconciliation.
- Capacity, staffing, maintenance, failure and repair modelling.
- Bootstrap summaries, sensitivity analysis and capacity search.
- Dashboard and Docker delivery.
- Python 3.10–3.12 continuous integration with an 80% coverage gate.
- Versioned official NHS aggregate-data benchmark evidence.
- Contributor, security, conduct, citation and data-governance documentation.

## Evidence boundaries

The official NHS benchmark validates the aggregate forecasting and evidence pipeline. It does not validate patient-level pathways, local waiting times, service-duration assumptions, clinical safety or production scheduling. The synthetic simulation benchmark verifies execution, accounting and scenario stability; it is not independent clinical evidence.

## Priority programme

### 1. Exact 2020-paper reproduction

Deliverables:

- authoritative transcription of every published scenario assumption;
- one versioned configuration per scenario;
- published-versus-reproduced result table;
- documented tolerances and replication counts;
- statistical-equivalence or discrepancy analysis;
- explicit explanation of unresolved source ambiguity.

Completion criterion: all eleven scenarios can be regenerated without guessed targets and each reported result is classified as reproduced, within tolerance, discrepant or not verifiable.

### 2. External validation of the simulation

Required evidence may include approved aggregate or de-identified observations for waiting time, throughput, utilisation, queue length, service duration, cancellation, no-show, turnaround and downtime.

Completion criterion: calibration and holdout periods are separated; acceptance thresholds are agreed before evaluation; observed-versus-simulated results and uncertainty intervals are published with governance approval.

### 3. Full static typing of core modules

Remove MyPy error suppressions progressively from the advanced engine, configuration, paper scenarios, reproduction, reporting and research-validation modules.

Completion criterion: core modules pass configured MyPy checks without module-wide `ignore_errors` overrides.

### 4. Immutable research releases

For each research release retain:

- source and wheel distributions;
- benchmark outputs and checksums;
- source manifest and retrieval dates;
- Python and dependency versions;
- container or lock-file identity;
- release notes and claim boundaries;
- a permanent software citation, preferably through an archival service.

### 5. One-command reproduction

Provide a documented command that rebuilds the environment, runs bounded reproducibility checks and verifies published output checksums without requiring private data.

### 6. Decision-model extensions

Future validated extensions include appointment templates, shift allocation, emergency reserve policies, maintenance scheduling, economic objectives, multi-modality pathways and multi-site networks.

## Acceptance standard

A research capability is complete only when code, tests, configuration, documentation, provenance, machine-readable outputs and interpretation agree. Operational recommendations require independent local validation, governance, safety review and accountable approval.