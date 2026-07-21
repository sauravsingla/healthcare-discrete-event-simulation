"""YAML configuration loading and demand calibration helpers."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pandas as pd
import yaml

from .model import ScenarioConfig


def load_config(path: str | Path) -> ScenarioConfig:
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    valid = {field.name for field in fields(ScenarioConfig)}
    unknown = sorted(set(payload) - valid)
    if unknown:
        raise ValueError(f"Unknown scenario settings: {', '.join(unknown)}")
    return ScenarioConfig(**payload)


def calibrate_daily_demand(path: str | Path, activity_column: str = "activity") -> float:
    """Convert monthly diagnostic activity into a mean calendar-day demand rate."""
    frame = pd.read_csv(path)
    if activity_column not in frame:
        raise ValueError(f"Missing required column: {activity_column}")
    activity = pd.to_numeric(frame[activity_column], errors="coerce").dropna()
    if activity.empty or (activity < 0).any():
        raise ValueError("Activity values must contain non-negative numbers")
    return float(activity.mean() / 30.4375)
