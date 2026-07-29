# Simulation Engine Guide

The repository contains two complementary simulation workflows. Both are maintained, but they serve different levels of analysis.

## Base engine

The base engine is the simplest entry point for YAML-configured scenarios, dashboard exploration, scenario comparisons and transparent capacity searches.

Use it when you need:

- a concise scenario definition;
- rapid replicated experiments;
- the Streamlit dashboard;
- standard KPI summaries;
- the existing `healthcare-des` and `healthcare-des-benchmark` commands.

Primary interfaces:

```python
from healthcare_des.model import ScenarioConfig, run_replications, summarise
```

```bash
healthcare-des --config configs/baseline.yaml --replications 20
healthcare-des-benchmark --config configs/baseline.yaml --replications 20
```

## Advanced engine

The advanced engine is recommended for new research extensions that require richer lifecycle accounting or time-varying operational behaviour.

Use it when you need:

- booked, cancelled, expected, no-show and actual-arrival accounting;
- a complete per-patient outcome ledger;
- hourly, weekday or monthly demand patterns;
- appointment scheduling and controlled overbooking;
- dynamic staffing windows;
- maintenance, failure, repair and optional scan restart;
- horizon, bounded-drain or full-drain termination;
- operational-hours and 24-hour state measures;
- corrected reconciliation of completed, abandoned and unfinished arrivals.

Primary interfaces:

```python
from healthcare_des import (
    AdvancedScenarioConfig,
    run_advanced_once,
    run_advanced_replications,
)
```

## Comparison

| Question | Base engine | Advanced engine |
|---|---:|---:|
| YAML scenario workflow | Yes | No |
| Streamlit dashboard | Yes | Not currently exposed directly |
| Replicated KPI summaries | Yes | Yes |
| Complete patient ledger | Limited | Yes |
| Dynamic staffing windows | Limited | Yes |
| Equipment failure and repair | Limited | Yes |
| Appointment lifecycle | Simplified | Detailed |
| Configurable drain policy | No | Yes |
| Recommended for new research extensions | For simple studies | Yes |

## Migration guidance

1. Begin with `AdvancedScenarioConfig()` and override only required assumptions.
2. Keep the same random seed when comparing implementation changes.
3. Use the same termination policy across scenarios unless termination is the experimental factor.
4. Reconcile every run with:

```text
arrivals = completed + abandoned + unfinished
```

5. Validate any locally calibrated assumptions independently before operational use.

Neither engine is a clinical recommendation or a production scheduling system without local validation, safety review and governance approval.
