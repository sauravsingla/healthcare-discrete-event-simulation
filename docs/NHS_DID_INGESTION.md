# NHS Diagnostic Imaging Dataset ingestion

This stage prepares public NHS England Diagnostic Imaging Dataset (DID) extracts for the external MRI benchmark.

## Output schema

The script writes one deterministic row per provider, reporting month and patient-source category:

- `provider_code`
- `provider_name`
- `period`
- `patient_source`
- `mri_activity`
- `request_to_test_days`, when available
- `test_to_report_days`, when available

Duplicate rows are aggregated by summing activity and taking the median of available turnaround measures.

## Usage

```bash
python scripts/prepare_nhs_did.py path/to/did.csv \
  --output data/processed/nhs_did_mri_provider_month.csv
```

The loader accepts common naming variations for provider, period, modality, activity, patient source and turnaround fields. It fails explicitly when required fields cannot be resolved or when the supplied extract contains no valid MRI activity.

## Interpretation limits

DID request-to-test time represents a diagnostic pathway interval and is not equivalent to queue waiting inside reception, preparation or scanning stages in the simulation. Test-to-report time can support external benchmarking of the reporting stage, but aggregate public DID data alone do not establish clinical validation or patient-level accuracy.

## Next join

The resulting provider-month table is designed to join with:

- DM01 activity and waiting-list measures;
- NIDC MRI scanner counts;
- NHS workforce capacity proxies;
- Community Diagnostic Centre activity.
