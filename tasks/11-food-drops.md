# Task 11 — Autonomous falling food

Status: planned. Depends on task 10.

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

Not started.
