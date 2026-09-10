# Task 12 — Distinct predators and rare hunts

Status: planned. Depends on task 11.

## Objective

Make predation a rare visible sequence with long recovery, following the
[event plan](../docs/LIVING_EVENTS_PLAN.md).

## Required work

- Replace proximity-only killing for every existing predator with eligibility
  based on hunger, valid prey, individual cooldown and shared scene availability.
- Model idle/ambush/patrol, preparation, pursuit, success/miss and recovery;
  require contact during pursuit for a kill and abort when a target disappears.
- Introduce reef_stalker first, then reef_hunter, with distinct silhouettes,
  movement profiles, trait bounds, population caps and configuration entries.
- Extend model, species catalog, terminal sprites, lock styles, configuration
  normalization and telemetry consistently; migrate old saves without auto-spawn.
- Add predator avoidance, burst escape and gradual shoal regrouping.
- Balance metabolism, finite energy transfer, and cooldown after every attempt;
  predator pressure zero prevents hunts and kills.

## Acceptance criteria

- Fixtures cover satiated/resting predators, misses, contact kills, invalid
  targets, simultaneous competitors, no prey, and restart during pursuit/rest.
- No predator kills outside pursuit or consumes the same target twice.
- Both new species are visually recognizable on both surfaces; existing species
  retain valid save/config behavior.
- Initial multi-seed runs show mostly failed hunts and extended calm periods;
  remaining tuning is recorded for task 14, including starvation risks.
- Applicable model/property, config, telemetry, rendering and QML checks pass.

## Completion notes

Not started.
