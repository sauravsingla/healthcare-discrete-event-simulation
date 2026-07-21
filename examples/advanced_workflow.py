"""Reproducible example for the corrected advanced MRI simulation engine."""
from dataclasses import replace

from healthcare_des import AdvancedScenarioConfig, run_advanced_once, run_advanced_replications, summarise_advanced


def main() -> None:
    config = replace(
        AdvancedScenarioConfig(),
        name="documented-example",
        days=14,
        warmup_days=2,
        daily_demand=70,
        mri_machines=4,
        termination_policy="bounded_drain",
        max_drain_minutes=720,
        bootstrap_samples=1000,
        seed=17,
    )

    result, patients, state = run_advanced_once(config)
    print("Single replication")
    print(result)
    print("\nPatient outcomes")
    print(patients["status"].value_counts(dropna=False))
    print("\nState observations")
    print(state.head())

    replications = run_advanced_replications(config, replications=20)
    summary = summarise_advanced(replications)
    print("\nReplication summary")
    for key in sorted(summary):
        print(f"{key}: {summary[key]:.4f}")

    assert result.arrivals == result.completed + result.abandoned + result.unfinished


if __name__ == "__main__":
    main()
