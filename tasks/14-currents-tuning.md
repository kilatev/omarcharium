# Task 14 — Current events and integrated tuning

Status: complete. Depends on task 13.

## Objective

Complete the [event plan](../docs/LIVING_EVENTS_PLAN.md) with currents and
verify that the combined aquarium stays calm, legible and resource-bounded.

## Required work

- Model seeded current pulses with smooth onset/decay and bounded strength.
- Apply the shared flow to food and fish movement; project it into bubbles,
  particles and plant sway without giving decorations biological side effects.
- Keep flow-event strength separate from existing visual water settings and
  document how they combine; fish gradually compensate against the current.
- Finish control-room toggles for food, hunts, shrimp and current events, plus
  one bounded activity-frequency setting. Document defaults and interaction
  with predator pressure, simulation speed, disabling and in-flight scenes.
- Execute multi-seed long-run and performance verification from the event plan;
  tune scene intervals, failed hunts, metabolism and recovery using results.
- Update configuration/user documentation and record limitations and measurements.

## Acceptance criteria

- Currents start/end deterministically, never push entities outside world bounds,
  and consume no more than the single shared major-scene slot.
- Defaults meet the planned calm-time and failed-hunt targets across measured runs;
  extinction remains possible and no hidden population replacement is introduced.
- Snapshot polling on multiple monitors does not change event counts or writes.
- CPU/update costs, entity bounds, checkpoint size/frequency and stale-snapshot
  behavior are measured and documented against task 10's baseline.
- Full applicable AGENTS.md checks and Qt Quick Test pass. Repository verification
  is distinct from any live installed-lock smoke test requiring runtime approval.

## Completion notes

- Added seeded current pulses with 20-second smooth triangular strength, bounded
  direction and a 120–300 second opportunity timer. The current is independent
  of visual `art.current`; fish compensate through shared motion while both
  renderers expose the active pulse. Currents use the single scene slot and keep
  fish inside normalized bounds.
- Added explicit `huntsEnabled`, `currentsEnabled` and `shrimpEnabled` controls;
  all event toggles are normalized, persisted, sent through service settings and
  available in the control room. Disabled opportunities never queue.
- Balance sample (seeds 0–2, 600 active seconds each): 15 hunts, 6 successes and
  9 misses; quiet time 85.52%, 76.45%, 80.52%. Aggregate calm time is 80.83% and
  failed hunts are 60%. Seed 1 remains a tuning watch case; no hidden population
  replacement or extinction prevention was added.
- Verification: 123 Python tests pass, including current pulse, disable/queue,
  replay, bounds, prior event scenarios and property cases. Generated QML
  geometry and Qt Quick Test pass (3 passes, no skips); compilation, shell syntax,
  plugin validation and `git diff --check` pass. Full-shell QML lint retains
  pre-existing external Omarchy type/import warnings.
- Compliance review found no unresolved task-14 defects. Installed runtime state
  was not changed; live lock smoke testing remains outside repository checks.
