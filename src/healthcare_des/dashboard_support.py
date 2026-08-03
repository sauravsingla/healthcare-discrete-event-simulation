"""Pure helpers used by the Streamlit dashboard and dashboard regression tests."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

import pandas as pd

from .advanced_model import AdvancedSimulationResult


def advanced_kpis(result: AdvancedSimulationResult) -> dict[str, float | int]:
    """Return the advanced lifecycle and reliability KPIs shown in the dashboard."""
    return {
        "booked": result.booked,
        "arrivals": result.arrivals,
        "completed": result.completed,
        "abandoned": result.abandoned,
        "unfinished": result.unfinished,
        "completion_rate_pct": result.completion_rate_pct,
        "mean_wait_minutes": result.mean_wait_minutes,
        "mean_system_minutes": result.mean_system_minutes,
        "mean_queue_length_open": result.mean_queue_length_open,
        "mean_queue_length_24h": result.mean_queue_length_24h,
        "max_queue_length": result.max_queue_length,
        "mri_failures": result.mri_failures,
        "mri_downtime_minutes": result.mri_downtime_minutes,
        "mean_available_mri_open": result.mean_available_mri_open,
        "mean_available_mri_24h": result.mean_available_mri_24h,
    }


def queue_summary(state: pd.DataFrame) -> pd.DataFrame:
    """Summarise explicit queue observations by patient type."""
    columns = [
        "mri_queue",
        "mri_queue_emergency",
        "mri_queue_inpatient",
        "mri_queue_outpatient",
    ]
    labels = ["Total", "Emergency", "Inpatient", "Outpatient"]
    if state.empty:
        return pd.DataFrame({"queue": labels, "mean": 0.0, "maximum": 0}).set_index("queue")
    available = [column for column in columns if column in state]
    means = state[available].mean().reindex(columns, fill_value=0.0)
    maxima = state[available].max().reindex(columns, fill_value=0).astype(int)
    return pd.DataFrame(
        {"queue": labels, "mean": means.to_numpy(), "maximum": maxima.to_numpy()}
    ).set_index("queue")


def lifecycle_summary(patients: pd.DataFrame) -> pd.DataFrame:
    """Return patient and reporting lifecycle counts for display."""
    if patients.empty:
        return pd.DataFrame(columns=["status", "count"]).set_index("status")
    status = patients["status"].fillna("unfinished").value_counts()
    report = (
        patients.get("report_status", pd.Series(index=patients.index, dtype="object"))
        .fillna("not_applicable")
        .value_counts()
    )
    rows: list[dict[str, Any]] = [
        {"status": f"patient:{name}", "count": int(value)} for name, value in status.items()
    ]
    rows.extend({"status": f"report:{name}", "count": int(value)} for name, value in report.items())
    return pd.DataFrame(rows).set_index("status")


def result_frame(result: AdvancedSimulationResult) -> pd.DataFrame:
    """Convert a result dataclass to a one-row dataframe for export/display."""
    return pd.DataFrame([asdict(result)])
