# Task 04 — Pure state rendering

## Objective

Make rendering a pure projection of model state.

## Required interface

```python
frame = view(model, viewport)
```

## Constraints

- no clock or random reads
- no persistence or IPC
- no calls to `update`
- no model mutation
- visual effects derive from model state or deterministic model time

## Acceptance criteria

The same model and viewport always produce the same frame, and rendering cannot alter future simulation results.

Property tests generate models and viewports and verify deterministic frames,
viewport bounds, and that `view()` leaves the model unchanged.
