# Task 19 — Evolution verification and handoff

## Objective

Verify the complete evolution fix and record reproducible results for handoff.

## Required work

- Run the focused regression and multi-seed long-run checks.
- Run all applicable repository checks from `AGENTS.md`.
- Record performance and pacing measurements in the completion notes.
- Leave installed runtime state untouched.

## Acceptance criteria

- Focused and full applicable tests pass.
- Population, births, mutations, bounds, replay, and extinction behavior are
  all covered by passing checks.
- No debug instrumentation, generated cache, or `__pycache__` is committed.

## Completion notes

- Full Python suite: 127 tests passed.
- Twenty seeded one-day biological runs produced 542 births, 336 deaths, 199
  mutation events, and 20 surviving worlds.
- The moving `Advance` regression passed for seed 7 within the 120-minute arcade
  window.
- Python compilation, shell syntax, plugin validation, and `git diff --check`
  passed. Qt Quick Test was unavailable because `qmltestrunner` is not installed.
- Installed runtime state was not changed.
