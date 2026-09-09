"""Pure visual projection for the autonomous ecosystem.

The renderer adapter may turn this frame into terminal, QML, or lock-screen
draw calls.  This module deliberately has no clock, random source, I/O, or
simulation update step.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

try:
    from scripts.ecosystem_model import Model, Organism
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from ecosystem_model import Model, Organism


@dataclass(frozen=True, slots=True)
class Viewport:
    width: int
    height: int

    def __post_init__(self) -> None:
        if isinstance(self.width, bool) or not isinstance(self.width, int) or self.width < 1:
            raise ValueError("viewport width must be a positive integer")
        if isinstance(self.height, bool) or not isinstance(self.height, int) or self.height < 1:
            raise ValueError("viewport height must be a positive integer")


SPECIES_STYLE: dict[str, dict[str, Any]] = {
    "neon_tetra": {"glyph": "fish", "colour": "#45f3ff", "size": 0.75},
    "clownfish": {"glyph": "fish", "colour": "#ff8a3d", "size": 0.95},
    "angelfish": {"glyph": "fish", "colour": "#f7e8a4", "size": 1.2},
    "discus": {"glyph": "fish", "colour": "#ff5ca8", "size": 1.05},
    "butterflyfish": {"glyph": "fish", "colour": "#ffe45d", "size": 0.95},
    "royal_tang": {"glyph": "fish", "colour": "#5899ff", "size": 1.0},
    "betta": {"glyph": "fish", "colour": "#c681ff", "size": 1.1},
    "puffer": {"glyph": "fish", "colour": "#a9f37d", "size": 1.0},
}


def _phase(identifier: str) -> float:
    """Return a stable unit phase without using process-randomized hashing."""

    digest = hashlib.blake2b(identifier.encode("utf-8"), digest_size=2).digest()
    return int.from_bytes(digest, "big") / 65535.0


def _organism_frame(organism: Organism, viewport: Viewport, tick: int) -> dict[str, Any]:
    style = SPECIES_STYLE[organism.species]
    phase = _phase(organism.id)
    # A tick is biological time owned by the model; it is not wall-clock time.
    direction = 1 if int((phase * 17) + tick // 8) % 2 == 0 else -1
    bob = ((phase + tick / 37.0) % 1.0 - 0.5) * 0.018
    return {
        "id": organism.id,
        "species": organism.species,
        "kind": style["glyph"],
        "x": round(organism.x * viewport.width, 4),
        "y": round(max(0.0, min(1.0, organism.y + bob)) * viewport.height, 4),
        "width": round(style["size"] * (0.7 + organism.energy * 0.3), 4),
        "height": round(style["size"] * (0.7 + organism.energy * 0.3), 4),
        "direction": direction,
        "colour": style["colour"],
        "energy": organism.energy,
        "generation": organism.generation,
    }


def view(model: Model, viewport: Viewport) -> dict[str, Any]:
    """Project a model into JSON-compatible render data without mutation."""

    if not isinstance(model, Model):
        raise TypeError("model must be a Model")
    if not isinstance(viewport, Viewport):
        raise TypeError("viewport must be a Viewport")

    resources = [
        {
            "id": resource.id,
            "kind": resource.kind,
            "x": round(resource.x * viewport.width, 4),
            "y": round(resource.y * viewport.height, 4),
            "radius": round(0.25 + resource.amount * 0.75, 4),
            "amount": resource.amount,
        }
        for resource in sorted(model.resources, key=lambda item: item.id)
    ]
    organisms = [
        _organism_frame(organism, viewport, model.tick)
        for organism in sorted(model.organisms, key=lambda item: item.id)
    ]
    return {
        "schemaVersion": 1,
        "width": viewport.width,
        "height": viewport.height,
        "tick": model.tick,
        "resources": resources,
        "organisms": organisms,
        "telemetry": {
            "population": len(organisms),
            "resourceCount": len(resources),
            "generation": max((item["generation"] for item in organisms), default=0),
        },
    }


__all__ = ["SPECIES_STYLE", "Viewport", "view"]
