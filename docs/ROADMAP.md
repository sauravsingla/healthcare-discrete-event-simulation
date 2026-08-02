# Research Roadmap

This roadmap separates completed capabilities from evidence-dependent research milestones. The project prioritises validated, reproducible improvements over feature count.

## Completed foundation

- Base and advanced MRI discrete-event simulation engines.
- Explicit patient lifecycle, queueing and outcome reconciliation.
- Outpatient, inpatient and emergency pathways.
- Hourly and calendar-aware demand profiles.
- Dynamic staffing and operating windows.
- Maintenance, stochastic machine failure, repair and optional scan restart.
- Resource-utilisation and system-state observations.
- Replications, bootstrap summaries, sensitivity analysis and capacity search.
- Reproducible synthetic demand-capacity benchmark.
- Official NHS aggregate-data acquisition, provenance and external forecasting benchmark.
- Python package, command-line applications, dashboard, Docker image and multi-version CI.
- Contributor, security, conduct, citation, changelog and data-governance documentation.

## Current priorities

### Exact 2020-paper reproduction

- Transcribe all authoritative scenario inputs and result targets.
- Produce one versioned configuration per published scenario.
- Compare published and reproduced outcomes with documented tolerances.
- Resolve or explicitly record incomplete source assumptions.

### External simulation validation

- Calibrate service-time, waiting-time, throughput, utilisation and queue behaviour using approved evidence.
- Separate calibration and holdout periods.
- Publish observed-versus-simulated results with uncertainty and pre-agreed acceptance thresholds.

### Engineering hardening

- Remove module-wide MyPy suppressions from core simulation and research modules.
- Add an exact dependency lock for published benchmark environments.
- Provide one-command reproduction and checksum verification.
- Publish tagged software releases with immutable benchmark evidence and an archival software citation.

## Medium-term research

- Appointment-template and shift-allocation optimisation.
- Emergency-reserve and maintenance-window policies.
- Cost, workforce and service-level objectives.
- Formal parameter and structural uncertainty analysis.
- CT and ultrasound pathways through reusable modality definitions.

## Longer-term research

- Multi-site radiology networks and patient transfers.
- Forecast-driven capacity planning with probabilistic intervals.
- Policy learning for appointment, staffing and prioritisation decisions.
- Calibrated healthcare digital-twin workflows using approved operational data.
- Independent external review with healthcare operations researchers.

## Acceptance criteria

A roadmap item is complete only when it includes tests, documentation, explicit assumptions, reproducible configuration, provenance, machine-readable outputs and clearly labelled interpretation. Research findings must not be presented as operational recommendations without independent validation, governance and accountable approval.

See [`REPOSITORY_MATURITY.md`](REPOSITORY_MATURITY.md) for detailed deliverables and claim boundaries.