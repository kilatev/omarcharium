# Task 15 — Advance-path starvation regression

## Objective

Lock down the real moving-simulation path that previously killed the population
before reproduction and mutation could occur.

## Required work

- Add a deterministic multi-seed `Advance` regression scenario.
- Exercise the same fixed-step movement, feeding, biology, and event path used
  by the service.
- Record biological time, population, births, deaths, generations, and mutation
  events at the relevant milestones.

## Acceptance criteria

- The test fails on the pre-fix behavior where all organisms die before the
  first generation.
- The test is deterministic, fast enough for the normal suite, and covers the
  actual `Advance` seam rather than only direct `Tick` calls.

## Completion notes

- Added a deterministic moving-world regression through `update(..., Advance)`.
- The pre-fix scenario produced zero births in 120 biological minutes; it now
  reaches the first reproduction window on seed 7.
