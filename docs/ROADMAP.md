# Mission and roadmap

## Mission

Omarcharium exists to make the desktop feel alive without making it noisy. It
turns Omarchy's terminal, shell, and idle surfaces into a calm, local-first
aquarium: a small ecosystem that changes over time, remains pleasant to watch,
and stays respectful of the system it inhabits.

The project has four commitments:

- **Life over looping:** the reef is driven by an autonomous model rather than
  a pre-rendered animation.
- **Omarchy-native integration:** the aquarium belongs in the tray, terminal,
  idle, and lock workflows while leaving first-party locking in control.
- **Local and conservative:** no runtime network service, bundled media,
  privileged installation, or unnecessary background process.
- **Inspectable engineering:** simulation state is serializable, updates are
  deterministic and testable, and visual configuration stays separate from
  biological state.

## Roadmap

The ecosystem is being built in small, verifiable milestones. The first three
feature tasks establish the biological core before service infrastructure is
expanded.

1. **Bootstrap** — consolidate the fork, integrations, task cards, and handoff
   conventions. Complete.
2. **Model and JSON state** — define stable entities, schema validation,
   deterministic initialization, and restart-safe random state. Complete.
3. **Pure food chain** — add resources, feeding, predation, energy, and death
   as deterministic state transitions. Complete.
4. **Reproduction and mutation** — add inheritance, bounded traits, and
   generational evolution. Complete.
5. **Pure view** — project model snapshots into render data without advancing
   or mutating the simulation. Complete.
6. **Runtime service** — run one shared world, expose read-only snapshots, and
   persist coalesced checkpoints. Complete.
7. **Configuration and reset** — expose ecosystem controls while preserving
   the existing visual/audio configuration contract. Complete.
8. **Lock integration** — render the same shared world on the lock surface
   without allowing lock input to change ecosystem state. Complete.
9. **Tuning and release** — tune calm long-running behavior, profile resource
   bounds, document the finished model, and ship it as a stable release. Core
   tuning and documentation are complete; release refinement remains optional.

The ecosystem core, pure view, runtime service, configuration, terminal
renderer, and lock-surface rendering are implemented. The visual work is
complete; ongoing tuning and future visual refinement remain ordinary
follow-up work rather than unimplemented architecture.

The detailed engineering contract and acceptance criteria live in
[IMPLEMENTATION_PLAN.md](../IMPLEMENTATION_PLAN.md). Each milestone has a
corresponding card under [`tasks/`](../tasks/).

## Design boundary

```text
Model + Message -> update() -> Model
Model + Viewport -> view() -> Frame
```

Time, randomness, persistence, IPC, and process lifecycle stay at the edges.
This boundary lets the same world be replayed in tests, rendered on multiple
monitors, and recovered after restart without coupling biology to the shell.
