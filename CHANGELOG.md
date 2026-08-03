# Changelog

All notable changes to this project are documented here.

The format follows Keep a Changelog principles and the project uses semantic versioning.

## [Unreleased]

### Added

- Patient-level calibration, clinical validation and independent operational review remain planned external activities.

## [1.3.0] - 2026-08-03

### Added

- System-wide MRI priority dispatch with emergency, inpatient and outpatient ordering.
- FIFO dispatch within each priority class and explicit queue measurements by patient type.
- Urgent-aware runtime MRI capacity reservation.
- Queue-wait-only abandonment semantics.
- Separate MRI scan-completion and reporting-completion lifecycle states.
- Explicit maintenance-window policies and unique overlapping-downtime accounting.
- Repeated failure, repair and optional scan-restart handling.
- Import-order-independent public advanced simulation runtime.
- Dashboard views for advanced lifecycle, queue, failure and downtime metrics.
- Testable dashboard transformation helpers and dashboard semantic regression tests.
- Whole-package coverage enforcement and expanded concurrency, boundary and analytical tests.
- Versioned capability and verification results in the README.

### Changed

- Package metadata now uses an SPDX licence expression.
- Package version increased from 1.2.0 to 1.3.0.
- The README distinguishes software verification, aggregate NHS forecasting evidence and local clinical validation.

### Verified baseline before the dashboard additions

- Python 3.10, 3.11 and 3.12 CI jobs.
- 188 tests passed.
- 84.68% whole-package branch coverage.
- Wheel and source-distribution build, metadata checks and clean-wheel installation.
- Four installed CLI entry points.
- Docker image build and Streamlit health endpoint.

### Validation and claim limits

- Public NHS inputs are aggregate operational data, not patient-level data.
- Patient-level calibration, clinical safety validation and local operational approval require authoritative local evidence and domain review.

## [1.2.0] - 2026-07-30

### Added

- Official NHS public-source manifest covering six versioned releases.
- Provenance-tracked acquisition with SHA-256 checksums and safe ZIP extraction.
- DM01 provider-month MRI activity preparation.
- DID MRI activity, patient-source and turnaround ingestion.
- NIDC MRI scanner asset integration and per-scanner benchmarking.
- NHS imaging workforce integration and workforce-normalised metrics.
- Leakage-free provider-level temporal holdout scoring.
- Reproducible real-data benchmark runner with CSV, JSON and Markdown outputs.
- End-to-end GitHub Actions workflow for official NHS MRI benchmark execution.
- Schema inventory, failure diagnostics and derived benchmark workflow artifacts.
- README documentation distinguishing synthetic benchmark results from official NHS multi-source benchmark capability.

### Changed

- Strengthened dynamic capacity accounting and MRI failure/repair behaviour.
- Restored the strict 80% test-coverage gate without test deselection.
- Expanded regression coverage across Python 3.10, 3.11 and 3.12.
- Added `openpyxl` as a runtime dependency for official NHS Excel workbooks.
- Upgraded the release workflow to create a GitHub Release and attach source and wheel distributions for version tags.
- Increased the package version from 1.1.0 to 1.2.0.

### Validation and claim limits

- Public NHS inputs are aggregate operational data, not patient-level data.
- NHS benchmarking is external operational evaluation and is not clinical validation or causal inference.
- Quantitative NHS result claims should cite retained `run_metadata.json`, `provider_scores.csv` and `benchmark_report.md` artifacts.

## [0.4.0] - 2026-07-21

### Added

- Corrected advanced MRI discrete-event simulation engine.
- Explicit patient lifecycle and outcome reconciliation.
- Stage-specific wait, service and system-time accounting.
- Dynamic staffing windows and MRI machine state tracking.
- Maintenance, failure, repair and bounded-drain handling.
- Hourly outpatient and emergency demand profiles.
- Calendar-aware weekday and seasonal demand.
- Bootstrap confidence intervals.
- Advanced regression tests, workflow example and scaling benchmark.
- CI and release-build workflows.
- Contributor, security, architecture, validation and data-governance documentation.

### Changed

- `advanced_model` exposes the corrected advanced implementation while preserving public imports.
- Package version increased to 0.4.0.
- CI expanded across Python 3.10, 3.11 and 3.12.

### Known evidence-dependent limitations

- Paper scenario targets require authoritative transcription.
- Scenario 10 staffing details require source confirmation.
- External holdout validation requires an appropriate governed dataset.

## Release process

Before creating a tagged release:

1. Confirm CI passes on every supported Python version.
2. Run and archive the baseline and advanced benchmark experiments.
3. Record dependencies, seeds, configurations and termination policies.
4. Update this changelog with the release date.
5. Create a version tag and release notes.
6. Attach or link reproducible output artifacts.

[Unreleased]: https://github.com/sauravsingla/healthcare-discrete-event-simulation/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/sauravsingla/healthcare-discrete-event-simulation/compare/v1.2.0...v1.3.0
[1.2.0]: https://github.com/sauravsingla/healthcare-discrete-event-simulation/compare/v1.1.0...v1.2.0
[0.4.0]: https://github.com/sauravsingla/healthcare-discrete-event-simulation/releases/tag/v0.4.0
