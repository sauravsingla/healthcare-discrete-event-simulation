"""Calibration utilities for comparing simulated and observed activity."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def calibration_metrics(
    observed: pd.Series | np.ndarray,
    simulated: pd.Series | np.ndarray,
) -> dict[str, float]:
    observed_values = np.asarray(observed, dtype=float)
    simulated_values = np.asarray(simulated, dtype=float)
    if observed_values.shape != simulated_values.shape:
        raise ValueError("observed and simulated values must have the same shape")
    if observed_values.size == 0:
        raise ValueError("calibration inputs must not be empty")

    error = simulated_values - observed_values
    nonzero = observed_values != 0
    mape = float(np.mean(np.abs(error[nonzero] / observed_values[nonzero])) * 100) if nonzero.any() else float("nan")
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(np.square(error)))),
        "mape_pct": mape,
        "mean_error": float(np.mean(error)),
    }


def calibration_table(
    observed: pd.DataFrame,
    simulated: pd.DataFrame,
    *,
    key: str,
    value: str,
) -> tuple[pd.DataFrame, dict[str, float]]:
    left = observed[[key, value]].rename(columns={value: "observed"})
    right = simulated[[key, value]].rename(columns={value: "simulated"})
    merged = left.merge(right, on=key, how="inner", validate="one_to_one")
    if merged.empty:
        raise ValueError("No overlapping calibration rows were found")
    merged["error"] = merged["simulated"] - merged["observed"]
    merged["absolute_error"] = merged["error"].abs()
    metrics = calibration_metrics(merged["observed"], merged["simulated"])
    return merged, metrics


def save_calibration_plot(table: pd.DataFrame, path: str | Path, *, x: str) -> Path:
    import matplotlib.pyplot as plt

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(9, 5))
    axis.plot(table[x], table["observed"], marker="o", label="Observed")
    axis.plot(table[x], table["simulated"], marker="o", label="Simulated")
    axis.set_xlabel(x)
    axis.set_ylabel("Activity")
    axis.set_title("Observed versus simulated MRI activity")
    axis.legend()
    figure.tight_layout()
    figure.savefig(destination, dpi=200)
    plt.close(figure)
    return destination
