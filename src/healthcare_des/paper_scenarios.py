"""Published-scenario registry and tolerance-based reproduction runner."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Mapping

import pandas as pd

from .advanced_model import AdvancedScenarioConfig, run_advanced_replications, summarise_advanced


# Scenario names mirror the eleven operational comparisons described in the paper.
# Expected metrics should be supplied from the paper evidence CSV rather than invented.
PAPER_SCENARIOS: dict[str, dict[str, object]] = {
    "scenario-01-baseline": {},
    "scenario-02-extra-mri": {"mri_machines": 5},
    "scenario-03-extra-radiographer": {"radiographer_capacity": ((0, 480, 2),)},
    "scenario-04-extra-radiologist": {"radiologist_capacity": ((0, 480, 2),)},
    "scenario-05-extended-hours": {
        "operating_hours": 12,
        "outpatient_hourly_profile": (
            1.2,
            1.3,
            1.1,
            0.8,
            0.7,
            1.1,
            1.0,
            0.8,
            0.6,
            0.5,
            0.4,
            0.3,
        ),
    },
    "scenario-06-reduced-demand": {"daily_demand": 56.0},
    "scenario-07-increased-demand": {"daily_demand": 84.0},
    "scenario-08-low-no-show": {"no_show_rate": 0.04},
    "scenario-09-overbooking": {"overbooking_rate": 0.10},
    "scenario-10-staggered-staff": {},
    "scenario-11-resilient-mri": {"mri_machines": 5},
}


def _coerce_windows(changes: Mapping[str, object]) -> dict[str, object]:
    """Convert compact tuple definitions into dataclass windows lazily."""
    from .advanced_model import CapacityWindow

    converted = dict(changes)
    for field in ("clerk_capacity", "radiographer_capacity", "radiologist_capacity"):
        if field in converted:
            converted[field] = tuple(CapacityWindow(*row) for row in converted[field])
    return converted


def run_paper_scenarios(
    base: AdvancedScenarioConfig,
    replications: int = 20,
    scenarios: Mapping[str, Mapping[str, object]] | None = None,
) -> pd.DataFrame:
    selected = PAPER_SCENARIOS if scenarios is None else scenarios
    rows: list[dict[str, float | str]] = []
    for name, changes in selected.items():
        config = replace(base, name=name, **_coerce_windows(changes))
        config.validate()
        summary = summarise_advanced(run_advanced_replications(config, replications))
        rows.append({"name": name, **summary})
    return pd.DataFrame(rows)


def verify_paper_targets(
    results: pd.DataFrame,
    targets_path: str | Path,
    default_tolerance_pct: float = 10.0,
) -> pd.DataFrame:
    """Compare reproduced metrics with externally transcribed paper targets.

    Required target columns: scenario, metric, expected. Optional: tolerance_pct.
    This design prevents the repository from silently inventing published values.
    """
    targets = pd.read_csv(targets_path)
    required = {"scenario", "metric", "expected"}
    missing = required - set(targets.columns)
    if missing:
        raise ValueError(f"Missing paper target columns: {', '.join(sorted(missing))}")
    indexed = results.set_index("name")
    checks: list[dict[str, object]] = []
    for row in targets.itertuples(index=False):
        scenario = str(row.scenario)
        metric = str(row.metric)
        if scenario not in indexed.index or metric not in indexed.columns:
            raise ValueError(f"Unknown paper target: {scenario}/{metric}")
        observed = float(indexed.loc[scenario, metric])
        expected = float(row.expected)
        tolerance = float(getattr(row, "tolerance_pct", default_tolerance_pct))
        error_pct = (
            abs(observed - expected) / abs(expected) * 100 if expected else abs(observed) * 100
        )
        checks.append(
            {
                "scenario": scenario,
                "metric": metric,
                "expected": expected,
                "observed": observed,
                "error_pct": error_pct,
                "tolerance_pct": tolerance,
                "passed": error_pct <= tolerance,
            }
        )
    return pd.DataFrame(checks)
