# Discrete-event simulation correctness hardening

This change addresses the priority, queue measurement, patience, reporting, maintenance and downtime issues identified during independent review.

## Changes

- MRI allocation now uses one system-wide priority queue. Emergency patients are dispatched first, followed by inpatients and outpatients, with FIFO ordering inside each class.
- Queue metrics are measured from the explicit waiting queue and include total, emergency, inpatient and outpatient counts.
- `emergency_capacity_reserve` is enforced by the runtime dispatcher when urgent patients are waiting, rather than being only an appointment-planning adjustment.
- `abandonment_minutes` is treated as a queue-wait budget. Active service time no longer consumes patience.
- MRI scan completion and report completion are separated. A scanned patient remains completed, while `report_status` records completed or unfinished reporting.
- `maintenance_policy` explicitly supports `fixed_duration_after_release` and `fixed_calendar_window` behaviour.
- Scanner downtime is integrated across unavailable-state transitions so overlapping blockers are counted once.
- Regression tests cover emergency priority, explicit queue measurement, wait-only patience, reporting status, maintenance policy and downtime overlap.

These changes strengthen software verification. Local patient-level, workflow and clinical validation remains required before operational deployment.
