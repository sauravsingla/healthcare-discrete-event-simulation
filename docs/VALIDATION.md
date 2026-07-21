# Validation Strategy

This document explains how to validate the discrete-event simulation without overstating what the model proves.

## Validation goals

Validation should answer four questions:

1. Does the software implement the intended patient-flow logic correctly?
2. Are stochastic results reproducible when seeds are fixed?
3. Do model outputs behave plausibly when demand or capacity changes?
4. How closely do simulated aggregate metrics align with an external reference dataset?

## 1. Verification of implementation

Use automated tests to check:

- deterministic replay with fixed random seeds;
- non-negative queue, waiting-time and throughput measures;
- expected ordering of priority classes;
- capacity constraints for scanners and staff;
- monotonic responses in controlled experiments, such as lower waiting times when effective capacity increases;
- correct handling of invalid configuration values.

Run:

```bash
ruff check src tests scripts
pytest --cov=healthcare_des --cov-report=term-missing
```

## 2. Face validation

Review the patient-flow assumptions with a healthcare operations expert. At minimum, validate:

- arrival profiles;
- emergency, inpatient and outpatient proportions;
- examination and reporting-time distributions;
- scanner operating hours;
- staff availability;
- priority rules;
- no-show assumptions;
- definitions of waiting time, utilisation and throughput.

A model can be internally correct and still be operationally unrealistic if these assumptions are wrong.

## 3. Behavioural validation

The model should produce directionally sensible responses.

| Experiment | Expected response |
|---|---|
| Increase daily demand | Waiting time and queue pressure should generally rise |
| Add scanner capacity | Throughput should increase and queues should generally fall |
| Add reporting capacity | Reporting delay should generally fall |
| Increase no-show rate | Completed throughput should generally fall |
| Increase emergency share | Lower-priority patients may wait longer |

Because the model is stochastic, compare distributions or repeated-run summaries rather than relying on one run.

## 4. External validation

Where a public aggregate dataset is used, document:

- source and retrieval date;
- exact fields used;
- filtering and aggregation rules;
- mapping between dataset concepts and simulation metrics;
- calibration period;
- holdout period;
- error measures.

Recommended comparison measures include:

- absolute and percentage error in throughput;
- difference in median waiting time;
- difference in 90th-percentile waiting time;
- resource-utilisation gap;
- confidence intervals across replications.

## 5. Calibration versus validation

Do not use the same observations for both calibration and validation.

A practical split is:

- **Calibration set:** used to choose demand, service-time and capacity parameters.
- **Validation set:** held back and used only to assess predictive agreement.

## 6. Reproducibility checklist

For every published experiment, record:

- commit SHA;
- Python version;
- configuration file;
- random seed;
- number of replications;
- input-data version;
- output tables and figures;
- execution date.

## 7. Interpretation limits

This repository is a research and planning tool. It is not a clinical decision system and should not be used to make patient-level decisions. Results depend on the stated assumptions and should be interpreted as scenario evidence, not as guaranteed operational outcomes.
