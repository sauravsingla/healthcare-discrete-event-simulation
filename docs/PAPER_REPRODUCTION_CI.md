# Paper Reproduction CI Validation

The pull-request CI workflow validates the Singla (2020) reproduction evidence as part of the Python 3.12 quality job.

The validation step generates the machine-readable evidence set and checks:

- DOI `10.4236/ojmsi.2020.84007`;
- all eleven published scenario intentions;
- 46 replications and random seed 17;
- the published demand, MRI waiting-time and scenario-11 targets;
- the reproduction manifest schema;
- the scenario catalogue, comparison template, evidence index and constraint-status outputs;
- paper-specific service-distribution samples.

Generated files are written under `outputs/paper_reproduction/` and included in the CI quality artifact when the workflow succeeds.

The supported claim remains **source-backed reproduction contract with partial numerical reproduction**. CI does not claim bit-for-bit equivalence with the unavailable original Simul8 model, event calendar or random streams.
