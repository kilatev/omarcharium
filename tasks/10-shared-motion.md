# Task 10 — Shared motion and event timing

Status: complete. Depends on task 09.

## Objective

Make visible movement authoritative across terminal and lock surfaces, providing
the foundation for [living events](../docs/LIVING_EVENTS_PLAN.md).

## Required work

- Define movement-time units, biological-time conversion, bounded fixed substeps,
  and pause/restart policy; keep the scheduler independent of renderer polling.
- Version and migrate JSON state for velocity, heading, behavior, targets,
  cooldowns, shared shelter geometry, and bounded event scheduling state.
- Implement deterministic cruising, boundary handling, and basic separation.
- Connect terminal sprites to snapshot organism IDs and positions; project the
  same movement and shelters into the lock frame. Preserve terminal appearance.
- Add one-scene scheduling and quiet intervals, with no accumulated event queue.
- Preserve read-only adapters, bounded stale-snapshot handling, input behavior,
  and existing checkpoint coalescing.

## Acceptance criteria

- Matching snapshots show the same individuals and world positions on both
  surfaces; viewing never advances the world.
- Legacy checkpoints retain populations, traits, and telemetry after migration.
- Zero/fractional dt, delayed service ticks, and restarts have documented,
  deterministic behavior with bounded processing cost.
- Model/view properties, service/bridge tests, terminal checks and applicable
  Qt Quick Test pass. Record baseline update/snapshot cost for later comparison.

## Completion notes

- Added schema-3 movement state, shared shelters, a fixed 0.1-second pure
  Advance message, bounded catch-up, and a single scene slot with quiet recovery.
- Legacy schema 1/2 migration preserves existing biological state. The pure
  projection now uses authoritative positions and headings.
- Service now advances movement at 0.1-second steps while preserving one
  biological minute per 60 active seconds. Renderers poll read-only snapshots at
  10 Hz, share positions/headings/shelters, and hold the last good fish frame on
  service failure. The existing standalone decorative CLI preview is retained.
- Settings changes preserve telemetry, movement state and RNG; invalid settings
  do not partially modify runtime controls. Decoding enforces population bounds
  and unique organism IDs. No runtime configuration or installed files changed.
- Verification: 99 Python tests, explicit generated QML geometry cases, Qt Quick
  Test (3 passed, no skips), compilation, shell syntax, plugin validation and
  diff whitespace checks pass. Property tests cover split-step replay and restart;
  integration tests cover matching surfaces, stale frames, reader independence,
  biological clock conversion and settings preservation.
- Baseline on this machine, seed 7, maximum 90 fish, 200 movement steps:
  4.75 ms/step (0.0475 CPU seconds per world second); snapshot serialization plus
  120x36 projection 2.24 ms; compact JSON 36,786 bytes after 20 world seconds
  versus 32,093 bytes initially. Timing is indicative, not a portable guarantee.
- Compliance and diff review: task requirements covered by the above checks and
  architecture documentation. Checkpoint coalescing remains unchanged. Live
  installed-lock testing was not performed; repository integration and actual
  Quickshell-free QML geometry were tested.
