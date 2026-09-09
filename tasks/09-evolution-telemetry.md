# Task 09 — Evolution telemetry and terminal statistics

## Objective

Expose truthful evolution progress from the shared ecosystem service without
changing the terminal-native fish animation or lock-screen authentication.

## Required work

- Persist biological elapsed time, births, deaths, and mutation-event counters.
- Accept legacy model checkpoints with zeroed telemetry counters.
- Project species, generation, resource, configuration, and evolution metrics
  through the pure telemetry/view boundary.
- Add a terminal status line and an `I`/`i` statistics overlay backed by shared
  service snapshots.
- Preserve dismissal behavior for all other keyboard, click, and pointer input.
- Document the new controls and record milestone verification here.

## Acceptance criteria

- Shared snapshots report truthful elapsed biological time, population, species,
  generation, births, deaths, mutation events, resources, and ecology settings.
- The terminal status line and statistics overlay remain usable when the service
  is unavailable, with a bounded fallback.
- Statistics polling does not advance time, increase checkpoint writes, or pause
  the animation.
- Lock rendering and authentication remain unchanged.

## Completion notes

- Added persistent schema-2 evolution statistics with schema-1 checkpoint
  fallback, deterministic event accounting, and pure telemetry projection.
- Added cached shared-service polling, a compact evolution status line, and a
  terminal-native `I`/`i` statistics overlay without changing the local fish
  animation or lock surface.
- Preserved ordinary dismissal behavior for all other keyboard, click, and
  pointer input; service failures retain a usable aquarium with `EVO OFFLINE`.
- Documented the telemetry controls and shared-world data boundary.
- Verification: 91 Python tests pass; Python compilation, shell syntax, plugin
  validation, `git diff --check`, and Qt Quick Test pass. Qt Quick Test reports
  one existing placeholder test as skipped.
