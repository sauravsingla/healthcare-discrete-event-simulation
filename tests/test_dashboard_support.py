from __future__ import annotations

from dataclasses import replace

import pandas as pd

from healthcare_des import AdvancedScenarioConfig, run_advanced_once
from healthcare_des.dashboard_support import (
    advanced_kpis,
    lifecycle_summary,
    queue_summary,
    result_frame,
)


def _run_small_advanced_case():
    config = replace(
        AdvancedScenarioConfig(),
        days=1,
        warmup_days=0,
        daily_demand=8,
        mri_machines=2,
        bootstrap_samples=20,
        seed=31,
    )
    return run_advanced_once(config)


def test_advanced_dashboard_kpis_reconcile_lifecycle():
    result, _, _ = _run_small_advanced_case()
    kpis = advanced_kpis(result)
    assert kpis["arrivals"] == kpis["completed"] + kpis["abandoned"] + kpis["unfinished"]
    assert kpis["max_queue_length"] >= 0
    assert kpis["mri_downtime_minutes"] >= 0


def test_queue_summary_exposes_all_patient_types():
    _, _, state = _run_small_advanced_case()
    summary = queue_summary(state)
    assert list(summary.index) == ["Total", "Emergency", "Inpatient", "Outpatient"]
    assert (summary["mean"] >= 0).all()
    assert (summary["maximum"] >= 0).all()


def test_queue_summary_handles_empty_state():
    summary = queue_summary(pd.DataFrame())
    assert summary["mean"].sum() == 0
    assert summary["maximum"].sum() == 0


def test_lifecycle_summary_includes_patient_and_report_statuses():
    _, patients, _ = _run_small_advanced_case()
    summary = lifecycle_summary(patients)
    assert any(index.startswith("patient:") for index in summary.index)
    assert any(index.startswith("report:") for index in summary.index)
    assert int(summary["count"].sum()) >= len(patients)


def test_result_frame_is_one_row_and_exportable():
    result, _, _ = _run_small_advanced_case()
    frame = result_frame(result)
    assert len(frame) == 1
    assert frame.loc[0, "scenario"] == result.scenario
