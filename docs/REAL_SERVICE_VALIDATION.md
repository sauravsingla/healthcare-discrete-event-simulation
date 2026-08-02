# Real MRI Service Validation

This protocol defines how simulated waiting times, utilisation and queues must be compared with a real MRI service.

## Required observed fields

The validation dataset should contain aggregate, privacy-safe observations for a declared site and time window:

- mean and median total waiting time;
- stage-specific waiting times where available;
- MRI utilisation;
- radiographer and radiologist utilisation where available;
- mean and peak queue length;
- throughput and completion rate;
- cancellations, no-shows and abandonment;
- operating hours, scanner count and staffing levels.

## Validation design

1. Use one period for calibration and a different holdout period for evaluation.
2. Fix metric definitions before running the comparison.
3. Record data provenance, extraction rules and missing-data treatment.
4. Declare absolute and relative acceptance thresholds in advance.
5. Compare observed values with simulation means and uncertainty intervals.
6. Publish every metric, including failed thresholds.
7. Obtain local operational, privacy and governance approval before presenting the model as validated for a service.

## Input template

Use `data/validation/real_mri_service_metrics.csv` with one row per metric and period. Required columns are:

```text
site_id,period,split,metric,observed_value,unit,tolerance_absolute,tolerance_relative
```

`split` must be either `calibration` or `holdout`.

## Claim boundary

The repository currently provides the validation structure but does not contain authorised real-service observations. Therefore it does not claim that simulated waiting time, utilisation or queue behaviour has already been validated against a real MRI department. A completed validation requires an approved dataset and a published observed-versus-simulated report.
