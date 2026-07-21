"""YAML configuration loading and demand calibration helpers."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

import pandas as pd
import yaml

from .model import ScenarioConfig


def load_config(path: str | Path) -> ScenarioConfig:
    config_path = Path(path)
    if not config_path.is_file():
        raise FileNotFoundError(f"Scenario configuration not found: {config_path}")

    payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("Scenario configuration must be a YAML mapping")

    valid = {field.name for field in fields(ScenarioConfig)}
    unknown = sorted(set(payload) - valid)
    if unknown:
        raise ValueError(f"Unknown scenario settings: {', '.join(unknown)}")

    config = ScenarioConfig(**payload)
    config.validate()
    return config


def calibrate_daily_demand(path: str | Path, activity_column: str = "activity") -> float:
    """Convert monthly diagnostic activity into a mean calendar-day demand rate."""
    data_path = Path(path)
    if not data_path.is_file():
        raise FileNotFoundError(f"Demand calibration file not found: {data_path}")

    frame = pd.read_csv(data_path)
    if activity_column not in frame:
        raise ValueError(f"Missing required column: {activity_column}")
    activity = pd.to_numeric(frame[activity_column], errors="coerce").dropna()
    if activity.empty or (activity <= 0).any():
        raise ValueError("Activity values must contain positive numbers")
    return float(activity.mean() / 30.4375)
