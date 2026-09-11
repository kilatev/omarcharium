# Task 16 — Motion feeding balance

## Objective

Prevent starvation caused by the interaction between authoritative movement and
the pure food-chain update.

## Required work

- Tune or correct movement-path feeding without breaking the model/update/view
  boundary.
- Preserve bounded energy, resource consumption, population ceilings, and
  possible natural extinction.
- Verify behavior across deterministic seeds and standard event settings.

## Acceptance criteria

- Standard moving simulations survive long enough to reach reproduction.
- No hidden population replacement is introduced.
- Predator pressure and disabled-food scenarios can still produce mortality and
  extinction.

## Completion notes

- Reduced metabolism to `0.0015`, increased resource meals to `0.03`, and
  widened the biological feeding radius to `0.20`.
- Kept starvation and natural extinction possible when food is unavailable.
