"""Lightweight capacity optimisation built on top of the simulation model."""

from __future__ import annotations

from dataclasses import asdict, replace
from itertools import product

import pandas as pd

from .model import ScenarioConfig, run_replications, summarise


def _validate_positive_options(name: str, values: tuple[int, ...]) -> None:
    if not values:
        raise ValueError(f"{name} must contain at least one option")
    if any(value <= 0 for value in values):
        raise ValueError(f"{name} options must be positive integers")


def search_capacity(
    base: ScenarioConfig,
    mri_options: tuple[int, ...] = (2, 3, 4, 5),
    radiographer_options: tuple[int, ...] = (2, 3, 4, 5, 6),
    radiologist_options: tuple[int, ...] = (1, 2),
    replications: int = 8,
    target_wait_minutes: float = 20.0,
) -> pd.DataFrame:
    """Evaluate feasible capacity combinations and rank them by service and cost.

    The score is intentionally transparent: estimated staffing/machine cost plus
    a penalty whenever average waiting time exceeds the target. This makes the
    method easy to audit and replace with organisation-specific cost weights.
    """
    base.validate()
    _validate_positive_options("mri_options", mri_options)
    _validate_positive_options("radiographer_options", radiographer_options)
    _validate_positive_options("radiologist_options", radiologist_options)
    if replications <= 0:
        raise ValueError("replications must be positive")
    if target_wait_minutes < 0:
        raise ValueError("target_wait_minutes must be non-negative")

    rows: list[dict[str, float | int | str]] = []
    for machines, radiographers, radiologists in product(
        mri_options, radiographer_options, radiologist_options
    ):
        config = replace(
            base,
            name=f"mri{machines}-rg{radiographers}-rl{radiologists}",
            mri_machines=machines,
            radiographers=radiographers,
            radiologists=radiologists,
        )
        summary = summarise(run_replications(config, replications=replications))
        estimated_cost = machines * 12.0 + radiographers * 3.0 + radiologists * 5.0
        wait_penalty = max(0.0, summary["mean_wait_minutes"] - target_wait_minutes) * 4.0
        rows.append(
            {
                **asdict(config),
                **summary,
                "estimated_capacity_cost": estimated_cost,
                "wait_penalty": wait_penalty,
                "objective_score": estimated_cost + wait_penalty,
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["objective_score", "mean_wait_minutes", "throughput_per_day"],
        ascending=[True, True, False],
    ).reset_index(drop=True)
