# Task 14 — Current events and integrated tuning

Status: planned. Depends on task 13.

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

Not started.
