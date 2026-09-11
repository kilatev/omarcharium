# Task 17 — Arcade evolution pacing

## Objective

Make births and bounded mutations visible within hours instead of days while
keeping evolution probabilistic.

## Required work

- Set an arcade maturity and reproduction cooldown target.
- Tune the default mutation rate so several births commonly produce a mutation
  without making every birth mutate.
- Keep species-specific trait bounds, generation accounting, and population
  ceilings unchanged.

## Acceptance criteria

- First births occur around the first hour in the standard moving scenario.
- Mutations are commonly observable within several hours over multi-seed runs.
- Reproduction remains deterministic for a fixed seed and does not guarantee a
  mutation on every birth.

## Completion notes

- Set maturity to 60 biological minutes, reproduction cooldown to 30 minutes,
  and the default mutation rate to `0.20`.
- Trait bounds, deterministic replay, species ceilings, and mutation semantics
  remain unchanged.
- Added a 20-seed pacing check: 310 births and mutations in all 20 runs by
  120 biological minutes under direct biological stepping.
