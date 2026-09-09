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

## Completion notes

- Replaced the per-monitor standalone renderer with read-only requests to the
  shared ecosystem service and the pure `ecosystem_view` projection.
- Added a bounded empty-frame fallback for service failure; lock input remains
  owned by Lock Explorer and display blanking still pauses frame requests.
- Updated the lock canvas to render resources and organisms from shared frame
  data, preserving the password field and selector integration.
