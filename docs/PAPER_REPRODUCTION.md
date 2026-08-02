# Numerical Reproduction of the 2020 Paper

This document governs reproduction of all eleven scenarios in **Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation** (Singla, 2020).

## Claim boundary

A scenario is marked **reproduced** only when its source assumptions and published numerical targets have been transcribed from the paper or an authoritative author record, the repository configuration executes deterministically, and the reproduced statistics fall within a pre-declared tolerance. Missing source values are not guessed.

## Reproduction matrix

| Scenario | Experiment described in the paper | Authoritative inputs transcribed | Published numerical targets transcribed | Executable repository configuration | Numerical comparison | Status |
|---:|---|---|---|---|---|---|
| 1 | Outpatient arrival-rate experiment | Pending source verification | Pending source verification | Registered | Not evaluated | Not yet reproducible |
| 2 | Outpatient arrival-rate experiment | Pending source verification | Pending source verification | Registered | Not evaluated | Not yet reproducible |
| 3 | Outpatient arrival-rate experiment | Pending source verification | Pending source verification | Registered | Not evaluated | Not yet reproducible |
| 4 | MRI service-time distribution experiment | Pending source verification | Pending source verification | Registered | Not evaluated | Not yet reproducible |
| 5 | MRI service-time distribution experiment | Pending source verification | Pending source verification | Registered | Not evaluated | Not yet reproducible |
| 6 | MRI service-time distribution experiment | Pending source verification | Pending source verification | Registered | Not evaluated | Not yet reproducible |
| 7 | No-show mitigation by overbooking | Pending source verification | Pending source verification | Registered | Not evaluated | Not yet reproducible |
| 8 | Time-positioned overbooking | Pending source verification | Pending source verification | Registered | Not evaluated | Not yet reproducible |
| 9 | Extended-hours or capacity experiment | Pending source verification | Pending source verification | Registered | Not evaluated | Not yet reproducible |
| 10 | Staffing or capacity experiment | Incomplete in available source record | Pending source verification | Registered | Not evaluated | Not yet reproducible |
| 11 | Final operating-policy experiment | Pending source verification | Pending source verification | Registered | Not evaluated | Not yet reproducible |

## Required numerical evidence

For every scenario, retain:

- source page, table and figure references;
- arrival assumptions and operating hours;
- service-time distributions and parameters;
- MRI, radiographer, radiologist, clerk and other capacity values;
- no-show and overbooking rules;
- run length, warm-up, replications and random-seed policy;
- published means, percentages, utilisation, queue and waiting-time targets;
- reproduced estimate, uncertainty interval, absolute difference and relative difference;
- declared tolerance and final classification.

## Classification

- **Reproduced:** all required values are authoritative and results meet the declared tolerance.
- **Discrepant:** authoritative inputs and targets are available, but reproduced results do not meet tolerance.
- **Not verifiable:** the paper or author record does not provide enough information to perform an exact comparison.
- **Not yet evaluated:** implementation or authoritative transcription is incomplete.

## Reproduction workflow

1. Transcribe authoritative inputs and expected outputs with page, table or figure references.
2. Store them in machine-readable configuration and target files.
3. Freeze the package and dependency environment.
4. Run the declared replication and seed policy.
5. Compare reproduced and published outcomes using predeclared tolerances.
6. Preserve commands, logs, configurations, outputs and discrepancy analysis.

## Current conclusion

The repository contains executable registrations for eleven scenarios, but exact numerical reproduction is not yet claimed. The missing element is authoritative transcription of complete scenario inputs and published numerical targets. Recording this explicitly prevents synthetic or guessed targets from being presented as reproduced research evidence.
