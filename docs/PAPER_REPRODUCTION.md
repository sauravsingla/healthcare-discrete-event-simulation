# Published Paper Reproduction Protocol

This document defines the evidence required to claim reproduction of the 2020 paper, *Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation*.

## Current status

Exact reproduction is **not claimed**. The repository contains an implementation and research extension, but authoritative scenario inputs, targets, software conditions, and all original experimental details have not yet been completely reconstructed and verified.

## Reproduction target

A reproduction attempt must identify the exact tables, figures, scenarios, and conclusions being reproduced. "Reproduced" must not be used when only qualitative behaviour or approximate trends agree.

## Original-condition inventory

Record, where available:

- software and library versions;
- simulation language and runtime;
- random-number generator and seed policy;
- warm-up period and run length;
- number of replications;
- arrival processes and time profiles;
- service-time distributions and parameters;
- resource counts, operating hours, and downtime;
- priority and queue discipline;
- appointment, cancellation, and no-show logic;
- termination and drain policy;
- scenario-specific interventions;
- output definitions and rounding rules.

Unknown items must be marked `unknown`; they must not be silently replaced with convenient assumptions.

## Reproduction workflow

1. Transcribe authoritative inputs and expected outputs with page, table, or figure references.
2. Store them in machine-readable configuration and target files.
3. Document every interpretation needed to translate the publication into code.
4. Freeze the package version and dependency environment.
5. Run the declared replication and seed policy.
6. Compare simulated and published outcomes using predeclared tolerances.
7. Investigate discrepancies and classify their likely cause.
8. Preserve commands, logs, configurations, outputs, and comparison tables.

## Result classifications

- **Exact numerical reproduction:** all declared targets match within justified numerical tolerance under the reconstructed original conditions.
- **Statistical reproduction:** published values fall within predeclared simulation uncertainty or equivalence bounds.
- **Partial reproduction:** only a declared subset of targets is reproduced.
- **Conceptual replication:** the direction or qualitative conclusion agrees, but the original numerical conditions are unavailable or materially different.
- **Not reproduced:** declared criteria are not met.

## Discrepancy categories

Classify each mismatch as one or more of:

- missing original parameter;
- ambiguous paper description;
- software or random-number difference;
- implementation defect;
- metric-definition difference;
- rounding or transcription issue;
- unavailable source data;
- result inconsistent with reconstructed conditions.

## Required evidence package

Create a versioned directory under `reproduction/` containing:

- `SOURCE_MAP.md` linking every input and target to the publication;
- an environment lock or exact dependency list;
- scenario configuration files;
- target values with tolerances;
- exact commands and random seeds;
- raw outputs;
- comparison tables;
- discrepancy analysis;
- a final classification for every target.

## Claim wording

Until the requirements above are met, use:

> The repository implements and extends the published modelling approach. Exact reproduction of the paper's numerical results remains unverified.

Afterward, state the reproduction category, exact targets, software version, and unresolved discrepancies. Do not describe conceptual or partial agreement as full reproduction.
