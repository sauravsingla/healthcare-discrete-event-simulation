"""Export the source-backed Singla (2020) reproduction contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from healthcare_des.paper_reproduction import (
    published_targets,
    reproduction_manifest,
    validate_reproduction_manifest,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the authoritative Singla (2020) DES reproduction specification"
    )
    parser.add_argument("--output-dir", default="outputs/paper_reproduction")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest = reproduction_manifest()
    validate_reproduction_manifest(manifest)
    manifest_path = output_dir / "singla_2020_reproduction_manifest.json"
    targets_path = output_dir / "singla_2020_published_targets.csv"
    manifest_path.write_text(json.dumps(manifest, indent=2, default=str) + "\n", encoding="utf-8")
    published_targets().to_csv(targets_path, index=False)

    print(f"Wrote {manifest_path}")
    print(f"Wrote {targets_path}")


if __name__ == "__main__":
    main()
