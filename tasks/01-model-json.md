# Task 01 — Serializable model and JSON state

## Objective

Define a fully JSON-serializable biological model and deterministic initial-world factory.

## Required work

- Add model/entity types with stable IDs.
- Add schema versioning and validation.
- Add JSON round-trip helpers.
- Store deterministic random state in or alongside the model.
- Keep state separate from `config.json`.

## Interface

```python
model = initial_model(seed, settings)
payload = model_to_json(model)
model = model_from_json(payload)
```

## Acceptance criteria

Equivalent models produce identical future updates after round-trip.

## Tests

- round-trip equality
- invalid state fallback
- schema version handling
- deterministic initial state
- Hypothesis-generated valid and malformed payloads preserve the JSON contract.
- Hypothesis finds no mutation of caller-owned input during serialization or parsing.

## Completion notes

- Added `scripts.ecosystem_model` with stable organism/resource IDs, schema version 1,
  deterministic seeded initialization, simulation-only settings, and serialized PRNG state.
- Added strict JSON encoding/decoding with validation and immutable-input coverage.
- Verification: `python3 -m unittest discover -s tests -v` passes (48 tests; Hypothesis
  properties skip when the optional development dependency is not installed).
