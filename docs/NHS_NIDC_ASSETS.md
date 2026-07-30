# NHS NIDC MRI asset workflow

This workflow standardises provider-level MRI scanner counts from NHS National Imaging Data Collection extracts and joins them to provider-month MRI activity prepared from DM01.

## Prepare assets

```bash
python scripts/prepare_nhs_nidc.py assets data/raw/nidc.csv \
  --output data/processed/nhs_nidc_mri_assets.csv
```

The output contains:

- `provider_code`
- `reporting_year`
- `mri_scanners`
- `asset_status`

Duplicate provider-year rows are summed. Zero, negative and unusually high counts are flagged rather than silently removed.

## Join activity

```bash
python scripts/prepare_nhs_nidc.py join \
  data/processed/nhs_mri_provider_month.csv \
  data/processed/nhs_nidc_mri_assets.csv \
  --output data/processed/nhs_mri_activity_with_assets.csv
```

The joined output adds `asset_join_status` and `mri_activity_per_scanner`. Throughput is calculated only when a positive scanner count is available.

## Interpretation limits

NIDC asset counts can be reported at provider or organisation level while scanners may be shared across sites, services or reporting units. Activity per scanner is therefore an external operational benchmark, not a clinical-quality measure. Missing provider-code joins, zero assets and implausible counts must remain visible in any report.
