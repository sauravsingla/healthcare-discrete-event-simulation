"""Automated reproduction checks against published research targets."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .benchmark import benchmark_scenarios
from .model import ScenarioConfig


@dataclass(frozen=True)
class ReproductionTarget:
    scenario: str
    metric: str
    expected: float
    tolerance: float


DEFAULT_TARGETS = (
    ReproductionTarget("baseline", "mean_wait_minutes", 17.0, 12.0),
    ReproductionTarget("extra-mri", "mean_wait_minutes", 5.0, 10.0),
)


def verify_targets(
    results: pd.DataFrame,
    targets: tuple[ReproductionTarget, ...] = DEFAULT_TARGETS,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    indexed = results.set_index("name")
    for target in targets:
        if target.scenario not in indexed.index:
            rows.append(
                {
                    "scenario": target.scenario,
                    "metric": target.metric,
                    "expected": target.expected,
                    "actual": float("nan"),
                    "absolute_error": float("nan"),
                    "tolerance": target.tolerance,
                    "passed": False,
                    "reason": "scenario missing",
                }
            )
            continue
        if target.metric not in indexed.columns:
            raise ValueError(f"Metric is not available: {target.metric}")
        actual = float(indexed.loc[target.scenario, target.metric])
        absolute_error = abs(actual - target.expected)
        rows.append(
            {
                "scenario": target.scenario,
                "metric": target.metric,
                "expected": target.expected,
                "actual": actual,
                "absolute_error": absolute_error,
                "tolerance": target.tolerance,
                "passed": absolute_error <= target.tolerance,
                "reason": "within tolerance"
                if absolute_error <= target.tolerance
                else "outside tolerance",
            }
        )
    return pd.DataFrame(rows)


def reproduce_paper(
    base: ScenarioConfig,
    *,
    replications: int = 50,
    targets: tuple[ReproductionTarget, ...] = DEFAULT_TARGETS,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    results = benchmark_scenarios(base, replications=replications)
    checks = verify_targets(results, targets)
    return results, checks
