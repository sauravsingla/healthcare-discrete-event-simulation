# NHS imaging workforce integration

This workflow adds provider-year imaging workforce capacity to the NHS MRI operational benchmark.

## Prepare workforce data

```bash
python scripts/prepare_nhs_workforce.py prepare data/raw/nhs_workforce.csv \
  --output data/processed/nhs_imaging_workforce.csv
```

The prepared table contains:

- `provider_code`
- `reporting_year`
- `imaging_workforce_fte`
- `workforce_status`

Imaging-related rows are identified from staff-group or occupation labels where available. Duplicate provider-year rows are aggregated. Zero, negative and unusually high values remain visible through status flags.

## Join to the MRI benchmark

```bash
python scripts/prepare_nhs_workforce.py join \
  data/processed/nhs_mri_activity_with_assets.csv \
  data/processed/nhs_imaging_workforce.csv \
  --output data/processed/nhs_mri_with_workforce.csv
```

Depending on available benchmark columns, the joined output can add:

- MRI activity per imaging-workforce FTE;
- observed and predicted activity per FTE;
- MRI scanners per FTE;
- backlog per FTE;
- explicit matched or missing workforce status.

## Interpretation limits

Workforce publications may use provider, trust, occupation or staff-group definitions that do not map exactly to MRI service delivery. Staff can also support several imaging modalities or sites. These metrics provide operational context only. They do not demonstrate causation, staffing adequacy, clinical quality or individual productivity.
