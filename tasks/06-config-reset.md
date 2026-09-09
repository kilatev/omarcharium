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
