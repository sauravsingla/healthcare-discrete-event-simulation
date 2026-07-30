# Running the NHS MRI benchmark with real data

The repository does not require raw NHS files to be committed. Keep DM01, DID and NIDC extracts in an approved local or controlled storage location and reference them from a JSON run configuration.

## Configuration

```json
{
  "benchmark_input": "../data/processed/nhs_mri_benchmark_input.csv",
  "output_dir": "../outputs/nhs_mri_real",
  "scoring": {
    "min_months": 12,
    "validation_months": 3,
    "holdout_months": 3
  },
  "sources": [
    {
      "name": "DM01",
      "path": "../data/raw/dm01.csv",
      "release": "2025-26 monthly release"
    },
    {
      "name": "DID",
      "path": "../data/raw/did.csv",
      "release": "2025-26 extract"
    },
    {
      "name": "NIDC",
      "path": "../data/raw/nidc.csv",
      "release": "2025 collection"
    }
  ]
}
```

The benchmark input must contain `provider_code`, `period`, `actual` and `predicted`. It may also contain `mri_scanners` for per-scanner comparisons.

## Execute

```bash
python scripts/run_nhs_mri_benchmark.py path/to/run.json
```

The runner writes:

- `provider_scores.csv` — provider-level holdout metrics;
- `run_metadata.json` — split settings, exclusions, source releases, file paths, byte sizes and SHA-256 checksums;
- `benchmark_report.md` — a human-readable provider table, provenance summary and exclusions.

## Reproducibility and controls

The same input files and configuration produce the same scores. The run timestamp is intentionally variable. File checksums make it possible to confirm exactly which source extracts were used.

Do not commit raw source files unless their licensing, information-governance status and repository size have been reviewed. The generated report is an external operational benchmark, not clinical validation or evidence of patient-level performance.
