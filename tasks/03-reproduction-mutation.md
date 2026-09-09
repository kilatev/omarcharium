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
