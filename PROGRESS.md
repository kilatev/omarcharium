# Progress

## 2026-09-09 — Pure view milestone complete

- Completed: added deterministic `scripts.ecosystem_view.view(model, viewport)`
  projection with bounded organism/resource render data and telemetry; added
  unit and Hypothesis coverage; recorded task 04 completion.
- Validation: 81 tests pass; Python compile, shell syntax, plugin validation,
  and `git diff --check` pass. Qt Quick Test remains unavailable.
- Published: `ae398c87` / `feat(ecosystem): add pure model view projection`.
- Remaining: connect lock rendering to shared service snapshots and verify lock
  input, blanking, and renderer-failure behavior.
- Next action: implement and test task 07 lock-surface integration.

## 2026-09-09 — Shared lock rendering milestone complete

- Completed: lock rendering now consumes read-only snapshots from the single
  ecosystem service through the pure view projection; Canvas draws resources
  and organisms; custom image backdrops, password input, pointer wake, and
  blanking behavior remain supported; service failure has an empty safe frame.
- Validation: 84 tests pass; Qt Quick Test passes (2 passed, 1 pre-existing
  skipped); Python compile, shell syntax, plugin validation, and `git diff
  --check` pass. `qmllint` exits successfully with only known external-type
  warnings.
- Published: `b6fa10ca` / `feat(lock): render the shared ecosystem snapshot`.
- Remaining: none for the requested visual scope; future work is optional tuning
  and release refinement.
- Next action: final verification and handoff.

## 2026-09-09 — Evolution telemetry foundation milestone complete

- Completed: model schema 2 now persists biological elapsed minutes, births,
  deaths, and per-offspring mutation events; schema 1 checkpoints recover with
  zeroed counters; pure telemetry reports species, generations, resources, and
  ecology settings.
- Validation: 87 Python tests pass, including focused legacy-schema, counter,
  mutation, and telemetry coverage.
- Remaining: terminal service polling, compact status line, `I`/`i` statistics
  overlay, and final documentation.
- Next action: implement the terminal telemetry adapter and statistics screen.
