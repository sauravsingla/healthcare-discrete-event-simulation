# Validation and Reproduction Protocol

This document separates three claims that must not be conflated:

1. **Software verification** — the implementation behaves as specified and passes automated tests.
2. **Model validation** — simulated outputs are acceptably close to observed or authoritative reference data.
3. **Paper reproduction** — exact published scenarios, assumptions and reported metrics have been transcribed and reproduced within stated tolerances.

Passing the test suite establishes software verification only. It does not by itself establish clinical validity or paper reproduction.

## Required evidence

Before making a reproduction claim, record for every scenario:

- source table, figure or page number;
- exact input parameter and unit;
- expected metric and unit;
- tolerance or equivalence margin;
- simulation version and commit SHA;
- Python and dependency versions;
- random-seed policy;
- warm-up period;
- number of replications;
- termination policy;
- calibration-data period;
- deviations from the source publication.

Authoritative values belong in `data/paper_targets_template.csv`. Blank expected values intentionally mean that reproduction has not yet been established.

## Software verification

Run:

```bash
ruff check src tests scripts examples
mypy src/healthcare_des
pytest --cov=healthcare_des --cov-report=term-missing --cov-fail-under=80
python -m build
twine check dist/*
```

The advanced-engine checks should include the accounting identity:

```text
arrivals = completed + abandoned + unfinished
```

For booked outpatients, lifecycle totals must also reconcile according to the configured definitions of cancellation, no-show and actual arrival.

## Face and behavioural validation

Review the following with a healthcare operations expert:

- arrival profiles and patient-class shares;
- examination and reporting distributions;
- scanner operating hours and downtime;
- staff shifts, breaks and handovers;
- priority and abandonment rules;
- cancellation and no-show assumptions;
- definitions of waiting time, utilisation and throughput.

Directionally controlled experiments should show plausible responses. For example, higher demand should generally increase queue pressure, while effective added capacity should generally reduce the constrained stage's delay. Because the model is stochastic, compare replicated distributions rather than single runs.

## Calibration workflow

1. Clean observed arrivals and service-time samples.
2. Fit weekday, seasonal and hourly demand profiles.
3. Fit candidate service-time distributions.
4. Calibrate uncertain parameters using a training period.
5. Freeze parameters.
6. Validate on a separate holdout period.
7. Report error before and after calibration.

Do not calibrate and validate on the same observations.

## Statistical comparison

Use complementary diagnostics:

- absolute and percentage error;
- confidence intervals across replications;
- two one-sided tests for equivalence where a justified margin exists;
- effect size;
- Kolmogorov–Smirnov comparison for distributions;
- QQ and density diagnostics;
- sensitivity analysis for uncertain assumptions.

A non-significant difference is not proof of equivalence. Equivalence margins must be chosen before examining results and should be operationally meaningful.

## Warm-up and termination

The measurement window begins after `warmup_days`. Warm-up patients and state observations must not contribute to reported KPIs.

Choose and document one termination policy:

- `horizon`: stop at the measurement horizon and report unfinished patients;
- `bounded_drain`: stop arrivals at the horizon and allow a limited drain period;
- `drain`: stop arrivals and run until all active patients complete or abandon.

Comparisons are valid only when scenarios use the same policy unless the policy itself is the experimental factor.

## Reproduction decision rule

A scenario may be labelled reproduced only when:

- all source parameters are populated;
- the software-verification workflow passes;
- the configured scenario matches the publication;
- every required target has a documented expected value;
- statistical or tolerance checks pass;
- deviations and unresolved ambiguities are disclosed.

Until then, describe results as an implementation, extension or partial reproduction attempt.

## Reproducibility checklist

For every reported experiment retain:

- commit SHA;
- Python and dependency versions;
- configuration file;
- random seeds;
- number of replications;
- input-data version and retrieval date;
- output tables and figures;
- execution date.

## Clinical and operational limitations

This repository is a research and decision-support framework. Local patient safety, clinical pathways, workforce rules, downtime practices, costs and governance requirements must be validated by qualified stakeholders before operational use.
