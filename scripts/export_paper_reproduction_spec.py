"""Export the source-backed Singla (2020) reproduction evidence set."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from healthcare_des.paper_reproduction import (
    comparison_template,
    operational_constraint_status,
    paper_table_figure_index,
    published_targets,
    reproduction_manifest,
    sample_published_service_times,
    scenario_results_catalog,
    validate_reproduction_manifest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the authoritative Singla (2020) DES reproduction specification"
    )
    parser.add_argument("--output-dir", default="outputs/paper_reproduction")
    parser.add_argument("--distribution-samples", type=int, default=1000)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = reproduction_manifest()
    validate_reproduction_manifest(manifest)
    outputs = {
        "singla_2020_reproduction_manifest.json": json.dumps(manifest, indent=2, default=str) + "\n",
    }
    for filename, content in outputs.items():
        (output_dir / filename).write_text(content, encoding="utf-8")

    published_targets().to_csv(output_dir / "singla_2020_published_targets.csv", index=False)
    scenario_results_catalog().to_csv(output_dir / "singla_2020_scenario_catalog.csv", index=False)
    comparison_template().to_csv(output_dir / "singla_2020_comparison_template.csv", index=False)
    paper_table_figure_index().to_csv(output_dir / "singla_2020_evidence_index.csv", index=False)
    operational_constraint_status().to_csv(
        output_dir / "singla_2020_constraint_status.csv", index=False
    )
    sample_published_service_times(
        np.random.default_rng(manifest["published_specification"]["random_seed"]),
        args.distribution_samples,
    ).to_csv(output_dir / "singla_2020_service_distribution_samples.csv", index=False)

    for path in sorted(output_dir.iterdir()):
        if path.is_file():
            print(f"Wrote {path}")


if __name__ == "__main__":
    main()
