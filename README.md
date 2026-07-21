# Healthcare Discrete-Event Simulation

A reproducible Python implementation of healthcare demand and capacity modelling for MRI services using discrete-event simulation, queue analysis, resource-utilisation measurement and scenario comparison.

## Research Basis

This repository is based on the published paper:

**Saurav Singla (2020), “Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation,” Open Journal of Modelling and Simulation, 8, 88–107.**

- DOI: https://doi.org/10.4236/ojmsi.2020.84007
- Paper: https://www.scirp.org/journal/paperinformation?paperid=102869
- Presentation: https://www.slideshare.net/slideshow/demand-capacity-modelling-in-healthcare/238573051

The original study used discrete-event simulation to examine MRI patient flow, demand, staffing, queueing, resource allocation, no-shows and operating-hour scenarios in an NHS radiology setting.

## Problem Statement

Radiology services must balance uncertain patient demand with constrained MRI machines, radiographers, radiologists, clerical staff and operating hours. Poor alignment between demand and capacity can produce long queues, extended patient time in the system, underused resources and reduced throughput.

This project aims to provide an open and reproducible framework for testing alternative demand-and-capacity scenarios without disrupting a real healthcare operation.

## Model Scope

The model represents:

- Outpatient, inpatient and emergency patient classes
- Priority handling for emergency patients
- Reception, MRI waiting room, scanning and report-interpretation stages
- MRI machines, radiographers, radiologists and clerical resources
- Morning, evening and night shifts
- Stochastic patient arrivals and service times
- No-shows and overbooking strategies
- 8-hour, 16-hour and 24-hour operating scenarios
- Dedicated-resource and staffing-allocation scenarios

## Key Performance Indicators

The simulation is designed to measure:

- Patient throughput
- Average waiting time
- Average time in the system
- Queue length and queueing time
- MRI utilisation
- Radiographer, radiologist and clerk utilisation
- Percentage of patients completing the system within 120 minutes
- Scenario-level demand and capacity balance

## Findings Reported in the Paper

The published study compared 11 scenarios. The strongest scenarios used dedicated resources and demand-aligned staffing. In the reported results:

- MRI waiting-room queue time decreased from approximately 17 minutes to 5 minutes
- Average outpatient time in the system decreased by approximately 20 minutes
- Outpatient throughput increased while maintaining reasonable system times
- Resource utilisation and patient-flow bottlenecks became visible through simulation

These figures are results from the original study and will be treated as validation targets rather than assumed outputs of the Python implementation.

## Planned Python Implementation

The repository will use:

- **SimPy** for discrete-event simulation
- **NumPy** and **SciPy** for stochastic distributions and statistical analysis
- **Pandas** for experiment outputs
- **Matplotlib** or **Plotly** for result visualisation
- **Pytest** for model and regression testing
- **YAML** configuration for reproducible scenarios
- **GitHub Actions** for continuous integration

## Planned Repository Structure

```text
healthcare-discrete-event-simulation/
├── README.md
├── LICENSE
├── CITATION.cff
├── pyproject.toml
├── configs/
│   ├── baseline.yaml
│   ├── extended-hours.yaml
│   └── staffing-scenario.yaml
├── src/
│   └── healthcare_des/
│       ├── model.py
│       ├── patients.py
│       ├── resources.py
│       ├── scenarios.py
│       ├── metrics.py
│       └── validation.py
├── notebooks/
├── tests/
├── figures/
└── docs/
```

## Reproducibility and Data

The original study used a combination of historical demand, published evidence and modelling assumptions. This open-source implementation will use synthetic or publicly shareable data only.

No confidential NHS, employer or patient-level data will be published in this repository.

Model parameters will be clearly labelled as one of:

- Reported in the paper
- Derived from public literature
- Synthetic
- User configurable

## Limitations

The original study was limited to MRI services, used some assumed demand—particularly at night—and did not model all interactions across the wider radiology department. Shared-resource effects and cost optimisation were also outside its main scope.

This implementation will preserve those limitations transparently and provide extension points for broader radiology services, cost modelling, optimisation, agent-based modelling and digital-twin research.

## Citation

```bibtex
@article{singla2020demand,
  title={Demand and Capacity Modelling in Healthcare Using Discrete Event Simulation},
  author={Singla, Saurav},
  journal={Open Journal of Modelling and Simulation},
  volume={8},
  pages={88--107},
  year={2020},
  doi={10.4236/ojmsi.2020.84007}
}
```

## Status

This repository is under active development. The first milestone is a validated Python reproduction of the baseline MRI patient-flow model and selected scenarios from the published study.

## Author

**Saurav Singla**

- LinkedIn: https://www.linkedin.com/in/sauravsingla008/
- ORCID: https://orcid.org/0000-0002-6404-3988
