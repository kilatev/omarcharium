# Task 08 — Tuning and release quality

## Objective

Tune the ecosystem for calm, long-running screensaver behavior.

## Required work

- tune food growth, metabolism, predator pressure, and extinction probability
- verify hours/days generational pacing
- profile CPU and memory
- add long-running deterministic tests
- update architecture, configuration, and troubleshooting docs

## Acceptance criteria

Population remains bounded, changes are observable over time, extinction is possible but not immediate, and multiple monitors do not multiply biological activity.

## Completion notes

- Tuned the model for one biological minute per default service tick, with calmer
  resource regeneration/metabolism and 12-hour maturity plus 4-hour cooldown
  pacing; diagnostic acceleration is isolated to the service adapter.
- Added a deterministic 2,000-minute long-run test proving continued life,
  generational change, turnover, and population ceilings.
- Documented pacing, configuration semantics, service ownership, and the remaining
  visual/lock-surface boundary in the architecture and configuration references.
- Profiled the long-run model locally: 2,000 ticks complete in 0.345s user time
  with 15,896 KiB peak RSS; the model stores bounded tuples/collections only.
- Verification: full test suite passes; Python compile, shell syntax, plugin
  validation, and `git diff --check` pass. Qt Quick Test is unavailable here.
