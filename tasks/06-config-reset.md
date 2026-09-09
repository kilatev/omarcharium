# Task 06 — Configuration and reset controls

## Objective

Expose configuration-only controls without allowing direct biological mutation.

## Controls

- ecosystem enable/disable
- simulation speed
- starting seed
- food abundance
- mutation rate
- predator pressure
- reset ecosystem
- diagnostic accelerated mode

## Acceptance criteria

Controls update configuration or dispatch an explicit reset; reset preserves visual/audio settings and creates a valid initial model.

Property tests generate control values and verify bounded normalization, preservation
of unrelated settings, and valid reset state.

## Completion notes

- Added a pure ecosystem configuration adapter with bounded enable, speed, seed,
  food, mutation, predator, and diagnostic controls.
- Added immutable control updates, explicit reset semantics preserving unrelated
  visual/audio configuration, and biological-settings translation for the service.
- Added packaged/QML configuration schema fields and service-client synchronization
  without changing rendering or visual effects.
- Added unit and Hypothesis coverage for malformed values, bounds, preservation,
  normalization, and control updates.
- Verification: 71 tests pass; Python compile, shell syntax, plugin validation, and
  `git diff --check` pass. Qt Quick Test remains unavailable in this environment.
