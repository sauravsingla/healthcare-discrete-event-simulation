"""CLI for automated paper-target reproduction checks."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .reproduction import reproduce_paper
from .reporting import save_latex_table, save_pdf_report, save_scenario_figure
from .tracking import write_manifest


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reproduce published healthcare DES targets")
    parser.add_argument("--config", required=True)
    parser.add_argument("--replications", type=positive_int, default=50)
    parser.add_argument("--output-dir", default="outputs/reproduction")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config = load_config(args.config)
    results, checks = reproduce_paper(config, replications=args.replications)

    results_path = output_dir / "scenario_results.csv"
    checks_path = output_dir / "target_checks.csv"
    results.to_csv(results_path, index=False)
    checks.to_csv(checks_path, index=False)
    save_scenario_figure(results, output_dir / "scenario_tradeoff.png")
    save_latex_table(results, output_dir / "scenario_table.tex")
    save_pdf_report(results, output_dir / "reproduction_report.pdf", title="Paper Reproduction Report")
    write_manifest(
        output_dir / "manifest.json",
        config,
        replications=args.replications,
        output_files=[str(results_path), str(checks_path)],
        extra={"all_targets_passed": bool(checks["passed"].all())},
    )

    print(checks.to_string(index=False))
    if not bool(checks["passed"].all()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
