"""Interactive dashboard for exploring MRI demand and capacity scenarios."""

from dataclasses import replace

import pandas as pd
import streamlit as st

from healthcare_des.model import ScenarioConfig, run_replications, summarise
from healthcare_des.optimisation import search_capacity

st.set_page_config(page_title="Healthcare Capacity Digital Twin", layout="wide")
st.title("Healthcare Demand & Capacity Digital Twin")
st.caption("A reproducible SimPy decision-support model for MRI patient flow and capacity planning.")

with st.sidebar:
    st.header("Scenario")
    daily_demand = st.slider("Daily MRI demand", 20, 160, 70)
    operating_hours = st.select_slider("Operating hours", options=[8, 12, 16, 24], value=8)
    mri_machines = st.slider("MRI machines", 1, 8, 4)
    radiographers = st.slider("Radiographers", 1, 10, 4)
    radiologists = st.slider("Radiologists", 1, 5, 1)
    no_show_rate = st.slider("Outpatient no-show rate", 0.0, 0.30, 0.08, 0.01)
    replications = st.slider("Simulation replications", 3, 30, 10)

config = ScenarioConfig(
    name="dashboard",
    days=30,
    daily_demand=float(daily_demand),
    operating_hours=int(operating_hours),
    mri_machines=int(mri_machines),
    radiographers=int(radiographers),
    radiologists=int(radiologists),
    no_show_rate=float(no_show_rate),
)

results = run_replications(config, replications=replications)
summary = summarise(results)

columns = st.columns(4)
columns[0].metric("Mean wait", f"{summary['mean_wait_minutes']:.1f} min")
columns[1].metric("Mean system time", f"{summary['mean_system_minutes']:.1f} min")
columns[2].metric("Throughput/day", f"{summary['throughput_per_day']:.1f}")
columns[3].metric("Completed ≤120 min", f"{summary['completed_within_120_pct']:.1f}%")

st.subheader("Replication uncertainty")
st.line_chart(results.set_index("replication")[["mean_wait_minutes", "mean_system_minutes"]])
st.dataframe(results, use_container_width=True)

st.subheader("Capacity search")
st.write("Ranks transparent machine and staffing combinations using service-level penalties and illustrative capacity weights.")
if st.button("Run capacity search"):
    candidates = search_capacity(
        replace(config, days=14),
        mri_options=tuple(range(max(1, mri_machines - 1), mri_machines + 2)),
        radiographer_options=tuple(range(max(1, radiographers - 1), radiographers + 2)),
        radiologist_options=tuple(range(1, max(2, radiologists + 1))),
        replications=4,
    )
    st.dataframe(
        candidates[
            [
                "mri_machines",
                "radiographers",
                "radiologists",
                "mean_wait_minutes",
                "throughput_per_day",
                "objective_score",
            ]
        ].head(10),
        use_container_width=True,
    )

st.info("This research model uses synthetic or public aggregate data and is not a clinical scheduling system.")
