# Task 13 — Personalities and shrimp encounters

Status: complete. Depends on task 12.

## Objective

Add small individual stories between major events, following the
[event plan](../docs/LIVING_EVENTS_PLAN.md).

## Required work

- Derive persistent personality differences from bounded traits: territorial,
  curious and shy behavior. Reuse aggression; define any additional traits and
  their migration/inheritance bounds without resetting existing evolution.
- Implement short nonlethal displacement, exploration and shelter preference,
  with cooldowns and escape/hunt priorities preventing conflicting behaviors.
- Add one bounded temporary shrimp entity, bottom movement, shelter escape and
  optional predation through the shared hunt machinery and scene scheduler.
- Distinguish shrimp consumption from fish deaths in telemetry; transfer energy
  once. Expiration is not a kill. No shrimp reproduction in this iteration.
- Render behaviors and shrimp on both surfaces and document enable settings.

## Acceptance criteria

- Seeded examples distinguish personalities without trapping fish in chase loops.
- Threat avoidance overrides exploration/territorial behavior; calm behavior resumes.
- Shrimp escape, consumption, expiration and missing-target cleanup are covered.
- Persistent traits replay identically; temporary entities and timers remain bounded.
- Applicable model/property, configuration, rendering and QML checks pass.

## Completion notes

- Added deterministic personality projection from existing bounded traits:
  aggressive fish are territorial, high diet-preference fish are curious, and
  others are shy. Territorial displacement and curious exploration are short
  nonlethal motion overrides and yield to active threat avoidance or hunts.
- Added one bounded temporary shrimp with seeded bottom spawning, shelter-facing
  escape, expiration, and optional predator consumption. Shrimp catches transfer
  finite energy and increment separate telemetry; they do not increment fish
  deaths or reproduce. Persistence accepts at most one shrimp and migrates older
  checkpoints with an empty list.
- Added shared terminal/lock projection, `shrimpEnabled` defaults and control
  plumbing, and JSON-safe counters. The existing scene slot prevents concurrent
  major scenes and keeps shrimp encounters rare.
- Verification: personality, exploration, territorial, escape, catch, expiration,
  missing cleanup, replay and no-death tests pass. Full suite and generated QML
  checks recorded with task 14.
