## Summary

Explain the problem, why it matters, and the implemented change.

## Type of change

- [ ] Simulation behaviour
- [ ] Data preparation or calibration
- [ ] Optimisation or sensitivity analysis
- [ ] Dashboard or visualisation
- [ ] Documentation
- [ ] Tests, CI, packaging or maintenance

## Validation

- [ ] `pre-commit run --all-files` passes
- [ ] `ruff check src tests scripts examples` passes
- [ ] `mypy src` passes
- [ ] `pytest --cov=healthcare_des --cov-report=term-missing` passes
- [ ] `python -m build` and `twine check dist/*` pass when packaging is affected
- [ ] New behaviour has deterministic regression tests
- [ ] Public CLI or configuration changes have smoke-test coverage

## Simulation integrity

- [ ] Patient outcomes reconcile: arrivals = completed + abandoned + unfinished
- [ ] Queue, resource and lifecycle metrics remain internally consistent
- [ ] Seeds, horizons, warm-up periods and termination rules are documented
- [ ] Configuration assumptions and units are explicit
- [ ] Backwards compatibility has been considered

## Research and data integrity

- [ ] No confidential, employer-owned or patient-identifiable data is included
- [ ] External datasets, papers and software are cited
- [ ] Illustrative results are clearly distinguished from reproduced findings
- [ ] Calibration and validation evidence are not conflated
- [ ] Assumptions, uncertainty and limitations are described

## Results

Include relevant metrics, tables, logs or screenshots. Do not include sensitive information.

## Checklist

- [ ] The change is focused and documented
- [ ] User-facing documentation and changelog entries are updated where needed
- [ ] Commit messages describe the implemented changes
- [ ] Generated files, caches, credentials and local environment artifacts are excluded
