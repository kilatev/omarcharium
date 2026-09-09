# Task 03 — Reproduction and mutation

## Objective

Add generational evolution after the food chain is stable.

## Required behavior

- maturity and reproduction thresholds
- cooldown and energy cost
- inherited traits
- bounded mutations
- mutable diet preference and aggression within baseline species constraints
- generation tracking
- natural extinction

## Acceptance criteria

Accelerated deterministic simulations show births, deaths, inherited traits, bounded mutations, and possible extinction without unbounded population growth.

Property tests generate reproduction and mutation inputs and verify trait bounds,
generation accounting, and population ceilings.

## Completion notes

- Added species-bounded diet preference and aggression traits, persisted with each
  organism and inherited by offspring with deterministic bounded mutation.
- Added maturity, energy-cost, cooldown, stable-ID reproduction, generation
  tracking, and species population ceilings; extinction remains possible through
  metabolism and starvation.
- The model PRNG state now advances only through pure `Tick` transitions and is
  serialized for deterministic replay.
- Added focused unit and Hypothesis coverage for reproduction, cooldowns, trait
  bounds, generation accounting, extinction, replay, and input immutability.
- Verification: 61 tests pass, including Hypothesis properties; Python compile,
  shell syntax, plugin validation, and `git diff --check` pass.
