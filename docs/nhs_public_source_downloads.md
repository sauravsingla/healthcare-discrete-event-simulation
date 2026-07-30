# Downloading official public NHS benchmark sources

The repository includes a versioned manifest for the public releases used by the real-data MRI benchmark. Raw source files are downloaded locally and must not be committed without a licensing, governance and repository-size review.

## Included releases

- DM01 monthly diagnostics full extract — March 2026;
- DID modality provider counts and median turnaround tables — final 2024-25;
- National Imaging Data Collection asset count — 2024-25;
- NHS HCHS Workforce Statistics CSV files — December 2025.

The manifest is `config/nhs_public_sources.json`.

## Download all sources

```bash
python scripts/fetch_nhs_public_sources.py
```

The default destination is `data/raw/nhs_public`. ZIP files are extracted into source-specific subdirectories.

## Download selected sources

```bash
python scripts/fetch_nhs_public_sources.py \
  --source dm01_2026_03 \
  --source nidc_assets_2024_25
```

Use `--no-extract` to retain ZIP archives without extraction and `--overwrite` to replace existing files.

## Provenance

Each run writes `download_receipt.json` containing the official source URL, release label, local path, file size, SHA-256 checksum and extracted member names. The receipt should be retained with derived benchmark results so the run can be reproduced.

## Execution boundary

Source acquisition does not itself create benchmark scores. After download, run the existing DM01, DID, NIDC and workforce preparation scripts, create the combined benchmark input, and execute `scripts/run_nhs_mri_benchmark.py` with a real-data configuration.

Public aggregate releases are operational benchmarking inputs. They are not patient-level data, clinical validation, or evidence of causality.
