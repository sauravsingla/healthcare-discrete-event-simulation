# Independent Clinical and Operational Review

This protocol defines the minimum review needed before simulation results are presented as clinically or operationally credible.

## Current status

No independent clinical endorsement is claimed. Repository maintainers and model authors cannot substitute for independent review.

## Reviewer profile

The review panel should include, where relevant:

- a radiologist or MRI service clinical lead;
- a radiographer or imaging operations manager;
- a hospital operations or scheduling specialist;
- a statistician, simulation modeller, or operations-research specialist;
- an information-governance or privacy representative when local data are used.

Reviewers should disclose conflicts of interest and whether they participated in model development.

## Review scope

The panel should evaluate:

1. Patient pathways and routing logic.
2. Priority rules and emergency handling.
3. Opening hours, staffing windows, maintenance, and failure assumptions.
4. Booking, cancellation, no-show, abandonment, and unfinished-patient definitions.
5. Service-time and arrival distributions.
6. Warm-up, horizon, drain policy, replications, and random seeds.
7. Capacity constraints and optimisation assumptions.
8. Outcome definitions and accounting identities.
9. Calibration and holdout-validation design.
10. Intended-use boundaries, safety implications, and limitations.

## Required review evidence

Each review should record:

- reviewer role and relevant expertise;
- review date and model version or commit SHA;
- documents, configurations, datasets, and outputs reviewed;
- assumptions accepted, rejected, or requiring evidence;
- material risks and recommended mitigations;
- whether the model is suitable for research, exploratory planning, or a defined operational decision;
- explicit exclusions from the review.

Personal contact information or signatures should not be published without consent. A reviewer may acknowledge the final review through a GitHub issue, pull request, institutional letter, or redacted signed form.

## Decision categories

Use one of the following outcomes:

- **Not reviewed:** no independent review has occurred.
- **Review in progress:** reviewers have been appointed but findings are unresolved.
- **Conditionally acceptable:** suitable only after listed actions are completed.
- **Acceptable for defined research use:** assumptions are reasonable for the stated research question.
- **Acceptable for defined operational evaluation:** suitable for a specific controlled evaluation, not autonomous clinical use.
- **Not acceptable:** material flaws prevent the proposed use.

## Review template

```text
Model version / commit:
Reviewer role and expertise:
Conflict-of-interest statement:
Intended use reviewed:
Evidence reviewed:

Pathway and logic findings:
Data and calibration findings:
Statistical and simulation findings:
Operational and safety findings:
Privacy and governance findings:

Required corrections:
Residual limitations:
Decision category:
Date:
Acknowledgement method:
```

## Claim control

Do not use phrases such as "clinically validated," "clinically approved," or "hospital-ready" unless the scope, reviewer credentials, evidence, date, and limitations are publicly documented. Independent review is evidence for a defined use; it is not regulatory approval.
