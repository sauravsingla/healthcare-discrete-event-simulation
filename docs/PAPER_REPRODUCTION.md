# Singla (2020) Reproduction Contract

This repository contains a machine-readable reproduction contract for **Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation** (Singla, 2020), DOI `10.4236/ojmsi.2020.84007`.

## Source-backed run controls and assumptions

The contract transcribes the assumptions disclosed in the article:

- 30-day simulation;
- 4,320-minute warm-up, equivalent to three days;
- 46 replications per scenario;
- random sampling seed 17;
- 57% outpatient, 24.08% inpatient and 18.92% emergency demand;
- 8% outpatient no-show rate;
- 90% staff and machine availability assumption;
- morning, evening and night shifts of eight hours each;
- radiographer staffing of 4, 3 and 2 by shift;
- one clerk and one consultant per shift;
- exponential reception service with mean eight minutes;
- triangular preparation time `(4, 5, 6)` minutes;
- uniform report interpretation time from 6 to 12 minutes;
- normal MRI service-time family;
- evening outpatient demand equal to 50% of daytime demand and night demand equal to 25%;
- reception/waiting queue capacity 20 and MRI reading-room queue capacity 25.

## Published validation targets

The evidence bundle records the numerical claims stated in the article:

- February 2018 historical MRI demand: 2,089 scans;
- simulated monthly demand: 1,828–1,930 scans;
- MRI waiting-room queue reduced from approximately 17 minutes to 5 minutes;
- scenario 11 outpatient system time reduced by approximately 20 minutes;
- scenarios 9–11 identified as the strongest operating alternatives;
- all eleven experiment intentions registered explicitly.

## Machine-readable implementation

The authoritative specification is implemented in `healthcare_des.paper_reproduction`.

```python
from healthcare_des import (
    PUBLISHED_SPEC,
    paper_base_config,
    published_targets,
    reproduction_manifest,
    validate_reproduction_manifest,
)

manifest = reproduction_manifest()
validate_reproduction_manifest(manifest)
config = paper_base_config()
targets = published_targets()
```

Export the evidence bundle with:

```bash
python scripts/export_paper_reproduction_spec.py \
  --output-dir outputs/paper_reproduction
```

This writes:

- `singla_2020_reproduction_manifest.json`;
- `singla_2020_published_targets.csv`.

## Scenario registry

| Scenario | Published experiment intention |
|---:|---|
| 1 | Outpatient arrival profile: 8-hour access |
| 2 | Outpatient arrival profile: 16-hour access |
| 3 | Outpatient arrival profile: 24-hour access |
| 4 | MRI service-time distribution experiment A |
| 5 | MRI service-time distribution experiment B |
| 6 | MRI service-time distribution experiment C |
| 7 | Normal-hours overbooking to offset no-shows |
| 8 | Start/end-of-hour overbooking |
| 9 | Exclusive resources for emergency patients |
| 10 | Exclusive resources for inpatient and emergency patients |
| 11 | Staff capacity changed to match demand by shift |

## Fidelity boundary

The contract completes the repository's authoritative transcription of the assumptions and numerical targets disclosed in the article. It prevents current defaults or guessed values from being presented as published evidence.

The original study was built in Simul8. The general Python engine directly supports the normal MRI service family and exponential reception service. The published Pearson V arrivals, triangular preparation distribution and uniform report-interpretation distribution are retained explicitly in the manifest; the closest general-engine baseline uses their disclosed central values. Therefore, the repository provides an auditable source-backed reproduction contract and comparison targets, but does not claim bit-for-bit equivalence with the proprietary Simul8 event calendar or random-number stream.
