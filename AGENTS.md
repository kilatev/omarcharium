# Omarcharium agent workflow

## Working agreement

- Treat this repository as the source of truth. Do not edit the installed copy
  or `/usr/share/omarchy/` during ordinary development.
- Read `IMPLEMENTATION_PLAN.md`, the assigned `tasks/*.md` card, and the current
  Git/Jujutsu status before implementation.
- Work only on the assigned task unless the user explicitly expands the scope.
- Preserve the pure model/update/view boundary described in
  `IMPLEMENTATION_PLAN.md`.
- Do not commit `CONTINUE.md`, generated caches, or `__pycache__` files.

## Routine verification

These commands are safe routine checks for this project:

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/aquarium.py
bash -n scripts/launch-aquarium scripts/idle-integration scripts/select-backdrop
omarchy plugin validate .
git diff --check
```

Run the narrowest relevant check after each change, then the full applicable
suite before handoff. QML changes also require Qt Quick Test when available.

## Approval boundaries

Ask before installing or upgrading dependencies, using networked shell
commands, changing system or Omarchy runtime state, synchronizing the installed
plugin, pushing or publishing Git history, or rewriting history.

Never use broad destructive cleanup or reset commands. Use targeted,
recoverable edits and preserve unrelated user changes.
