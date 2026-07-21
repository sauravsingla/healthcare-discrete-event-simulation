"""Command-line interface for reproducible multi-scenario benchmarks."""

from __future__ import annotations

import argparse
from pathlib import Path

from .benchmark import benchmark_scenarios
from .config import load_config
from .reporting import save_latex_table, save_pdf_report, save_scenario_figure
from .tracking import write_manifest


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Benchmark standard healthcare capacity scenarios"
    )
    parser.add_argument("--config", required=True, help="Path to baseline scenario YAML")
    parser.add_argument("--replications", type=positive_int, default=20)
    parser.add_argument("--output", default="outputs/benchmark.csv")
    parser.add_argument(
        "--research-outputs",
        action="store_true",
        help="Also generate a PDF report, publication figure, LaTeX table and manifest",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output = Path(args.output)
    if output.exists() and output.is_dir():
        raise ValueError(f"Output path is a directory: {output}")

    base = load_config(args.config)
    results = benchmark_scenarios(base, replications=args.replications)
    output.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(output, index=False)

    generated = [str(output)]
    if args.research_outputs:
        stem = output.with_suffix("")
        generated.extend(
            [
                str(save_scenario_figure(results, stem.parent / f"{stem.name}_tradeoff.png")),
                str(save_latex_table(results, stem.parent / f"{stem.name}_table.tex")),
                str(save_pdf_report(results, stem.parent / f"{stem.name}_report.pdf")),
            ]
        )
        write_manifest(
            stem.parent / f"{stem.name}_manifest.json",
            base,
            replications=args.replications,
            output_files=generated,
        )

    columns = [
        "name",
        "mean_wait_minutes",
        "p90_system_minutes",
        "completed_within_120_pct",
        "throughput_per_day",
        "mean_wait_minutes_vs_baseline_pct",
        "throughput_per_day_vs_baseline_pct",
    ]
    print(results[columns].to_string(index=False))
    print(f"Saved benchmark results to {output}")


if __name__ == "__main__":
    main()
