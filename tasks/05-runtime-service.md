# Task 05 — Background simulation service

## Objective

Wrap the pure core in a single authoritative service.

## Required behavior

- load JSON model
- generate periodic `Tick` messages
- call pure `update`
- atomically save the returned model
- expose read-only snapshots over private local IPC
- recover from restart and renderer disconnects
- enforce one authoritative writer
- keep the model in memory between checkpoints
- checkpoint compact JSON at most every five minutes
- force checkpoints for reset, simulation-setting changes, explicit saves, and clean shutdown
- atomically replace checkpoints and retain dirty state after failed writes
- serve renderer snapshots from memory without filesystem reads

## Acceptance criteria

Multiple renderers observe one world; renderer frame rate does not control biological time; service failure has a safe fallback.

Property tests cover generated restart/snapshot payloads and malformed IPC inputs at
the public service boundary without exercising inherited renderer code.

Performance tests verify that tick frequency, frame rate, and renderer count do not
increase checkpoint writes, and that snapshot requests do not read the checkpoint
file.
