"""Interactive dashboard for exploring MRI demand and capacity scenarios."""

from dataclasses import replace

import pandas as pd
import streamlit as st

from healthcare_des import AdvancedScenarioConfig, run_advanced_once
from healthcare_des.benchmark import benchmark_scenarios
from healthcare_des.dashboard_support import advanced_kpis, lifecycle_summary, queue_summary
from healthcare_des.model import ScenarioConfig, run_replications, summarise
from healthcare_des.optimisation import search_capacity

st.set_page_config(page_title="Healthcare Capacity Digital Twin", layout="wide")
st.title("Healthcare Demand & Capacity Digital Twin")
st.caption(
    "A reproducible SimPy decision-support model for MRI patient flow and capacity planning."
)

with st.sidebar:
    st.header("Scenario")
    daily_demand = st.slider("Daily MRI demand", 20, 160, 70)
    operating_hours = st.select_slider("Operating hours", options=[8, 12, 16, 24], value=8)
    mri_machines = st.slider("MRI machines", 1, 8, 4)
    radiographers = st.slider("Radiographers", 1, 10, 4)
    radiologists = st.slider("Radiologists", 1, 5, 1)
    no_show_rate = st.slider("Outpatient no-show rate", 0.0, 0.30, 0.08, 0.01)
    replications = st.slider("Simulation replications", 3, 30, 10)
    warmup_days = st.slider("Warm-up days", 0, 14, 2)
    emergency_reserve = st.slider("Urgent-aware MRI reserve", 0.0, 0.50, 0.15, 0.05)
    maintenance_policy = st.selectbox(
        "Maintenance policy",
        ["fixed_duration_after_release", "fixed_calendar_window"],
    )

config = ScenarioConfig(
    name="dashboard",
    days=30,
    warmup_days=int(warmup_days),
    daily_demand=float(daily_demand),
    operating_hours=int(operating_hours),
    mri_machines=int(mri_machines),
    radiographers=int(radiographers),
    radiologists=int(radiologists),
    no_show_rate=float(no_show_rate),
)

results = run_replications(config, replications=replications)
summary = summarise(results)

columns = st.columns(5)
columns[0].metric("Mean wait", f"{summary['mean_wait_minutes']:.1f} min")
columns[1].metric("Mean system time", f"{summary['mean_system_minutes']:.1f} min")
columns[2].metric("Throughput/day", f"{summary['throughput_per_day']:.1f}")
columns[3].metric("Completed ≤120 min", f"{summary['completed_within_120_pct']:.1f}%")
columns[4].metric("Completion rate", f"{summary['completion_rate_pct']:.1f}%")

st.subheader("Confidence intervals")
ci_columns = [
    "mean_wait_minutes_ci95_low",
    "mean_wait_minutes",
    "mean_wait_minutes_ci95_high",
    "throughput_per_day_ci95_low",
    "throughput_per_day",
    "throughput_per_day_ci95_high",
]
st.dataframe(
    pd.DataFrame([{column: summary[column] for column in ci_columns}]), use_container_width=True
)

st.subheader("Replication uncertainty")
st.line_chart(
    results.set_index("replication")[
        ["mean_wait_minutes", "mean_system_minutes", "throughput_per_day"]
    ]
)

st.subheader("Resource utilisation")
utilisation = pd.DataFrame(
    {
        "resource": ["Clerks", "Radiographers", "MRI", "Radiologists"],
        "utilisation_pct": [
            summary["clerk_utilisation_pct"],
            summary["radiographer_utilisation_pct"],
            summary["mri_utilisation_pct"],
            summary["radiologist_utilisation_pct"],
        ],
    }
).set_index("resource")
st.bar_chart(utilisation)

st.subheader("Patient-type performance")
patient_types = pd.DataFrame(
    {
        "patient_type": ["Outpatient", "Inpatient", "Emergency"],
        "mean_wait_minutes": [
            summary["outpatient_mean_wait_minutes"],
            summary["inpatient_mean_wait_minutes"],
            summary["emergency_mean_wait_minutes"],
        ],
        "mean_system_minutes": [
            summary["outpatient_mean_system_minutes"],
            summary["inpatient_mean_system_minutes"],
            summary["emergency_mean_system_minutes"],
        ],
    }
).set_index("patient_type")
st.bar_chart(patient_types)

st.subheader("Correctness-hardened advanced DES snapshot")
advanced_config = replace(
    AdvancedScenarioConfig(),
    name="dashboard-advanced",
    days=2,
    warmup_days=0,
    daily_demand=float(daily_demand),
    operating_hours=int(operating_hours),
    mri_machines=int(mri_machines),
    no_show_rate=float(no_show_rate),
    emergency_capacity_reserve=float(emergency_reserve),
    maintenance_policy=maintenance_policy,
    bootstrap_samples=100,
)
advanced_result, advanced_patients, advanced_state = run_advanced_once(advanced_config)
advanced = advanced_kpis(advanced_result)
advanced_columns = st.columns(6)
advanced_columns[0].metric("Completed", int(advanced["completed"]))
advanced_columns[1].metric("Abandoned", int(advanced["abandoned"]))
advanced_columns[2].metric("Unfinished", int(advanced["unfinished"]))
advanced_columns[3].metric("Max MRI queue", int(advanced["max_queue_length"]))
advanced_columns[4].metric("MRI failures", int(advanced["mri_failures"]))
advanced_columns[5].metric("MRI downtime", f"{advanced['mri_downtime_minutes']:.1f} min")

left, right = st.columns(2)
with left:
    st.markdown("**Explicit MRI queue observations**")
    st.dataframe(queue_summary(advanced_state), use_container_width=True)
with right:
    st.markdown("**Patient and reporting lifecycle**")
    st.dataframe(lifecycle_summary(advanced_patients), use_container_width=True)

st.caption(
    f"Reserve policy: urgent-aware {emergency_reserve:.0%}; maintenance policy: {maintenance_policy}. "
    "Routine patients may use spare capacity when no urgent patient is queued."
)

with st.expander("Replication-level results"):
    st.dataframe(results, use_container_width=True)

st.subheader("Scenario comparison")
if st.button("Run standard scenario comparison"):
    comparison = benchmark_scenarios(
        replace(config, days=14), replications=max(3, replications // 2)
    )
    st.scatter_chart(
        comparison,
        x="mean_wait_minutes",
        y="throughput_per_day",
        size="mri_utilisation_pct",
        color="name",
    )
    st.dataframe(comparison, use_container_width=True)

st.subheader("Capacity search")
st.write(
    "Ranks transparent machine and staffing combinations using service-level penalties and "
    "illustrative capacity weights."
)
if st.button("Run capacity search"):
    candidates = search_capacity(
        replace(config, days=14),
        mri_options=tuple(range(max(1, mri_machines - 1), mri_machines + 2)),
        radiographer_options=tuple(range(max(1, radiographers - 1), radiographers + 2)),
        radiologist_options=tuple(range(1, max(2, radiologists + 1))),
        replications=4,
    )
    st.dataframe(candidates.head(10), use_container_width=True)

st.info(
    "This research model uses synthetic or public aggregate data and is not a clinical scheduling system."
)
