# Repository Gap-Closure Status

This document records the disposition of the eight post-1.3.0 hardening items. It distinguishes changes that can be proven from this repository from evidence that must come from external hospitals, domain reviewers, or GitHub release administration.

## 1. Validation status currency

`VALIDATION_STATUS.md` is updated alongside this document to reference the latest verified 1.3.0 quality run: 193 tests, 84.80% whole-package coverage, five dashboard transformation tests, Python 3.10–3.12, package build and clean-wheel installation, Docker health, and generated benchmark/reporting artifacts.

## 2. Warning disposition

The NHS benchmark period parser now uses an explicit mixed-format parse strategy. The two MRI regular-expression warnings are tracked as non-functional data-ingestion cleanup because the existing compiled expression intentionally exposes named alternatives used by the ingestion logic. They do not change benchmark values. Any future warning suppression must be accompanied by a regression test proving identical row selection.

## 3. Low-coverage user-facing modules

Dedicated tests now exercise configuration loading and rejection paths, demand calibration, CLI parsing and output, calibration metrics/tables/plots, reporting figures/LaTeX/PDF, and parallel replication validation/execution. Coverage remains enforced at the whole-package level; module-level percentages are evidence, not substitutes for behavioural assertions.

## 4. Advanced-engine architecture

The public runtime remains `healthcare_des.advanced_model`; `advanced_engine` is retained as a compatibility base. A destructive consolidation is deliberately not performed in the 1.3.x line because it would create unnecessary API and reproducibility risk. The migration rule is:

1. new behaviour belongs only in `advanced_model`;
2. no import-time monkey-patching is allowed;
3. compatibility aliases must remain explicit;
4. removal of `advanced_engine` requires a major-version deprecation cycle and equivalence tests across all registered scenarios.

This is an intentional compatibility architecture, not an undocumented duplicate implementation.

## 5. Dispatch timing boundary

The MRI dispatcher polls at 0.1 simulated minutes. The current deadline allowance exists solely to let a same-timestamp dispatch event settle before abandonment is finalised. It is not clinical patience and must not be interpreted as extra waiting time. A future major-version event-driven dispatcher may remove polling entirely; until then, boundary regressions are the acceptance gate.

## 6. Exact 2020-paper reproduction

Exact reproduction remains unclaimed until authoritative scenario assumptions and target outputs are fully transcribed. The repository may reproduce methods and scenario families without claiming numerical identity. Required evidence includes source page/table references, units, distributions, warm-up, run length, replications, seeds, termination policy, and target tolerances.

## 7. External operational and clinical validation

The repository now defines the minimum evidence pack, but cannot manufacture external validity. Completion requires:

- approved de-identified patient-flow or operational observations;
- a locked calibration period and independent holdout period;
- pathway, priority, workforce and safety sign-off;
- predefined acceptance thresholds for throughput, waits, queues, abandonment and downtime;
- uncertainty and sensitivity review;
- documented model limitations, governance, privacy and change control;
- independent technical and healthcare-domain reviewers.

No operational deployment claim is valid until these artefacts are attached and approved.

## 8. Formal 1.3.0 release

The package metadata, changelog, source distribution and wheel are release-ready and verified in CI. Publishing a GitHub tag/release is an administrative action outside pull-request code changes. The release owner should create tag `v1.3.0`, attach the CI-built wheel and source distribution, paste the 1.3.0 changelog, and link the successful quality run. Until the tag exists, documentation must say “release-ready” rather than “published release.”

## Closure interpretation

The repository-level work is complete when CI passes this pull request. Patient-level validation, clinical approval, independent review, and GitHub release publication remain externally owned gates and are intentionally not represented as completed software work.
