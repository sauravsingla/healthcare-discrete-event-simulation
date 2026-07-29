"""Generate reproducible benchmark tables and charts for repository documentation."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt

from healthcare_des.advanced_benchmark_cli import run_benchmark


OUTPUT_DIR = Path("outputs")
ASSET_DIR = Path("docs/assets/generated")


def _save_runtime_by_demand(frame) -> None:  # type: ignore[no-untyped-def]
    grouped = frame.groupby("daily_demand", as_index=False)["elapsed_seconds"].mean()
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(grouped["daily_demand"], grouped["elapsed_seconds"], marker="o")
    axis.set_title("Advanced-engine runtime by daily demand")
    axis.set_xlabel("Daily demand")
    axis.set_ylabel("Mean elapsed seconds")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(ASSET_DIR / "runtime_by_demand.png", dpi=160)
    plt.close(figure)


def _save_runtime_by_capacity(frame) -> None:  # type: ignore[no-untyped-def]
    grouped = frame.groupby("mri_machines", as_index=False)["elapsed_seconds"].mean()
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(grouped["mri_machines"], grouped["elapsed_seconds"], marker="o")
    axis.set_title("Advanced-engine runtime by MRI capacity")
    axis.set_xlabel("MRI machines")
    axis.set_ylabel("Mean elapsed seconds")
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(ASSET_DIR / "runtime_by_mri_capacity.png", dpi=160)
    plt.close(figure)


def _save_output_growth(frame) -> None:  # type: ignore[no-untyped-def]
    grouped = frame.groupby("daily_demand", as_index=False)[["patient_rows", "state_rows"]].mean()
    figure, axis = plt.subplots(figsize=(8, 4.5))
    axis.plot(grouped["daily_demand"], grouped["patient_rows"], marker="o", label="Patient rows")
    axis.plot(grouped["daily_demand"], grouped["state_rows"], marker="o", label="State rows")
    axis.set_title("Simulation output growth by daily demand")
    axis.set_xlabel("Daily demand")
    axis.set_ylabel("Mean generated rows")
    axis.legend()
    axis.grid(alpha=0.25)
    figure.tight_layout()
    figure.savefig(ASSET_DIR / "output_growth_by_demand.png", dpi=160)
    plt.close(figure)


def main() -> None:
    """Run the bounded benchmark and save documentation-ready outputs."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ASSET_DIR.mkdir(parents=True, exist_ok=True)

    frame = run_benchmark(days=2, replications=2)
    frame.to_csv(OUTPUT_DIR / "readme_advanced_benchmark.csv", index=False)

    _save_runtime_by_demand(frame)
    _save_runtime_by_capacity(frame)
    _save_output_growth(frame)

    print(f"Wrote benchmark table to {(OUTPUT_DIR / 'readme_advanced_benchmark.csv').resolve()}")
    print(f"Wrote documentation charts to {ASSET_DIR.resolve()}")


if __name__ == "__main__":
    main()
