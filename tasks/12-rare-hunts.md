# Task 12 — Distinct predators and rare hunts

Status: complete. Depends on task 11.

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

- Replaced proximity-only predation for every predator with a shared hunt scene:
  eligibility, 0.7-second preparation, finite pursuit, contact success or miss,
  and mandatory 120–240 second recovery (180–300 for reef_hunter). Pressure zero
  cancels/prevents hunts; positive pressure scales opportunities. Satiated fish
  cannot start. Invalid/missing targets abort without transferring energy.
- Added reef_stalker and reef_hunter across model, traits, population caps,
  catalog, defaults, controls, terminal sprites and distinct lock proportions.
  Existing saves retain their individuals. An explicit reset applies configured
  populations through the client/service; new worlds default to one stalker.
- Added predator avoidance, burst escape and gradual species regrouping.
  Schema 5 persists active hunts and counters; migration accepts schemas 1–4.
  Biological ticks preserve hunt statistics and never kill prey by proximity.
- Finite kill energy is capped at 0.25 and 60% of prey energy. Existing metabolism
  costs only 0.01–0.025 over a full recovery, so a healthy hunter can rest without
  exhausting its energy solely because of the cooldown. Starvation stays possible.
- Initial seed 0/1/2 runs, 600 active seconds each: 5 hunts in every run;
  successes 3/2/1, remaining population 26/27/28; quiet time 85.52%/76.45%/80.52%.
  Aggregate misses exceed successes (9 vs 6). Task 14 must investigate the lower
  quiet-time seed and long-run starvation/population balance across 20 seeds.
- Verification: 115 Python tests pass, including hunt eligibility, contact/miss,
  missing target, zero pressure, one scene, outside-scene safety, JSON replay,
  counters, bounded new populations and explicit reset. Generated QML geometry
  cases and Qt Quick Test pass (3 passes, no skips). Compilation, shell syntax,
  plugin validation and diff checks pass. QML syntax passes; full-shell lint
  retains known external-type/import diagnostics.
- Fukit compliance/diff review found no outstanding task-12 defect. Runtime and
  installed plugin files remain untouched; live lock testing was not performed.
