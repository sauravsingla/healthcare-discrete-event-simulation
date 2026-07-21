"""Synthetic patient-demand generation for reproducible MRI experiments."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DemandPattern:
    days: int = 30
    base_daily_demand: float = 70.0
    weekday_multiplier: float = 1.15
    weekend_multiplier: float = 0.75
    monday_multiplier: float = 1.20
    trend_per_day: float = 0.002
    seed: int = 17


def generate_daily_demand(pattern: DemandPattern = DemandPattern()) -> pd.DataFrame:
    """Generate a privacy-safe daily MRI demand series.

    The generator includes weekday/weekend effects, a Monday surge, a small
    deterministic trend and Poisson demand noise. It is suitable for examples,
    tests and scenario analysis where real patient-level data cannot be shared.
    """
    if pattern.days <= 0 or pattern.base_daily_demand <= 0:
        raise ValueError("days and base_daily_demand must be positive")

    rng = np.random.default_rng(pattern.seed)
    dates = pd.date_range("2024-01-01", periods=pattern.days, freq="D")
    expected: list[float] = []

    for index, date in enumerate(dates):
        multiplier = pattern.weekday_multiplier if date.dayofweek < 5 else pattern.weekend_multiplier
        if date.dayofweek == 0:
            multiplier *= pattern.monday_multiplier
        expected.append(pattern.base_daily_demand * multiplier * (1 + pattern.trend_per_day * index))

    demand = rng.poisson(np.asarray(expected, dtype=float))
    return pd.DataFrame(
        {
            "date": dates,
            "expected_demand": expected,
            "observed_demand": demand,
            "is_weekend": dates.dayofweek >= 5,
            "day_of_week": dates.day_name(),
        }
    )
