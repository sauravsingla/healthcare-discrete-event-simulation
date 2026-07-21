"""Experiment metadata and reproducibility manifests."""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import subprocess
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .model import ScenarioConfig


def _git_sha() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _versions() -> dict[str, str]:
    packages = ("healthcare-des", "numpy", "pandas", "simpy", "scipy", "matplotlib")
    versions: dict[str, str] = {}
    for package in packages:
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            continue
    return versions


def config_hash(config: ScenarioConfig) -> str:
    payload = json.dumps(asdict(config), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def experiment_manifest(
    config: ScenarioConfig,
    *,
    replications: int,
    output_files: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": _git_sha(),
        "scenario": asdict(config),
        "config_sha256": config_hash(config),
        "seed": config.seed,
        "replications": replications,
        "package_versions": _versions(),
        "output_files": output_files or [],
        "extra": extra or {},
    }


def write_manifest(
    path: str | Path,
    config: ScenarioConfig,
    *,
    replications: int,
    output_files: list[str] | None = None,
    extra: dict[str, Any] | None = None,
) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(
            experiment_manifest(
                config,
                replications=replications,
                output_files=output_files,
                extra=extra,
            ),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return destination
