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
bash -n scripts/launch-aquarium scripts/idle-integration scripts/select-backdrop scripts/sync-installed-plugin
omarchy plugin validate .
git diff --check
```

Run the narrowest relevant check after each change, then the full applicable
suite before handoff. QML changes also require Qt Quick Test when available.

## Approval boundaries

Ask before installing or upgrading dependencies, using unrelated networked shell
commands, changing system or Omarchy runtime state, synchronizing the installed
plugin, or rewriting history. An explicit user invocation of `fukit` authorizes
its validated, task-scoped Jujutsu description, bookmark update, push preview,
and push; do not ask for a second confirmation once the required checks pass.
Standalone pushes and publication outside `fukit` remain approval-gated.

Never use broad destructive cleanup or reset commands. Use targeted,
recoverable edits and preserve unrelated user changes.

## Installed runtime handoff

- The repository is the source of truth; the installed copy is updated only by
  `scripts/sync-installed-plugin`.
- That script copies runtime files without `.git`, preserves user configuration
  and ecosystem state, validates the installed plugin, and restarts the
  Omarchy shell so `Service.qml` reloads the current ecosystem service.
- After a successful explicit `fukit` workflow, run
  `scripts/sync-installed-plugin` as its final post-push handoff. A standalone
  invocation still requires approval because it changes live Omarchy state.
- Verify the handoff with two snapshot reads. The installed service must emit
  the current schema and organism coordinates must change between reads.
