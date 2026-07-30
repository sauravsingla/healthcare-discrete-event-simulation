"""Generate small, deterministic, machine-readable example outputs.

The generated files are intentionally not committed as clinical findings. They are
reproducible software examples created from illustrative default assumptions.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pandas as pd

from healthcare_des.model import ScenarioConfig, run_replications, summarise
from healthcare_des.optimisation import search_capacity


OUTPUT_DIR = Path("outputs")


def main() -> None:
    """Run a bounded example and write CSV outputs for repository reviewers."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = replace(
        ScenarioConfig(),
        name="readme-example",
        days=7,
        warmup_days=1,
        daily_demand=50.0,
        mri_machines=3,
        radiographers=3,
        radiologists=1,
        seed=17,
    )

    replications = run_replications(config, replications=5)
    summary = summarise(replications)
    candidates = search_capacity(
        replace(config, days=5),
        mri_options=(2, 3, 4),
        radiographer_options=(2, 3, 4),
        radiologist_options=(1, 2),
        replications=3,
    )

    replications.to_csv(OUTPUT_DIR / "example_replications.csv", index=False)
    pd.DataFrame([summary]).to_csv(OUTPUT_DIR / "example_summary.csv", index=False)
    candidates.head(10).to_csv(OUTPUT_DIR / "example_capacity_candidates.csv", index=False)

    print(f"Wrote {len(replications)} replication rows")
    print(f"Wrote {len(candidates.head(10))} ranked capacity candidates")
    print(f"Outputs are available in {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
