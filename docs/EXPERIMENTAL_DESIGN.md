# Experimental design and reporting standard

Use this checklist for every benchmark, paper reproduction, dashboard result and optimisation study produced by this repository.

## Required experiment declaration

Every experiment must state:

| Item | Required content |
|---|---|
| Research question | Decision or hypothesis being evaluated |
| Model version | Git commit or release tag |
| Engine | Base or advanced |
| Scenario configuration | Complete configuration file or serialized parameters |
| Time unit | Minutes |
| Horizon | Number of simulated days |
| Warm-up | Duration and selection method |
| Termination | Fixed horizon, bounded drain or full drain |
| Replications | Number of independent runs |
| Seed policy | Base seed and deterministic offset rule |
| Uncertainty | Confidence level and interval method |
| Primary outcomes | Metrics selected before inspecting results |
| Parameter provenance | Source, date, units and transformation |
| Hardware context | Only when runtime is reported |

## Terminating versus steady-state use

### Terminating systems

Use a terminating design when the simulated operation has a natural endpoint, such as a daily clinic or finite planning period. Report how patients remaining at closure are classified and whether draining is allowed.

### Steady-state systems

Use a warm-up period when the aim is long-run performance. Select warm-up through an explicit method such as Welch plots, repeated moving averages or a documented conservative rule. Do not choose warm-up after inspecting only the preferred scenario.

## Replications

- Use independent replications rather than one long run when practical.
- Use at least 20 replications for inferential comparisons unless a precision analysis justifies fewer.
- Report both the number of replications and the effective observations used in each interval.
- Preserve run-level output so summaries can be independently recomputed.

## Seed management

- Record a base seed.
- Derive replication seeds deterministically and uniquely.
- Use common random numbers when comparing scenarios so that alternatives experience aligned stochastic streams where the implementation permits.
- Validate the selected alternative on a fresh set of out-of-sample seeds.

## Confidence intervals

For each primary metric report:

- sample mean;
- standard deviation;
- standard error;
- confidence level;
- lower and upper confidence bounds;
- interval method.

A zero-width interval from one replication is a descriptive placeholder, not inferential evidence.

## Scenario comparison

Prefer paired comparisons under common random numbers. Report:

- mean paired difference;
- confidence interval for the difference;
- practical effect size;
- operational constraints;
- whether the result remains stable under sensitivity analysis.

Do not rank alternatives solely by point estimates.

## Optimisation under simulation noise

A valid optimisation workflow should:

1. define hard constraints separately from objectives;
2. evaluate every candidate using multiple replications;
3. use common random numbers across candidates;
4. retain uncertainty for each objective;
5. validate finalists on unseen seeds;
6. show a Pareto frontier when objectives conflict;
7. avoid declaring a unique optimum when intervals materially overlap.

## Parameter provenance table

Maintain a table with these fields:

```text
parameter
model component
value and unit
distribution
source organisation or publication
source date
sample size
fitting or transformation method
goodness-of-fit evidence
fallback assumption
owner/reviewer
```

Synthetic defaults must be labelled as assumptions rather than observed clinical estimates.

## Sensitivity analysis

At minimum, evaluate sensitivity to:

- demand level and temporal profile;
- patient mix;
- scan-time distribution and tail behaviour;
- staffing and scanner capacity;
- no-show and abandonment assumptions;
- downtime and repair assumptions;
- termination and draining policy;
- warm-up and run length.

Use global sensitivity analysis for high-dimensional studies where feasible. One-at-a-time sensitivity is acceptable for transparent local diagnostics but does not capture interactions.

## Runtime benchmarking

When reporting runtime include:

- processor and memory;
- operating system;
- Python version;
- dependency versions;
- process/thread settings;
- scenario size;
- number of replications;
- median and dispersion across repeated benchmark executions.

Runtime on one machine must not be presented as a universal performance claim.

## Minimum result statement

A defensible result statement should follow this form:

> Under the documented scenario assumptions, termination policy and seed design, configuration A changed the primary outcome by X relative to configuration B, with a 95% confidence interval of [L, U]. External operational validity has not been inferred beyond the calibration evidence described here.

## Release evidence

For benchmark releases retain:

- configuration files;
- run-level CSV or Parquet output;
- summary tables;
- metadata JSON;
- checksums;
- software environment lock or dependency export;
- plots generated from scripts;
- exact reproduction command.
