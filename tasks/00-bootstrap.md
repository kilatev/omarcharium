# Task 00 — Bootstrap the project

## Objective

Establish the consolidated fork and session handoff structure.

## Context

The upstream plugin is the primary source. The lock-screen adapter and selector are local integrations.

## Required work

- Preserve upstream Git history.
- Keep integrations under `integrations/`.
- Keep biological state separate from user configuration.
- Maintain this plan and the ordered task cards.

## Acceptance criteria

- Existing upstream tests run successfully.
- `scripts/aquarium.py --snapshot --width 80 --height 24 --seed 7` works.
- Integration files are present and documented.

## Verification

```sh
python3 -m unittest discover -s tests -v
python3 scripts/aquarium.py --snapshot --width 80 --height 24 --seed 7
```
