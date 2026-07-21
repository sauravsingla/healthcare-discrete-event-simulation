# External Validation Protocol

This document defines how the healthcare discrete-event simulation may be evaluated against real or publicly available aggregate healthcare data without using confidential patient-level information.

## Validation status

External validation has **not yet been completed**. The repository must not describe the model as externally validated until all acceptance criteria below have been met and the evidence has been committed or linked reproducibly.

## Eligible data sources

Use only datasets that are legally accessible and appropriate for the intended analysis, such as:

- publicly released aggregate hospital activity statistics;
- published radiology or MRI utilisation summaries;
- government open-data portals;
- peer-reviewed supplementary datasets;
- de-identified institutional aggregates supplied under an appropriate data-sharing agreement.

Do not commit patient identifiers, dates of birth, free-text clinical notes, accession numbers, local record identifiers, or any data that could reasonably permit re-identification.

## Minimum dataset requirements

A validation dataset should contain enough information to estimate at least three of the following:

- arrivals or bookings by day, week, or hour;
- cancellations and no-shows;
- completed examinations;
- waiting-time distribution or quantiles;
- service-time distribution or quantiles;
- scanner utilisation or operating hours;
- abandonment or unfinished workload;
- inpatient, outpatient, and emergency mix.

The source, extraction date, licence, population, observation window, missingness, exclusions, and aggregation method must be recorded.

## Holdout design

1. Split calibration and validation periods before tuning parameters.
2. Use the calibration period only to estimate demand, service, cancellation, no-show, and capacity assumptions.
3. Freeze the configuration and random-seed policy.
4. Evaluate the frozen model on the holdout period.
5. Report all tested outcomes, including those that do not match well.

## Comparison measures

Report absolute and relative error for count outcomes and distribution-sensitive measures for waiting and service times. Recommended outputs include:

- mean absolute error and root mean squared error;
- mean absolute percentage error where denominators are stable and non-zero;
- observed-versus-simulated quantiles;
- empirical coverage of simulation intervals;
- calibration plots across time periods or activity bands;
- sensitivity of results to warm-up, termination policy, and random seed.

## Acceptance criteria

Acceptance thresholds must be declared before reviewing holdout results. They should be justified by the operational decision and measurement quality rather than chosen to make the model pass.

At minimum, external validation requires:

- a documented data source and licence;
- a reproducible transformation script;
- a frozen calibration configuration;
- a distinct holdout period or dataset;
- uncertainty intervals across replications;
- reconciliation of all patient-flow identities;
- a table of passed and failed criteria;
- a limitations statement reviewed by a qualified domain expert.

## Evidence package

Create a dated directory under `validation/` containing:

- `DATA_SOURCE.md`;
- transformation code;
- a machine-readable configuration;
- exact commands and package version;
- seeds and replication count;
- observed and simulated aggregate outputs;
- metrics and plots;
- an interpretation signed or acknowledged by the reviewer.

## Permitted claims

Before completion, use wording such as:

> The repository provides a protocol and tooling for external validation; independent validation against real healthcare observations remains future work.

After completion, describe exactly which dataset, period, population, and outcomes were validated. Do not generalise a narrow validation result to other hospitals, patient groups, scanners, or operating policies.