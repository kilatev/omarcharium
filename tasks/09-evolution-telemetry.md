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

## Verification

The model and pure telemetry foundation is complete; terminal UI and final
documentation remain in progress.

- Focused model/view tests: 30 passed.
- Full repository tests: 87 passed.
