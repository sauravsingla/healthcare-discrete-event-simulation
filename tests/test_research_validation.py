from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from healthcare_des.research_validation import (
    confidence_interval,
    equivalence_report,
    fit_distributions,
    fit_hourly_profile,
)


def test_fit_hourly_profile_uses_observed_counts() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": [
                "2026-01-01 08:00",
                "2026-01-01 08:15",
                "2026-01-01 09:00",
            ],
            "count": [3, 1, 2],
        }
    )
    profile = fit_hourly_profile(frame, count_column="count", operating_hours=10, smoothing=0)
    assert len(profile) == 10
    assert sum(profile) == pytest.approx(1.0)
    assert profile[8] == pytest.approx(4 / 6)
    assert profile[9] == pytest.approx(2 / 6)


def test_confidence_interval_contains_mean() -> None:
    values = [9.0, 10.0, 11.0, 10.5]
    low, high = confidence_interval(values)
    assert low < np.mean(values) < high


def test_equivalence_report_detects_close_samples() -> None:
    observed = [10.0, 10.2, 9.8, 10.1, 9.9, 10.05, 9.95, 10.0]
    reference = [10.1, 10.0, 9.9, 10.05, 9.95, 10.0, 10.1, 9.9]
    report = equivalence_report(observed, reference, equivalence_margin=0.5)
    assert report["equivalent"] is True
    assert abs(float(report["cohens_d"])) < 0.5
    assert 0 <= float(report["ks_pvalue"]) <= 1


def test_fit_distributions_returns_information_criteria() -> None:
    rng = np.random.default_rng(4)
    values = rng.exponential(8.0, 250)
    report = fit_distributions(values, candidates=("expon", "norm"))
    assert set(["aic", "bic", "ks_pvalue", "anderson_darling"]).issubset(report.columns)
    assert report.iloc[0]["distribution"] == "expon"


def test_profile_rejects_bad_timestamps() -> None:
    with pytest.raises(ValueError, match="invalid"):
        fit_hourly_profile(pd.DataFrame({"timestamp": ["not-a-date"]}))
