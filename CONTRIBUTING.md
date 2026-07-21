# Contributing

Thank you for helping improve this healthcare discrete-event simulation project.

## Development setup

```bash
git clone https://github.com/sauravsingla/healthcare-discrete-event-simulation.git
cd healthcare-discrete-event-simulation
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -e ".[dev,dashboard]"
```

## Workflow

1. Create a focused branch from `main`.
2. Keep each pull request limited to one coherent change.
3. Add or update deterministic tests for behavioural changes.
4. Run the complete local verification suite.
5. Document new assumptions, data sources and limitations.

```bash
ruff check src tests scripts examples
mypy src/healthcare_des
pytest --cov=healthcare_des --cov-report=term-missing --cov-fail-under=80
python -m build
twine check dist/*
```

## Simulation-change requirements

Changes to patient flow, capacity, machine state, demand generation or KPI definitions must include:

- a deterministic regression test;
- an explanation of the operational assumption;
- confirmation that patient outcomes reconcile;
- confirmation that waiting and system-time definitions remain consistent;
- documentation of any effect on paper-scenario comparisons.

## Research standards

- Use only public, synthetic or properly licensed data.
- Do not commit patient-level, confidential or employer-owned information.
- Distinguish reproduced findings from illustrative simulation results.
- Record seeds, configuration values, termination policy and software versions.
- Cite external datasets, papers and software.
- Do not claim paper reproduction unless the requirements in `docs/VALIDATION.md` are met.

## Code style

- Target Python 3.10 or later.
- Prefer typed, testable functions with clear docstrings.
- Keep simulation assumptions configurable rather than hard-coded.
- Use deterministic seeds in tests.

## Pull requests

A strong pull request explains the problem, implementation, validation, assumptions and limitations. Include result tables for changes that affect model outputs.
