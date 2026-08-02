# Verification and validation framework

This repository uses four distinct evidence levels. They must not be described interchangeably.

## Level 1 — software verification

Question: **Does the code execute the intended computational rules correctly?**

Evidence may include:

- unit and integration tests;
- deterministic replay under fixed seeds;
- conservation identities;
- event chronology checks;
- non-negative time and queue checks;
- capacity and occupancy invariants;
- package, CLI and container checks;
- analytical queueing benchmarks for simplified cases.

Passing Level 1 supports the phrase **software-verified implementation**. It does not establish that the model represents a real healthcare service.

## Level 2 — conceptual-model validation

Question: **Are the entities, pathways, resources, priorities and assumptions appropriate for the intended operational setting?**

Evidence may include:

- structured review by healthcare operations experts;
- process mapping against standard operating procedures;
- face-validation workshops;
- review of exclusions and boundary conditions;
- confirmation that priorities, opening hours, staffing and routing reflect the target service.

Passing Level 2 supports the phrase **domain-reviewed conceptual model**, provided reviewers and scope are disclosed.

## Level 3 — calibration and outcome validation

Question: **Do model inputs and outputs agree sufficiently with observed data for the intended use?**

Evidence may include:

- parameter fitting to relevant operational data;
- temporal holdout validation;
- comparison of arrival, waiting, throughput, utilisation and abandonment distributions;
- calibration targets selected before tuning;
- residual and subgroup analysis;
- uncertainty and sensitivity analysis;
- comparison against simple baselines.

Passing Level 3 may support **empirically calibrated and validated for the documented setting and period**. It does not imply general clinical validity.

## Level 4 — external and prospective validation

Question: **Does the model remain useful when reviewed or tested independently and applied beyond the development sample?**

Evidence may include:

- independent reproduction by another group;
- external-site validation;
- prospective comparison with future operational outcomes;
- peer-reviewed assessment;
- documented operational use with monitoring and governance.

Passing Level 4 may support carefully scoped claims of external validity.

## Public NHS data

The repository's public NHS workflows provide external observational evidence and provenance checks. They do not, by themselves, validate the discrete-event simulation's patient-flow logic or establish clinical effectiveness.

Approved wording:

> Benchmarked against official public NHS aggregate data and published healthcare operations evidence.

Avoid unless formally supported:

> NHS validated.

> Clinically validated.

> Proven to improve patient outcomes.

## Independent review terminology

Use `independent review` only when the reviewer:

- is not an author or maintainer of the repository;
- did not generate the claims being assessed;
- is identified by name or institution where permission allows;
- reviewed a clearly stated version and scope;
- supplied findings that are retained without selective omission.

Automated checks, internal author review, literature comparison and AI-assisted feedback should be labelled accordingly.

## Claim matrix

| Evidence available | Permitted claim |
|---|---|
| Tests and CI only | Software verified against documented tests |
| Tests plus analytical benchmark | Internally verified against selected queueing identities |
| Domain review | Conceptual model reviewed for the stated setting |
| Observed-data calibration | Calibrated to the named dataset and period |
| Temporal/external holdout | Validated on the named holdout or external dataset |
| Independent reproduction | Independently reproduced for the disclosed scope |
| Prospective operational study | Prospectively evaluated in the named operational setting |

## Validation report template

Each formal validation report should contain:

1. model version and commit;
2. intended use and excluded uses;
3. validation level claimed;
4. data sources and provenance;
5. pre-specified acceptance criteria;
6. calibration and holdout split;
7. metrics and uncertainty;
8. subgroup and failure analysis;
9. sensitivity analysis;
10. unresolved limitations;
11. reviewer identity and independence statement;
12. conclusion using wording from the claim matrix.

## Acceptance criteria examples

Acceptance thresholds must be chosen before final evaluation. Examples include:

- lifecycle conservation holds for every run;
- no negative durations or impossible event orderings;
- utilisation remains within mathematically valid bounds;
- simplified M/M/1 experiments agree with analytical waiting-time targets within a pre-specified stochastic tolerance;
- holdout error is no worse than the named baseline by a pre-specified margin;
- primary operational metrics fall within agreed calibration intervals.

Thresholds should reflect intended use and should not be retrofitted to observed results.
