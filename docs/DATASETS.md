# Data Sources and Governance

This project is designed to work with public aggregate data and privacy-safe synthetic demand. It must not contain patient-identifiable information.

## Supported data categories

### 1. Public aggregate diagnostics data

Suitable inputs include publicly released counts or waiting-time summaries for diagnostic activity. Before adding a source, record:

- publisher;
- dataset title;
- source page;
- retrieval date;
- licence or reuse terms;
- geographic and reporting coverage;
- update frequency;
- fields used by the model.

Public availability does not remove the need to check the applicable licence and attribution requirements.

### 2. Synthetic demand

The module `healthcare_des.synthetic` generates reproducible daily MRI demand using:

- weekday and weekend effects;
- an optional Monday surge;
- a gradual demand trend;
- Poisson variation;
- a fixed random seed.

Example:

```python
from healthcare_des.synthetic import DemandPattern, generate_daily_demand

pattern = DemandPattern(days=90, base_daily_demand=70, seed=17)
demand = generate_daily_demand(pattern)
```

Synthetic data is appropriate for demonstrations, automated tests and sensitivity analysis. It is not evidence that the simulation has been calibrated to a real hospital.

## Minimum input schema

A daily aggregate demand file should normally contain:

| Field | Meaning |
|---|---|
| `date` | Observation date |
| `observed_demand` | Number of requests or referrals |
| `completed_scans` | Completed examinations, when available |
| `median_wait` | Median wait in a documented unit, when available |
| `p90_wait` | 90th-percentile wait, when available |
| `site_id` | Anonymous site identifier for multi-site analysis |

Not every source will provide every field. Missing fields must be documented rather than inferred silently.

## Preparation principles

1. Preserve the raw downloaded file unchanged.
2. Create a separate processed output.
3. Record every filter and transformation.
4. Use explicit units for durations.
5. Check duplicate dates and missing periods.
6. Avoid forward-filling operational outcomes without justification.
7. Keep calibration and validation periods separate.
8. Store only data permitted by the source licence.

## Privacy and security

Do not commit:

- names, addresses or contact information;
- NHS numbers or other patient identifiers;
- free-text clinical notes;
- exact timestamps that could enable re-identification;
- small-cell extracts that violate disclosure controls;
- credentials or signed download URLs.

Use aggregate or synthetic inputs. Consult the repository security policy before reporting any accidental exposure.

## Provenance record

Each processed dataset should have an adjacent metadata record containing:

```yaml
source_title: "Example aggregate diagnostics release"
publisher: "Example publisher"
retrieved_at: "YYYY-MM-DD"
licence: "State the licence"
raw_sha256: "SHA-256 of the raw file"
processing_script: "scripts/example.py"
parameters:
  modality: "MRI"
  start_date: "YYYY-MM-DD"
  end_date: "YYYY-MM-DD"
```

## Reproducibility

A result is reproducible only when the input version, processing logic, configuration, random seed and code revision are all recorded. Published tables or figures should include this information in their accompanying notes or experiment manifest.
