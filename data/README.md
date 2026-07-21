# Data

This project does not publish patient-level or confidential hospital data.

## External public source

Use the official NHS England **Monthly Diagnostic Waiting Times and Activity** collection:

- https://www.england.nhs.uk/statistics/statistical-work-areas/diagnostics-waiting-times-and-activity/monthly-diagnostics-waiting-times-and-activity/

Download a provider/commissioner CSV extract, unpack it locally, and standardise MRI activity:

```bash
python scripts/prepare_nhs_diagnostics.py path/to/nhs_extract.csv
```

The generated `data/processed/nhs_mri_activity.csv` can calibrate daily simulation demand:

```bash
healthcare-des --config configs/baseline.yaml \
  --demand-csv data/processed/nhs_mri_activity.csv
```

Raw NHS files and generated outputs are intentionally excluded from version control because releases can be large and may be revised. Record the source month, download date and publication URL when reporting results.
