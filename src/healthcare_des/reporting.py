"""Publication-ready tables, figures and lightweight PDF reports."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def save_scenario_figure(results: pd.DataFrame, path: str | Path) -> Path:
    import matplotlib.pyplot as plt

    required = {"name", "mean_wait_minutes", "throughput_per_day"}
    missing = required - set(results.columns)
    if missing:
        raise ValueError(f"Missing reporting columns: {', '.join(sorted(missing))}")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.scatter(results["mean_wait_minutes"], results["throughput_per_day"])
    for row in results.itertuples(index=False):
        axis.annotate(str(row.name), (row.mean_wait_minutes, row.throughput_per_day))
    axis.set_xlabel("Mean waiting time (minutes)")
    axis.set_ylabel("Throughput per day")
    axis.set_title("Scenario trade-off: waiting time versus throughput")
    figure.tight_layout()
    figure.savefig(destination, dpi=300)
    plt.close(figure)
    return destination


def save_latex_table(results: pd.DataFrame, path: str | Path) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    preferred = [
        "name",
        "mean_wait_minutes",
        "mean_wait_minutes_ci95_low",
        "mean_wait_minutes_ci95_high",
        "throughput_per_day",
        "completed_within_120_pct",
        "mri_utilisation_pct",
    ]
    columns = [column for column in preferred if column in results.columns]
    destination.write_text(
        results[columns].to_latex(index=False, float_format="%.2f"), encoding="utf-8"
    )
    return destination


def save_pdf_report(
    results: pd.DataFrame,
    path: str | Path,
    *,
    title: str = "Healthcare DES Scenario Report",
) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(destination) as pdf:
        figure = plt.figure(figsize=(11.69, 8.27))
        figure.text(0.08, 0.92, title, fontsize=20, weight="bold")
        figure.text(
            0.08,
            0.86,
            "Reproducible scenario comparison generated from healthcare-des.",
            fontsize=11,
        )
        columns = [
            column
            for column in (
                "name",
                "mean_wait_minutes",
                "throughput_per_day",
                "completed_within_120_pct",
                "mri_utilisation_pct",
            )
            if column in results.columns
        ]
        table = figure.add_axes([0.06, 0.12, 0.88, 0.65])
        table.axis("off")
        table.table(
            cellText=results[columns].round(2).astype(str).values,
            colLabels=columns,
            loc="center",
        )
        pdf.savefig(figure, bbox_inches="tight")
        plt.close(figure)

        chart = plt.figure(figsize=(11.69, 8.27))
        axis = chart.add_subplot(111)
        axis.scatter(results["mean_wait_minutes"], results["throughput_per_day"])
        for row in results.itertuples(index=False):
            axis.annotate(str(row.name), (row.mean_wait_minutes, row.throughput_per_day))
        axis.set_xlabel("Mean waiting time (minutes)")
        axis.set_ylabel("Throughput per day")
        axis.set_title("Scenario trade-off")
        chart.tight_layout()
        pdf.savefig(chart)
        plt.close(chart)
    return destination
