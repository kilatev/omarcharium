# Task 11 — Autonomous falling food

Status: complete. Depends on task 10.

## Objective

Create autonomous feeding scenes without user interaction, following the
[event plan](../docs/LIVING_EVENTS_PLAN.md).

## Required work

- Schedule bounded food portions at seeded random top-edge positions.
- Model sinking, lifetime, amount and consumption separately from regenerating
  algae; expired crumbs disappear without creating unlimited bottom resources.
- Let eligible hungry fish select reachable crumbs and steer toward them.
- Resolve competing consumers deterministically; account for finite energy once.
- Render crumbs and feeding behavior in terminal and lock projections.
- Respect scene quiet intervals; expose an enable toggle through existing
  configuration boundaries and document its default.

## Acceptance criteria

- Seeded fixtures show approach, interception, consumption, and return to cruising.
- No keyboard or pointer input creates food, including on the lock screen.
- Disabled feeding creates no new drops; existing crumbs finish or expire.
- Food and energy stay bounded, including across restart and simultaneous consumers.
- Relevant model, configuration, view, bridge and QML checks pass; record results.

## Completion notes

- Schema 4 persists bounded finite crumbs and the food opportunity timer, with
  migration from schemas 1–3. A first portion is eligible after 90 active seconds;
  later opportunities use the model RNG at 60–180 second intervals.
- Portions contain 4–10 sinking crumbs lasting at most 30 seconds. Hungry
  herbivores steer toward reachable food; ID-ordered consumption accounts for
  finite energy once. Expired crumbs never become regenerating algae.
- The shared scene slot and quiet period gate portions. Disabled/busy opportunities
  are discarded; existing crumbs finish normally. The foodDrops control is wired
  through defaults, Python/QML normalization, persistence, service settings/reset,
  and a control-room toggle. No screensaver or lock input creates food.
- Both renderers draw shared crumb positions; generated QML geometry cases now
  exercise food as well as fish. Documentation describes timing and disabling.
- Verification: 105 Python tests pass, including approach/interception, competing
  consumers, expiration, disabled/busy opportunities, migration, restart replay,
  and Hypothesis food bounds. Generated QML cases and Qt Quick Test pass (3 QML
  passes, no skips); compilation, shell syntax, plugin validation and diff checks
  pass. QML syntax inspection found and fixed a toggle syntax error; remaining
  lint diagnostics concern existing shell types and external lock imports.
- Compliance/diff review found no outstanding task-11 defects. Live installed
  surfaces were not changed or exercised; repository rendering seams were tested.
