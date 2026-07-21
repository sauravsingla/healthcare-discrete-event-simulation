# Contributing

Thank you for helping improve this healthcare discrete-event simulation project.

## Development setup

```bash
git clone https://github.com/sauravsingla/healthcare-discrete-event-simulation.git
cd healthcare-discrete-event-simulation
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,analysis,dashboard]"
pre-commit install
```

## Workflow

1. Create a focused branch from `main`.
2. Keep each pull request limited to one coherent change.
3. Add or update tests for behavioural changes.
4. Run linting and tests locally.
5. Document new assumptions, data sources and limitations.

```bash
ruff check src tests scripts
pytest --cov=healthcare_des --cov-report=term-missing
```

## Research standards

- Use only public, synthetic or properly licensed data.
- Do not commit patient-level, confidential or employer-owned information.
- Distinguish reproduced findings from illustrative simulation results.
- Record seeds, configuration values and software versions for reproducibility.
- Cite external datasets, papers and software.

## Code style

- Target Python 3.10 or later.
- Prefer typed, testable functions with clear docstrings.
- Keep simulation assumptions configurable rather than hard-coded.
- Use deterministic seeds in tests.

## Pull requests

A strong pull request explains the problem, implementation, validation, assumptions and limitations. Screenshots or result tables are encouraged for dashboard or analysis changes.
