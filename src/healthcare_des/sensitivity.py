"""Sensitivity and uncertainty analysis for healthcare capacity scenarios."""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pandas as pd

from .model import ScenarioConfig, run_replications, summarise


def one_at_a_time(
    base: ScenarioConfig,
    demand_multipliers: tuple[float, ...] = (0.8, 1.0, 1.2, 1.4),
    no_show_rates: tuple[float, ...] = (0.0, 0.08, 0.15),
    replications: int = 10,
) -> pd.DataFrame:
    """Measure KPI response to demand and no-show assumptions."""
    base.validate()
    if not demand_multipliers and not no_show_rates:
        raise ValueError("At least one sensitivity value must be provided")
    if any(multiplier <= 0 for multiplier in demand_multipliers):
        raise ValueError("demand_multipliers must be positive")
    if any(not 0 <= rate < 1 for rate in no_show_rates):
        raise ValueError("no_show_rates must be in [0, 1)")
    if replications <= 0:
        raise ValueError("replications must be positive")

    rows: list[dict[str, float | str]] = []
    for multiplier in demand_multipliers:
        config = replace(
            base,
            name=f"demand-{multiplier:.2f}",
            daily_demand=base.daily_demand * multiplier,
        )
        rows.append(
            {
                "factor": "daily_demand",
                "value": multiplier,
                **summarise(run_replications(config, replications)),
            }
        )

    for rate in no_show_rates:
        config = replace(base, name=f"no-show-{rate:.2f}", no_show_rate=rate)
        rows.append(
            {
                "factor": "no_show_rate",
                "value": rate,
                **summarise(run_replications(config, replications)),
            }
        )

    return pd.DataFrame(rows)


def monte_carlo(
    base: ScenarioConfig,
    samples: int = 50,
    replications: int = 4,
    seed: int = 2024,
) -> pd.DataFrame:
    """Propagate uncertainty in demand, no-shows and scan duration.

    Parameter ranges are illustrative and should be replaced with locally
    validated estimates before operational use.
    """
    base.validate()
    if samples <= 0:
        raise ValueError("samples must be positive")
    if replications <= 0:
        raise ValueError("replications must be positive")

    rng = np.random.default_rng(seed)
    rows: list[dict[str, float | int]] = []
    for sample in range(samples):
        config = replace(
            base,
            name=f"mc-{sample:03d}",
            daily_demand=max(1.0, float(rng.normal(base.daily_demand, base.daily_demand * 0.12))),
            no_show_rate=float(rng.uniform(0.03, 0.15)),
            scan_mean=max(5.0, float(rng.normal(base.scan_mean, 3.0))),
            seed=base.seed + sample * 100,
        )
        rows.append(
            {
                "sample": sample,
                "daily_demand": config.daily_demand,
                "no_show_rate": config.no_show_rate,
                "scan_mean": config.scan_mean,
                **summarise(run_replications(config, replications)),
            }
        )
    return pd.DataFrame(rows)
