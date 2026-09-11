# Omarcharium Living Ecosystem

This fork adds an autonomous ecosystem while preserving Omarcharium's terminal-native renderer and Omarchy integrations.

## Architecture

The biological core follows a strict Elm-style boundary:

```text
Model + Message -> update() -> Model
Model + Viewport -> view() -> Frame
```

`update(model, message)` is deterministic and side-effect free. It does not read clocks, files, environment variables, renderers, IPC, or global randomness. Time, randomness, persistence, IPC, and process lifecycle are adapters around the core.

`view(model, viewport)` is a pure projection. Rendering never advances time, mutates populations, performs persistence, or communicates with the simulation service.

Biological state is JSON-serializable and stored separately from visual configuration:

- Configuration: `~/.config/omarcharium/config.json`
- State: `~/.local/state/omarcharium/ecosystem.json`

The background service owns one shared world for all monitors. Renderers receive read-only snapshots.

Persistence is checkpoint-based: the service keeps the authoritative model in
memory, marks it dirty after updates, and writes one compact JSON checkpoint at
most every five minutes. Reset, simulation-setting changes, explicit saves, and
clean shutdowns force an immediate checkpoint. Renderers never read the state file.

## Property-based testing

Property-based tests apply only to code introduced by this fork for the autonomous
ecosystem. The inherited terminal renderer, existing upstream tests, and existing
Omarchy integrations remain outside this test scope and must not be refactored just
to make them property-testable.

Python ecosystem seams are tested with Hypothesis. The test-only dependency is
declared in `requirements-dev.txt`; it is never needed by the installed plugin.
Generated cases cover JSON models, configuration, message sequences, viewports, and
timesteps. Required properties include JSON round-trips, deterministic replay,
bounded state, input immutability, pure update/view behavior, and safe malformed
input recovery. Hypothesis settings must retain the seed and minimized example in
failure output.

QML property testing is limited to new Quickshell-free QML/JavaScript helpers. They
are exercised with Qt Quick Test through `qmltestrunner`. Python Hypothesis supplies
JSON fixture cases to the QML test boundary so a failing cross-language case can be
reproduced without loading the Quickshell-dependent shell entry points. Shell wiring
continues to use focused smoke and live-surface checks.

## Ordered tasks

1. `tasks/00-bootstrap.md` — workspace and handoff structure
2. `tasks/01-model-json.md` — serializable model and state contract
3. `tasks/02-pure-food-chain.md` — pure resources, eating, predation, death
4. `tasks/03-reproduction-mutation.md` — reproduction, inheritance, evolution
5. `tasks/04-pure-view.md` — render only model state
6. `tasks/05-runtime-service.md` — background service, IPC, persistence adapter
7. `tasks/06-config-reset.md` — configuration and reset controls
8. `tasks/07-lock-integration.md` — shared read-only lock rendering
9. `tasks/08-tuning-release.md` — tuning, profiling, documentation
10. `tasks/09-evolution-telemetry.md` — evolution telemetry and terminal statistics
11. `tasks/10-shared-motion.md` — authoritative movement and shared event timing
12. `tasks/11-food-drops.md` — autonomous falling food and feeding response
13. `tasks/12-rare-hunts.md` — distinct predators, rare hunts, and recovery
14. `tasks/13-fish-personalities.md` — schooling, personalities, and shrimp encounters
15. `tasks/14-currents-tuning.md` — current events and integrated pacing verification

Tasks 10–13 are complete; task 14 remains planned. Their product scope, initial tuning
targets, dependencies, and cross-cutting acceptance criteria are defined in
[`docs/LIVING_EVENTS_PLAN.md`](docs/LIVING_EVENTS_PLAN.md).

The first three feature tasks provide most of the value and should be completed before investing in service infrastructure.

## Session protocol

Each implementation session must read this file, its assigned task card, the previous task's completion notes, and current Git/Jujutsu status. Work only on the assigned task, run its verification commands, record results in the task card or commit message, and leave the project runnable.

## Definition of done

- `update(model, message)` is pure and deterministic.
- `view(model, viewport)` is pure and deterministic.
- Biological state round-trips through JSON.
- Seaweed/resources feed fish; predators eat fish.
- Reproduction and bounded mutation work.
- Extinction is possible and reset restores a viable world.
- One background service owns the shared world.
- All monitors render read-only snapshots of the same world.
- Existing aquarium, lock-screen, and authentication behavior remains functional.
- Fork-owned ecosystem properties pass under Hypothesis and Qt Quick Test.
- CI installs and runs both property-test suites; missing required tooling fails CI.
- No runtime dependency is introduced for property testing.
- JSON persistence is limited to coalesced checkpoints and does not run per tick,
  per frame, or per renderer.
- A completed checkpoint is flushed and atomically replaced; failed writes leave
  the in-memory model dirty for retry.
- Evolution telemetry is derived from the authoritative model and remains pure at
  the update/view boundary; terminal statistics must not pause or mutate the
  simulation.
