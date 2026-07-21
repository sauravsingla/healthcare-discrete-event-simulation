# Examples

This directory is for small, reproducible examples that demonstrate one capability at a time.

## Recommended environment

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

On Windows PowerShell, activate the environment with:

```powershell
.venv\Scripts\Activate.ps1
```

## Baseline simulation

Use the package API to run a short baseline experiment:

```python
from healthcare_des.model import ScenarioConfig, run_replications

config = ScenarioConfig(days=30, daily_demand=70)
summary = run_replications(config, replications=20)
print(summary)
```

Use multiple replications for reported results. A single stochastic run is useful for debugging, not for drawing conclusions.

## Synthetic demand

```python
from healthcare_des.synthetic import DemandPattern, generate_daily_demand

pattern = DemandPattern(days=30, base_daily_demand=70, seed=17)
demand = generate_daily_demand(pattern)
print(demand.head())
```

The generated data is privacy-safe and reproducible for a fixed seed.

## Capacity search

```python
from healthcare_des.model import ScenarioConfig
from healthcare_des.optimisation import search_capacity

base = ScenarioConfig(days=30, daily_demand=70)
ranked = search_capacity(
    base,
    mri_options=(1, 2, 3),
    radiographer_options=(1, 2, 3),
    radiologist_options=(1, 2),
    replications=10,
)
print(ranked.head())
```

The objective score is a scenario-ranking aid. Before operational use, review its weights and cost assumptions with domain experts.

## Sensitivity analysis

```python
from healthcare_des.model import ScenarioConfig
from healthcare_des.sensitivity import monte_carlo, one_at_a_time

base = ScenarioConfig(days=30, daily_demand=70)

local = one_at_a_time(base, replications=10)
uncertainty = monte_carlo(base, samples=100, replications=5, seed=11)

print(local)
print(uncertainty.describe())
```

## Reporting results

For any result shared publicly, record:

- code commit SHA;
- configuration values;
- input-data version;
- random seed;
- number of replications;
- Python version;
- execution date.

See `docs/VALIDATION.md` and `docs/DATASETS.md` for the validation and data-governance expectations.

## Interpretation

Examples are educational and research-oriented. They do not constitute clinical guidance, operational guarantees or a validated representation of any specific healthcare provider.
