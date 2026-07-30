"""Run the NHS MRI benchmark with local data and reproducible provenance."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

SCORER_PATH = Path(__file__).with_name("score_nhs_mri_benchmark.py")
SPEC = importlib.util.spec_from_file_location("score_nhs_mri_benchmark", SCORER_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Unable to load benchmark scorer from {SCORER_PATH}")
SCORER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCORER)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("Run configuration must be a JSON object")
    if "benchmark_input" not in config:
        raise ValueError("Run configuration is missing 'benchmark_input'")
    sources = config.get("sources", [])
    if not isinstance(sources, list):
        raise ValueError("'sources' must be a list")
    return config


def resolve_path(value: str, config_path: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else (config_path.parent / path).resolve()


def source_provenance(config: dict[str, Any], config_path: Path) -> list[dict[str, Any]]:
    provenance: list[dict[str, Any]] = []
    for source in config.get("sources", []):
        if not isinstance(source, dict) or "name" not in source or "path" not in source:
            raise ValueError("Each source requires 'name' and 'path'")
        path = resolve_path(str(source["path"]), config_path)
        if not path.is_file():
            raise FileNotFoundError(f"Configured source does not exist: {path}")
        provenance.append(
            {
                "name": str(source["name"]),
                "release": source.get("release"),
                "path": str(path),
                "sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    return provenance


def _markdown_table(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in frame.itertuples(index=False, name=None):
        values = ["" if pd.isna(value) else str(value) for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def render_report(scores: pd.DataFrame, metadata: dict[str, Any]) -> str:
    lines = [
        "# NHS MRI external benchmark report",
        "",
        f"Run timestamp: `{metadata['run_timestamp_utc']}`",
        "",
        "This is an external operational benchmark and is not clinical validation.",
        "",
        "## Provider results",
        "",
    ]
    if scores.empty:
        lines.append("No providers met the inclusion criteria.")
    else:
        columns = [
            column
            for column in (
                "provider_code",
                "holdout_months",
                "wape",
                "mape",
                "annualised_throughput_error",
                "seasonal_correlation",
                "direction_accuracy",
                "actual_per_scanner",
                "predicted_per_scanner",
            )
            if column in scores.columns
        ]
        lines.append(_markdown_table(scores[columns]))
    lines.extend(["", "## Provenance", ""])
    for source in metadata["sources"]:
        release = source.get("release") or "not specified"
        lines.append(
            f"- **{source['name']}** — release: {release}; SHA-256: `{source['sha256']}`"
        )
    excluded = metadata.get("excluded_providers", [])
    lines.extend(["", "## Exclusions", ""])
    if excluded:
        for item in excluded:
            lines.append(
                f"- `{item['provider_code']}`: {item['reason']} "
                f"({item.get('observed_months', 0)} observed months)"
            )
    else:
        lines.append("No providers were excluded.")
    return "\n".join(lines) + "\n"


def run(config_path: Path) -> dict[str, Path]:
    config = load_config(config_path)
    benchmark_input = resolve_path(str(config["benchmark_input"]), config_path)
    if not benchmark_input.is_file():
        raise FileNotFoundError(f"Benchmark input does not exist: {benchmark_input}")

    output_dir = resolve_path(str(config.get("output_dir", "outputs/nhs_mri_real")), config_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    scores_path = output_dir / "provider_scores.csv"
    metadata_path = output_dir / "run_metadata.json"
    report_path = output_dir / "benchmark_report.md"

    scoring = config.get("scoring", {})
    scores = SCORER.score(
        benchmark_input,
        scores_path,
        metadata_path,
        min_months=int(scoring.get("min_months", 6)),
        validation_months=int(scoring.get("validation_months", 2)),
        holdout_months=int(scoring.get("holdout_months", 2)),
    )
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata.update(
        {
            "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "config_path": str(config_path.resolve()),
            "config_sha256": sha256(config_path),
            "benchmark_input": str(benchmark_input),
            "benchmark_input_sha256": sha256(benchmark_input),
            "sources": source_provenance(config, config_path),
        }
    )
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    report_path.write_text(render_report(scores, metadata), encoding="utf-8")
    return {"scores": scores_path, "metadata": metadata_path, "report": report_path}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a provenance-tracked NHS MRI benchmark")
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    outputs = run(args.config)
    print("\n".join(f"{name}: {path}" for name, path in outputs.items()))


if __name__ == "__main__":
    main()
