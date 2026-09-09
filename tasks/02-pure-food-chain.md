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
