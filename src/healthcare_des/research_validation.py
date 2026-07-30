"""Research-grade calibration, equivalence testing and distribution diagnostics."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Mapping, Sequence

import numpy as np
import pandas as pd

try:
    from scipy import optimize, stats
except ImportError as exc:  # pragma: no cover - exercised when analysis extra missing
    raise ImportError("Install healthcare-des[analysis] for research validation") from exc

from .advanced_model import AdvancedScenarioConfig, run_advanced_replications


def fit_hourly_profile(
    data: pd.DataFrame,
    timestamp_column: str = "timestamp",
    count_column: str | None = None,
    operating_hours: int = 24,
    smoothing: float = 1.0,
) -> tuple[float, ...]:
    """Estimate a normalized hourly demand profile from timestamped activity data.

    When ``count_column`` is omitted each row represents one arrival. Additive
    smoothing avoids zero-rate hours and makes the profile safe for simulation.
    """
    if timestamp_column not in data:
        raise ValueError(f"Missing timestamp column: {timestamp_column}")
    timestamps = pd.to_datetime(data[timestamp_column], errors="coerce")
    if timestamps.isna().any():
        raise ValueError("Timestamp column contains invalid values")
    if not 1 <= operating_hours <= 24 or smoothing < 0:
        raise ValueError("operating_hours must be in [1, 24] and smoothing non-negative")
    weights = np.ones(len(data), dtype=float)
    if count_column is not None:
        if count_column not in data:
            raise ValueError(f"Missing count column: {count_column}")
        weights = pd.to_numeric(data[count_column], errors="coerce").to_numpy(float)
        if np.isnan(weights).any() or (weights < 0).any():
            raise ValueError("Counts must be finite and non-negative")
    counts = np.full(operating_hours, float(smoothing))
    for hour, weight in zip(timestamps.dt.hour.to_numpy(), weights, strict=True):
        if hour < operating_hours:
            counts[int(hour)] += float(weight)
    if counts.sum() <= 0:
        raise ValueError("No activity falls inside the requested operating hours")
    return tuple((counts / counts.sum()).tolist())


def confidence_interval(values: Sequence[float], confidence: float = 0.95) -> tuple[float, float]:
    array = np.asarray(values, dtype=float)
    if array.size < 2:
        raise ValueError("At least two observations are required")
    mean = float(array.mean())
    sem = float(stats.sem(array))
    critical = float(stats.t.ppf((1 + confidence) / 2, array.size - 1))
    return mean - critical * sem, mean + critical * sem


def equivalence_report(
    observed: Sequence[float],
    reference: Sequence[float],
    equivalence_margin: float,
    alpha: float = 0.05,
) -> dict[str, float | bool]:
    """Two one-sided tests, CI overlap, effect size and KS comparison."""
    x = np.asarray(observed, dtype=float)
    y = np.asarray(reference, dtype=float)
    if x.size < 2 or y.size < 2 or equivalence_margin <= 0:
        raise ValueError("Two samples and a positive equivalence margin are required")
    difference = float(x.mean() - y.mean())
    se = float(np.sqrt(x.var(ddof=1) / x.size + y.var(ddof=1) / y.size))
    df_num = (x.var(ddof=1) / x.size + y.var(ddof=1) / y.size) ** 2
    df_den = ((x.var(ddof=1) / x.size) ** 2 / (x.size - 1)) + (
        (y.var(ddof=1) / y.size) ** 2 / (y.size - 1)
    )
    df = float(df_num / df_den) if df_den else float(x.size + y.size - 2)
    lower_t = (difference + equivalence_margin) / se if se else np.inf
    upper_t = (difference - equivalence_margin) / se if se else -np.inf
    p_lower = float(1 - stats.t.cdf(lower_t, df))
    p_upper = float(stats.t.cdf(upper_t, df))
    pooled = np.sqrt(
        ((x.size - 1) * x.var(ddof=1) + (y.size - 1) * y.var(ddof=1)) / (x.size + y.size - 2)
    )
    effect = difference / pooled if pooled else 0.0
    x_ci = confidence_interval(x, 1 - 2 * alpha)
    y_ci = confidence_interval(y, 1 - 2 * alpha)
    ks = stats.ks_2samp(x, y)
    return {
        "observed_mean": float(x.mean()),
        "reference_mean": float(y.mean()),
        "mean_difference": difference,
        "equivalence_margin": equivalence_margin,
        "tost_p_lower": p_lower,
        "tost_p_upper": p_upper,
        "equivalent": bool(p_lower < alpha and p_upper < alpha),
        "observed_ci_low": x_ci[0],
        "observed_ci_high": x_ci[1],
        "reference_ci_low": y_ci[0],
        "reference_ci_high": y_ci[1],
        "ci_overlap": bool(max(x_ci[0], y_ci[0]) <= min(x_ci[1], y_ci[1])),
        "cohens_d": float(effect),
        "ks_statistic": float(ks.statistic),
        "ks_pvalue": float(ks.pvalue),
    }


def fit_distributions(
    values: Sequence[float],
    candidates: Sequence[str] = ("expon", "gamma", "lognorm", "norm", "weibull_min"),
) -> pd.DataFrame:
    """Fit candidate scipy distributions and return KS, AD-like, AIC and BIC diagnostics."""
    sample = np.asarray(values, dtype=float)
    sample = sample[np.isfinite(sample)]
    if sample.size < 8:
        raise ValueError("At least eight finite observations are required")
    rows: list[dict[str, object]] = []
    for name in candidates:
        distribution = getattr(stats, name, None)
        if distribution is None:
            raise ValueError(f"Unknown scipy distribution: {name}")
        params = distribution.fit(sample)
        log_likelihood = float(np.sum(distribution.logpdf(sample, *params)))
        k = len(params)
        ks = stats.kstest(sample, lambda value: distribution.cdf(value, *params))
        ordered = np.sort(sample)
        cdf = np.clip(distribution.cdf(ordered, *params), 1e-12, 1 - 1e-12)
        n = sample.size
        ad = float(
            -n - np.mean((2 * np.arange(1, n + 1) - 1) * (np.log(cdf) + np.log(1 - cdf[::-1])))
        )
        rows.append(
            {
                "distribution": name,
                "parameters": repr(tuple(float(p) for p in params)),
                "log_likelihood": log_likelihood,
                "aic": 2 * k - 2 * log_likelihood,
                "bic": k * np.log(n) - 2 * log_likelihood,
                "ks_statistic": float(ks.statistic),
                "ks_pvalue": float(ks.pvalue),
                "anderson_darling": ad,
            }
        )
    return pd.DataFrame(rows).sort_values(["aic", "bic"]).reset_index(drop=True)


def save_distribution_plots(
    values: Sequence[float], distribution_name: str, output_dir: str | Path, prefix: str = "service"
) -> tuple[Path, Path]:
    """Save Q-Q and empirical-versus-fitted density plots."""
    import matplotlib.pyplot as plt

    sample = np.asarray(values, dtype=float)
    distribution = getattr(stats, distribution_name)
    params = distribution.fit(sample)
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    qq_path = output / f"{prefix}_{distribution_name}_qq.png"
    density_path = output / f"{prefix}_{distribution_name}_density.png"
    probabilities = (np.arange(1, len(sample) + 1) - 0.5) / len(sample)
    theoretical = distribution.ppf(probabilities, *params)
    fig, ax = plt.subplots()
    ax.scatter(theoretical, np.sort(sample))
    limits = [min(theoretical.min(), sample.min()), max(theoretical.max(), sample.max())]
    ax.plot(limits, limits)
    ax.set(
        xlabel="Theoretical quantiles",
        ylabel="Empirical quantiles",
        title=f"Q-Q: {distribution_name}",
    )
    fig.savefig(qq_path, bbox_inches="tight")
    plt.close(fig)
    grid = np.linspace(sample.min(), sample.max(), 300)
    fig, ax = plt.subplots()
    ax.hist(sample, bins="auto", density=True, alpha=0.45)
    ax.plot(grid, distribution.pdf(grid, *params))
    ax.set(xlabel="Value", ylabel="Density", title=f"Empirical and fitted: {distribution_name}")
    fig.savefig(density_path, bbox_inches="tight")
    plt.close(fig)
    return qq_path, density_path


def calibrate_parameters(
    base: AdvancedScenarioConfig,
    observed_metrics: Mapping[str, float],
    bounds: Mapping[str, tuple[float, float]],
    replications: int = 8,
    seed: int = 17,
) -> tuple[AdvancedScenarioConfig, pd.DataFrame]:
    """Fit numeric scenario parameters by differential evolution."""
    names = tuple(bounds)
    limits = [bounds[name] for name in names]
    history: list[dict[str, float]] = []

    def objective(vector: np.ndarray) -> float:
        changes = {name: float(value) for name, value in zip(names, vector, strict=True)}
        config = replace(base, seed=seed, **changes)
        results = run_advanced_replications(config, replications)
        loss = 0.0
        for metric, target in observed_metrics.items():
            if metric not in results:
                raise ValueError(f"Unknown calibration metric: {metric}")
            scale = max(abs(float(target)), 1.0)
            loss += ((float(results[metric].mean()) - float(target)) / scale) ** 2
        history.append({**changes, "loss": loss})
        return loss

    solution = optimize.differential_evolution(objective, limits, seed=seed, polish=True)
    fitted = replace(
        base, **{name: float(value) for name, value in zip(names, solution.x, strict=True)}
    )
    return fitted, pd.DataFrame(history).sort_values("loss").reset_index(drop=True)
