# Model specification

This document defines the conceptual and computational model implemented by the healthcare discrete-event simulation. It is the normative description against which code, tests and reported results should be reviewed.

## Purpose and scope

The model represents an MRI service in which outpatient, inpatient and emergency demand competes for shared administrative, radiography, scanner and reporting capacity. It is intended for reproducible scenario analysis, capacity planning, teaching and operations-research experimentation.

It is not a clinically validated decision system. Results depend on the supplied demand, service-time, routing, staffing, downtime and behavioural assumptions.

## Model type

- Stochastic, process-interaction discrete-event simulation.
- Finite-horizon terminating model by default.
- Optional warm-up period and configurable draining behaviour.
- Multiple independent replications supported through deterministic seed offsets.

## Entities

### Patient

Each patient has:

- unique identifier;
- patient type: outpatient, inpatient or emergency;
- scheduled or generated arrival time;
- queue-entry and service timestamps by stage;
- completion state: completed, no-show, abandoned or unfinished;
- stage waiting times, total waiting time and total system time.

### Resource units

- clerks;
- radiographers;
- MRI machines;
- radiologists.

Resource capacities are scenario parameters. MRI requests use patient-type priority; other resources use first-come, first-served behaviour unless a future policy explicitly changes this.

## Events

The event calendar may include:

1. patient generation;
2. scheduled arrival or stochastic arrival;
3. no-show determination for eligible outpatients;
4. queue entry and resource acquisition;
5. service start and service completion;
6. planned maintenance start/end;
7. stochastic MRI failure and repair;
8. abandonment where enabled by the advanced engine;
9. model-horizon termination;
10. bounded or full draining of remaining work.

## Patient flow

The canonical flow is:

```text
arrival
  -> reception
  -> preparation
  -> MRI scan and cleaning
  -> reporting
  -> completion
```

Alternative terminal states are:

- `no_show`: an eligible outpatient does not enter the physical service process;
- `abandoned`: a patient leaves before completion under an enabled patience rule;
- `unfinished`: a patient remains in the system when the configured termination policy ends the run.

## Queue disciplines

- Reception: first come, first served.
- Preparation: first come, first served.
- MRI: non-preemptive priority queue with emergency before inpatient before outpatient.
- Reporting: first come, first served.

Priority affects the order of waiting MRI requests; it does not interrupt a scan already in progress.

## Time and calendar

- Internal time unit: minutes.
- A day contains 1,440 minutes.
- Operating hours, staffing windows, breaks and maintenance windows are scenario inputs.
- Arrivals occurring before `warmup_days * 1440` may be simulated but are excluded from measured outputs.

## Stochastic assumptions

The base engine currently uses configurable distributions including:

- reception service: exponential;
- preparation service: triangular;
- scan service: lower-bounded normal by patient type;
- reporting service: uniform;
- MRI repair time: exponential;
- outpatient arrival deviation: normal;
- event probabilities for no-show and failure: Bernoulli trials.

These are modelling assumptions, not universal clinical facts. Each empirical use should document parameter source, fitting method, date, sample size and goodness-of-fit evidence.

## State variables

At minimum, the model tracks:

- simulation clock;
- queue length and occupancy for each resource;
- patient status and timestamps;
- measured arrivals and terminal outcomes;
- resource busy time;
- MRI failures and downtime;
- optional state observations for advanced-engine runs.

## Conservation identities

For the base engine, every measured generated patient must satisfy:

```text
arrivals = completed + no_shows + unfinished
```

For the advanced engine, the corresponding identity is:

```text
arrivals = completed + abandoned + unfinished
```

No patient may belong to more than one terminal state.

## Output measures

Primary outputs include:

- arrivals, completions and terminal-state counts;
- completion rate;
- stage and total waiting time;
- total system time and upper quantiles;
- service-level attainment;
- throughput;
- utilisation by resource type;
- patient-type performance;
- failure and downtime measures;
- replication uncertainty and confidence intervals.

## Termination policies

### Fixed horizon

The run stops at the configured horizon. Patients still active are counted as unfinished.

### Drain until empty

No new patients are generated after the horizon, and the simulation continues until eligible work completes.

### Bounded drain

The advanced engine may continue for at most a configured drain period, after which remaining patients are unfinished.

The selected policy must be reported with every result because it affects completion, waiting-time and utilisation metrics.

## Assumptions and exclusions

Unless explicitly configured, the model does not claim to represent:

- clinical deterioration;
- diagnostic accuracy or health outcomes;
- detailed modality protocols;
- patient transport constraints;
- ward-bed interactions;
- infection-control constraints;
- radiologist subspecialty matching;
- geographically distributed resources;
- financial reimbursement rules.

## Verification target

The implementation is considered internally verified only when:

- deterministic seeds reproduce identical outputs;
- all conservation identities hold;
- times and queue lengths remain non-negative;
- occupancy never exceeds capacity;
- stage times are chronologically ordered;
- simplified cases agree with analytical queueing results within stochastic tolerance;
- all tests and quality gates pass.

## Validation target

Operational validation requires evidence beyond code correctness, such as review by domain experts, parameter calibration from relevant data and comparison of model outputs with observed system behaviour. Public-data benchmarking alone is not clinical validation.
