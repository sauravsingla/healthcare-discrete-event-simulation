# Changelog

All notable changes to this project are documented here.

The format follows Keep a Changelog principles and the project uses semantic versioning.

## [Unreleased]

### Added

- Installed `healthcare-des-advanced-benchmark` command.
- Branch coverage configuration and strict pytest configuration.
- Expanded package classifiers and project links.

### Changed

- Corrected contributor installation and verification instructions.
- Strengthened package metadata for built distributions.

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

[Unreleased]: https://github.com/sauravsingla/healthcare-discrete-event-simulation/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/sauravsingla/healthcare-discrete-event-simulation/releases/tag/v0.4.0
