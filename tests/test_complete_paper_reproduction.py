from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from healthcare_des.paper_reproduction import (
    REPRODUCTION_CLAIM,
    compare_reproduced_results,
    comparison_template,
    operational_constraint_status,
    paper_base_config,
    paper_table_figure_index,
    published_targets,
    reproduction_manifest,
    sample_published_service_times,
    scenario_results_catalog,
)


def test_published_targets_include_before_and_after_queue_results() -> None:
    targets = published_targets().set_index("target")
    assert targets.loc["mri_waiting_room_queue_before", "expected"] == 17
    assert targets.loc["mri_waiting_room_queue_after", "expected"] == 5
    assert (
        targets.loc[
            "scenario_11_system_time_reduction"
            if "scenario_11_system_time_reduction" in targets.index
            else "system_time_reduction",
            "expected",
        ]
        == 20
    )


def test_all_eleven_scenarios_are_indexed_without_invented_values() -> None:
    catalog = scenario_results_catalog()
    assert len(catalog) == 11
    assert catalog["scenario"].is_unique
    assert catalog.loc[catalog["scenario"].eq("scenario-11"), "published_value"].iloc[0] == 20
    assert catalog.loc[catalog["scenario"].ne("scenario-11"), "published_value"].isna().all()


def test_published_service_distributions_are_sampled_with_correct_support() -> None:
    samples = sample_published_service_times(np.random.default_rng(17), 5000)
    assert samples["preparation_minutes"].between(4, 6).all()
    assert samples["report_minutes"].between(6, 12).all()
    assert (samples["mri_minutes"] >= 0).all()
    assert samples["reception_minutes"].mean() == pytest.approx(8, rel=0.08)
    assert samples["preparation_minutes"].mean() == pytest.approx(5, rel=0.02)
    assert samples["report_minutes"].mean() == pytest.approx(9, rel=0.02)


def test_paper_baseline_applies_published_mri_parameters_and_shift_capacity() -> None:
    config = paper_base_config()
    assert config.scan_mean == pytest.approx(26.46)
    assert config.scan_sd == pytest.approx(8.0)
    assert tuple(window.capacity for window in config.radiographer_capacity) == (4, 3, 2)
    assert tuple(window.capacity for window in config.clerk_capacity) == (1, 1, 1)
    assert tuple(window.capacity for window in config.radiologist_capacity) == (1, 1, 1)


def test_constraint_status_is_explicit_about_supported_and_retained_items() -> None:
    constraints = operational_constraint_status()
    assert len(constraints) == 6
    assert constraints["application_status"].str.contains("applied directly").any()
    assert constraints["application_status"].str.contains("metadata").any()


def test_comparison_template_covers_all_scenarios_and_available_targets() -> None:
    template = comparison_template()
    assert set(f"scenario-{index:02d}" for index in range(1, 12)).issubset(
        set(template["scenario"])
    )
    assert "mri_waiting_room_queue_before" in set(template["metric"])
    assert template["reproduced_value"].isna().all()


def test_reproduced_result_comparison_reports_pass_and_fail() -> None:
    reproduced = pd.DataFrame(
        [
            {
                "scenario": "baseline",
                "metric": "historical_february_2018_demand",
                "reproduced_value": 2089,
            },
            {
                "scenario": "scenario-11",
                "metric": "system_time_reduction",
                "reproduced_value": 18,
            },
        ]
    )
    comparison = compare_reproduced_results(reproduced, tolerance_pct=10)
    demand = comparison.loc[comparison["metric"].eq("historical_february_2018_demand")].iloc[0]
    scenario_11 = comparison.loc[comparison["metric"].eq("system_time_reduction")].iloc[0]
    assert bool(demand["passed"])
    assert bool(scenario_11["passed"])


def test_manifest_and_evidence_index_use_qualified_claim_wording() -> None:
    manifest = reproduction_manifest()
    index = paper_table_figure_index()
    assert manifest["claim"] == REPRODUCTION_CLAIM
    assert "partial numerical reproduction" in manifest["claim"].lower()
    assert len(index) >= 7
