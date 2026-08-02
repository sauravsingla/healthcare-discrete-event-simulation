"""Publish retained NHS benchmark results into the README.

This script performs a narrow, deterministic replacement so the README cannot
silently drift away from the versioned benchmark evidence.
"""

from __future__ import annotations

from pathlib import Path

README = Path("README.md")

OLD = """**Current published-result status:** numerical NHS outputs such as provider counts, months covered, selected-baseline WAPE and national holdout WAPE are generated as workflow artefacts, but no authoritative numerical artefact is committed in the current repository state. The README therefore documents the verified multi-source execution capability without inventing or presenting unavailable figures. These results should be added only after the generated `run_metadata.json`, `provider_scores.csv` and `benchmark_report.md` are retained as versioned evidence or attached to a release.
"""

NEW = """#### Published external benchmark results

The successful official NHS benchmark is now retained as versioned evidence in [`docs/benchmarks/nhs/2026-08-02/`](docs/benchmarks/nhs/2026-08-02/README.md).

| External benchmark measure | Published result |
|---|---:|
| Monthly DM01 MRI activity tables | 12 |
| Providers represented | 463 |
| Months represented | 11 |
| Provider-month rows | 4,979 |
| Rows matched to MRI scanner capacity | 1,480 |
| Selected leakage-free baseline | `lag_1` |
| Validation WAPE — `lag_1` | 6.7826% |
| Validation WAPE — trailing three-month mean | 6.8400% |
| National holdout actual MRI activity | 840,480 |
| National holdout predicted MRI activity | 821,577 |
| National holdout absolute difference | 18,903 |
| **National holdout WAPE** | **2.2491%** |

The selected `lag_1` baseline marginally outperformed the trailing three-month baseline on the validation period. Provider-level WAPE was available for 289 providers with positive holdout activity: median 13.0128%, 68.5% at or below 20%, and 90.0% at or below 50%. Provider-level results are more volatile for low-volume organisations, so the national aggregate WAPE is the primary headline measure.

The retained evidence records workflow run `30742975228`, source commit `b036068`, artifact ID `8831932312`, and artifact SHA-256 `4a91bc13ae9a038718f5591290189cd39dc9a97427078c123a311bf963a705fe`. Full interpretation, provider-distribution statistics, highest-volume provider results, source-table coverage and claim boundaries are documented in the [published benchmark report](docs/benchmarks/nhs/2026-08-02/README.md), with machine-readable metadata in [`run_metadata.json`](docs/benchmarks/nhs/2026-08-02/run_metadata.json).
"""


def main() -> None:
    text = README.read_text(encoding="utf-8")
    if OLD not in text:
        if NEW in text:
            print("README already contains the published NHS results section")
            return
        raise SystemExit("Expected README publication-status paragraph was not found")
    README.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print("Published NHS external benchmark results in README.md")


if __name__ == "__main__":
    main()
