# Task 02 — Pure resources and food chain

## Objective

Implement the first high-value ecosystem slice as pure state transitions.

## Required messages

- `Tick(dt)`
- `Reset(seed, starting_population)`
- configuration messages needed by calculations

## Required behavior

- seaweed/algae regeneration
- fish metabolism and hunger
- herbivore resource consumption
- predator fish consumption
- energy transfer
- starvation, predation, and bounded populations

## Acceptance criteria

`update(model, message)` has no side effects and deterministic message sequences demonstrate eating, energy changes, deaths, and resource recovery.

Property tests generate bounded models and message sequences and verify deterministic
replay, bounded resources/populations, and unchanged input models.

## Completion notes

- Added pure `Tick` and `Reset` messages plus `update(model, message)`.
- Added bounded seaweed regeneration, metabolism/starvation, herbivore feeding,
  predator feeding, and deterministic ID-ordered interactions.
- Added focused unit tests and Hypothesis coverage for replay, bounds, and input
  immutability.
- Verification: 57 tests pass, including Hypothesis properties; Python compile,
  shell syntax, plugin validation, and `git diff --check` pass.
