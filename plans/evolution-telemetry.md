# Goal: Add evolution telemetry and a statistics overlay

## Objective

Add a terminal-only evolution status line and an `I`/`i` hotkey that opens a
full-screen statistics view. The displayed data must come from the authoritative
shared ecosystem service. The existing terminal fish animation remains unchanged
in this goal.

The lock screen and password interaction remain untouched.

## Scope

### Biological model and persistence

- Extend the biological model with persistent evolution statistics:
  - biological elapsed minutes;
  - cumulative births;
  - cumulative deaths;
  - cumulative mutation events.
- Count one mutation event when an offspring receives at least one mutated trait.
- Reset all counters on ecosystem reset.
- Upgrade the model JSON schema while accepting older checkpoints with zeroed
  statistics.
- Preserve deterministic replay, JSON round-tripping, and checkpoint recovery.

### Telemetry projection

Expand the pure telemetry projection to include:

- elapsed biological time;
- current population;
- species present and total species;
- per-species population;
- maximum generation;
- births, deaths, and mutation events;
- resource count and total resource amount;
- configured mutation rate, food abundance, and predator pressure.

The existing snapshot IPC operation remains unchanged; it returns the expanded
model data through the existing snapshot payload.

### Terminal interface

- Poll the shared service snapshot at a low rate, approximately once per second.
- Do not let polling affect biological time, rendering cadence, or checkpoint
  frequency.
- Reuse the existing `art.showTelemetry` setting for the status line.
- Render a compact top-line summary containing biological time, population,
  species-present count, maximum generation, and mutation events.
- If the service is unavailable, keep the aquarium running and show a bounded
  `EVO OFFLINE` fallback indicator.
- Reserve `I` and `i`:
  - toggle the statistics screen;
  - all other keyboard input still dismisses the screensaver;
  - clicks and pointer movement still dismiss it.
- Opening the statistics screen does not pause the service or local animation.
- Render a terminal-native, responsive statistics screen showing:
  - shared-world elapsed biological time;
  - total population and species-present count;
  - per-species populations;
  - generation, births, deaths, and mutation events;
  - resource totals;
  - food abundance, predator pressure, and configured mutation rate;
  - service availability.

### Documentation and task tracking

- Add a new ordered task card for telemetry/statistics.
- Update `IMPLEMENTATION_PLAN.md` with the new task and acceptance criteria.
- Update architecture, configuration, roadmap, and terminal-controls
  documentation.
- Record verification results in the task card.

## Public interfaces and data contracts

- Keep `update(model, message)` pure and deterministic.
- Keep `view(model, viewport)` and telemetry projection pure and deterministic.
- Extend the model dataclass and JSON encoder/decoder with statistics while
  preserving safe recovery from older valid checkpoints.
- Keep the Unix-socket protocol operations unchanged: `snapshot`, `reset`,
  `settings`, and `save`.
- Treat biological elapsed time as simulation time, not process uptime.
- Mutation counts are cumulative since the latest ecosystem reset and are
  persisted in checkpoints.

## Tests and acceptance criteria

Add or update tests covering:

- statistics initialization, accumulation, reset, bounds, and deterministic
  replay;
- mutation-event counting when zero, one, or both traits mutate;
- schema round-trip and legacy-checkpoint fallback;
- expanded telemetry and per-species counts;
- service-backed terminal polling and offline fallback;
- `I`/`i` toggling versus dismissal for other input;
- compact status and overlay rendering at minimum supported dimensions;
- unchanged lock bridge behavior.

The goal is complete when:

- the shared model reports truthful evolution duration, species, generations,
  births, deaths, and mutation events;
- the terminal status line is visible when telemetry is enabled;
- `I` opens and closes the statistics screen without changing simulation state;
- unrelated input still dismisses the terminal immersion;
- service failure degrades to the existing aquarium plus a bounded fallback;
- lock authentication and lock rendering behavior remain unchanged;
- all repository checks pass:

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/aquarium.py
bash -n scripts/launch-aquarium scripts/idle-integration scripts/select-backdrop
omarchy plugin validate .
git diff --check
/usr/lib/qt6/bin/qmltestrunner -input tests/qml
```

## Constraints and assumptions

- Work only on this feature; preserve unrelated working-copy edits.
- Do not edit the installed plugin or `/usr/share/omarchy/`.
- Do not add a runtime dependency for property testing or telemetry.
- Keep the lock surface unchanged in this goal.
- The terminal’s existing local fish animation remains decorative; the status
  and statistics describe the authoritative shared service world.
- Do not commit this goal file unless explicitly requested.
