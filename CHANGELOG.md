# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog, and the project intends to follow Semantic Versioning once stable releases begin.

## [Unreleased]

### Added

- Discrete-event MRI patient-flow simulation built with SimPy.
- Priority-aware patient routing and constrained scanner and staff resources.
- Repeated stochastic simulation and aggregate KPI summaries.
- Synthetic daily MRI demand generation with reproducible random seeds.
- Capacity-search utilities for scanner, radiographer and radiologist scenarios.
- One-at-a-time sensitivity analysis and Monte Carlo uncertainty analysis.
- Streamlit dashboard entry point.
- Docker support and automated quality checks.
- Unit tests for extension modules and seeded reproducibility.
- Contributor, security, architecture, validation, data-governance and roadmap documentation.
- GitHub issue and pull-request templates.

### Changed

- Expanded continuous integration across Python 3.10, 3.11 and 3.12.
- Added Ruff linting and test coverage reporting to CI.

### Known limitations

- Published benchmark results have not yet been frozen as a versioned release artifact.
- External validation against a specific healthcare provider requires an independently governed dataset and documented calibration process.
- Scenario rankings depend on model assumptions and objective weights and should not be treated as operational recommendations without expert review.

## Release process

Before creating the first tagged release:

1. Confirm CI passes on every supported Python version.
2. Run and archive the baseline experiment.
3. Record dependencies, seeds and configuration values.
4. Update this changelog with the release date.
5. Create a version tag and release notes.
6. Attach or link reproducible output artifacts.

[Unreleased]: https://github.com/sauravsingla/healthcare-discrete-event-simulation/commits/main
