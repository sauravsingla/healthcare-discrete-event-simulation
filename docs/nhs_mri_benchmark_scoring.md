# NHS MRI provider benchmark scoring

This workflow scores provider-level MRI benchmark observations using explicit calibration, validation and temporal holdout periods.

## Input schema

Required columns:

- `provider_code`
- `period`
- `actual`
- `predicted`

Optional columns such as `mri_scanners` are retained for asset-normalised comparisons.

## Run

```bash
python scripts/score_nhs_mri_benchmark.py data/processed/nhs_mri_benchmark_input.csv \
  --output-csv outputs/nhs_mri_benchmark.csv \
  --output-json outputs/nhs_mri_benchmark.json \
  --min-months 6 \
  --validation-months 2 \
  --holdout-months 2
```

## Metrics

The current provider-level output includes:

- WAPE;
- MAPE with zero-actual observations excluded;
- annualised throughput error;
- seasonal correlation where enough variation exists;
- month-to-month direction accuracy;
- actual and predicted throughput per scanner where positive NIDC asset counts exist.

The JSON metadata records split configuration, included-provider count, provider exclusions and exclusion reasons.

## Leakage control

The final months are reserved as temporal holdout observations. Validation months immediately precede the holdout. Earlier observations form the calibration period. Metrics are calculated only on the holdout partition.

## Interpretation limits

These outputs are an external operational benchmark based on aggregate public data. They do not establish clinical validity, diagnostic quality, patient-level outcomes or causal performance. Provider-code coverage, reporting changes, shared scanner assets and missing observations must remain visible in any report.
