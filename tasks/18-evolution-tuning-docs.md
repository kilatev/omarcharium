# Task 18 — Evolution tuning documentation

## Objective

Document the corrected starvation behavior and the new arcade pacing controls.

## Required work

- Explain biological time, `simulationSpeed`, `mutationRate`, feeding, and
  diagnostic acceleration.
- Document that mutation is evaluated at birth and remains probabilistic.
- Update troubleshooting guidance for stale snapshots, paused simulation, and
  exhausted populations.

## Acceptance criteria

- Configuration and troubleshooting docs describe the shipped defaults and
  observable timing accurately.
- Documentation does not imply that mutation is guaranteed after a fixed wall
  time.

## Completion notes

- Updated configuration and architecture references with arcade timing,
  feeding balance, and probabilistic mutation semantics.
