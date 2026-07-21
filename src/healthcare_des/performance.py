"""Parallel execution helpers for independent simulation replications."""

from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict

import pandas as pd

from .model import ScenarioConfig, run_once


def _run_replication(arguments: tuple[ScenarioConfig, int]) -> dict[str, object]:
    config, replication = arguments
    return asdict(run_once(config, replication)[0])


def run_replications_parallel(
    config: ScenarioConfig,
    *,
    replications: int = 20,
    workers: int | None = None,
) -> pd.DataFrame:
    if replications <= 0:
        raise ValueError("replications must be positive")
    if workers is not None and workers <= 0:
        raise ValueError("workers must be positive")
    arguments = [(config, index) for index in range(replications)]
    with ProcessPoolExecutor(max_workers=workers) as executor:
        rows = list(executor.map(_run_replication, arguments))
    return pd.DataFrame(rows)
