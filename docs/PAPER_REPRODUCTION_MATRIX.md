# Singla (2020) reproduction matrix

The repository claim is **source-backed reproduction contract with partial numerical reproduction**. Published values are transcribed where available; unavailable scenario-level numbers are never inferred.

## Seven-point evidence coverage

1. **Scenario-level results:** all eleven scenario intentions are indexed in `singla_2020_scenario_catalog.csv`. Scenario 11 has a transcribed numerical improvement; other scenarios are marked as lacking a numerical target in the current evidence.
2. **Automated comparison:** `singla_2020_comparison_template.csv` provides paper value, reproduced value, difference, tolerance and pass/fail fields. `compare_reproduced_results()` evaluates supplied reproduction metrics.
3. **Distribution fidelity:** the paper-specific sampler implements exponential reception, triangular preparation, normal MRI and uniform reporting distributions. Pearson V arrival shape/scale remain unavailable and are explicitly not fabricated.
4. **MRI parameters:** the manifest records MRI normal mean 26.46 minutes and standard deviation 8.0 minutes and applies them to the supported baseline.
5. **Operational constraints:** staff-by-shift values are applied directly. The 90% generic availability and hard reception/reading-room queue capacities are retained in `singla_2020_constraint_status.csv` because the current engine has no equivalent generic availability or hard queue-cap field.
6. **Evidence index:** `singla_2020_evidence_index.csv` maps paper evidence concepts to repository fields and generated outputs.
7. **Claim control:** README, manifest and validation documentation must use the qualified claim above; bit-for-bit Simul8 equivalence is not claimed.

## Exported evidence

Running:

```bash
python scripts/export_paper_reproduction_spec.py --output-dir outputs/paper_reproduction
```

produces:

- `singla_2020_reproduction_manifest.json`
- `singla_2020_published_targets.csv`
- `singla_2020_scenario_catalog.csv`
- `singla_2020_comparison_template.csv`
- `singla_2020_evidence_index.csv`
- `singla_2020_constraint_status.csv`
- `singla_2020_service_distribution_samples.csv`

## Numerical targets currently transcribed

| Scenario | Metric | Published value |
|---|---|---:|
| Baseline | Historical February 2018 demand | 2,089 scans |
| Baseline | Simulated monthly demand | 1,828–1,930 scans |
| Baseline | MRI waiting-room queue before improvement | 17 minutes |
| Improved | MRI waiting-room queue after improvement | 5 minutes |
| Scenario 11 | System-time reduction | 20 minutes |

Full numerical reproduction for every scenario requires additional authoritative paper tables, the original Simul8 model, or original outputs. The repository reports that limitation explicitly rather than inventing missing values.
