# Task 07 — Lock-screen integration

## Objective

Make lock-screen rendering consume shared read-only snapshots.

## Constraints

- authentication remains isolated
- lock input never changes ecosystem state
- all monitors use the shared world
- display blanking pauses frame rendering only
- service failure leaves a usable password field

## Acceptance criteria

Existing lock design selection and password authentication remain functional.
