from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pandas as pd

SCRIPT = Path(__file__).parents[1] / "scripts" / "run_nhs_end_to_end.py"
SPEC = importlib.util.spec_from_file_location("run_nhs_end_to_end", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_end_to_end_outputs_are_derived_and_leakage_free(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    rows = []
    for provider, base in (("AAA", 100), ("BBB", 200)):
        for month in range(1, 9):
            rows.append(
                {
                    "Provider Code": provider,
                    "Reporting Period": f"2025-{month:02d}-01",
                    "Diagnostic Test": "Magnetic Resonance Imaging",
                    "Total Activity": base + month,
                }
            )
    pd.DataFrame(rows).to_csv(raw / "dm01.csv", index=False)
    pd.DataFrame(
        {
            "Organisation Code": ["AAA", "BBB"],
            "Modality": ["MRI", "MRI"],
            "Asset Count": [2, 4],
        }
    ).to_excel(raw / "nidc.xlsx", index=False)

    output = tmp_path / "out"
    MODULE.run(raw, output)

    benchmark = pd.read_csv(output / "benchmark_input.csv")
    scores = pd.read_csv(output / "provider_scores.csv")
    metadata = json.loads((output / "run_metadata.json").read_text(encoding="utf-8"))

    assert {"actual", "predicted", "mri_scanners"}.issubset(benchmark.columns)
    assert len(scores) == 2
    assert metadata["providers"] == 2
    assert metadata["months"] >= 6
    assert metadata["baseline_selected"] in {"lag_1", "trailing_3"}
    first = benchmark[benchmark["provider_code"].eq("AAA")].sort_values("period").iloc[0]
    assert first["predicted"] == 101
    assert (output / "benchmark_report.md").is_file()
    assert (output / "schema_inventory.json").is_file()


def test_missing_mri_schema_fails_with_actionable_message(tmp_path: Path) -> None:
    raw = tmp_path / "raw"
    raw.mkdir()
    pd.DataFrame({"x": [1]}).to_csv(raw / "unknown.csv", index=False)
    try:
        MODULE.run(raw, tmp_path / "out")
    except ValueError as exc:
        message = str(exc)
        assert "provider-month MRI activity" in message
        assert "schema_inventory.json" in message
        assert (tmp_path / "out" / "failure_diagnostics.json").is_file()
    else:
        raise AssertionError("Expected schema discovery failure")
