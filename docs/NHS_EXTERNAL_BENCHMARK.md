# NHS MRI External Benchmark Protocol

This benchmark uses public aggregate NHS data to assess operational plausibility and out-of-sample performance. It does not establish clinical validation or suitability for patient scheduling.

## Data layers

1. **DM01 monthly diagnostics**: provider-month MRI activity, waiting list and long-wait measures.
2. **Diagnostic Imaging Dataset (DID)**: MRI activity, patient-source mix and request/test/report intervals.
3. **National Imaging Data Collection (NIDC)**: provider-level MRI scanner counts.
4. **NHS Workforce Statistics**: trust-level staffing constraints and staffing-to-asset ratios.
5. **Community Diagnostic Centre activity**: transferability to a predominantly planned outpatient operating model.

## Common join keys

The benchmark table uses:

- `provider_code` — NHS organisation/provider code;
- `period` — calendar month in `YYYY-MM` format;
- `mri_activity` — MRI tests carried out during the period;
- `activity_per_calendar_day` — activity divided by the number of calendar days;
- optional waiting-list, scanner, workforce and patient-source fields.

Organisation changes, mergers and code discontinuities must be documented before joining releases.

## Evaluation periods

| Purpose | Period | Use |
|---|---|---|
| Calibration | April 2023–March 2024 | Estimate demand, seasonality and plausible operating ranges |
| Validation | April 2024–March 2025 | Evaluate without provider-specific retuning |
| Temporal holdout | April 2025 onward | Final out-of-sample assessment |

## Primary metrics

- monthly MRI activity weighted absolute percentage error;
- annual throughput absolute percentage error;
- throughput per scanner error;
- Spearman provider-rank correlation;
- monthly seasonal correlation;
- patient-source percentage-point error;
- median test-to-report error;
- backlog direction accuracy.

Proposed thresholds are benchmark design choices, not clinical standards. Every published result must report the provider sample, period, exclusions, missingness and parameter-freezing date.

## DM01 preparation

Download an official provider-level CSV extract and run:

```bash
python scripts/prepare_nhs_diagnostics.py raw_dm01.csv \
  --output data/processed/nhs_mri_provider_month.csv
```

The preparation script resolves known column-name variations, filters MRI rows, aggregates duplicates to provider-month level and fails when required fields cannot be identified.

## Claim control

Permitted wording after successful evaluation:

> Externally benchmarked against public aggregate NHS imaging activity and capacity data across defined providers and time periods.

Do not describe this aggregate-data benchmark as patient-level validation, clinical approval or proof of deployment impact.
