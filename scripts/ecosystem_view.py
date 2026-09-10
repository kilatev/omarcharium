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
    from scripts.ecosystem_model import Model, Organism, SPECIES
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from ecosystem_model import Model, Organism, SPECIES


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
    direction = 1 if organism.vx >= 0 else -1
    return {
        "id": organism.id,
        "species": organism.species,
        "kind": style["glyph"],
        "x": round(organism.x * viewport.width, 4),
        "y": round(organism.y * viewport.height, 4),
        "vx": organism.vx,
        "vy": organism.vy,
        "behavior": organism.behavior,
        "width": round(style["size"] * (0.7 + organism.energy * 0.3), 4),
        "height": round(style["size"] * (0.7 + organism.energy * 0.3), 4),
        "direction": direction,
        "colour": style["colour"],
        "energy": organism.energy,
        "generation": organism.generation,
    }


def telemetry(model: Model) -> dict[str, Any]:
    """Project model statistics into JSON-compatible read-only telemetry."""

    if not isinstance(model, Model):
        raise TypeError("model must be a Model")
    species_population = {
        species: sum(organism.species == species for organism in model.organisms)
        for species in SPECIES
    }
    return {
        "biologicalMinutes": model.statistics.biological_minutes,
        "population": len(model.organisms),
        "speciesPresent": sum(value > 0 for value in species_population.values()),
        "speciesTotal": len(SPECIES),
        "speciesPopulation": species_population,
        "resourceCount": len(model.resources),
        "resourceAmount": round(sum(resource.amount for resource in model.resources), 6),
        "generation": max((organism.generation for organism in model.organisms), default=0),
        "births": model.statistics.births,
        "deaths": model.statistics.deaths,
        "mutationEvents": model.statistics.mutation_events,
        "mutationRate": model.settings["mutation_rate"],
        "foodAbundance": model.settings["food_abundance"],
        "predatorPressure": model.settings["predator_pressure"],
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
        "seconds": model.world_time.seconds,
        "scene": model.world_time.scene,
        "shelters": [{"id": item.id, "x": item.x * viewport.width,
                      "y": item.y * viewport.height} for item in model.shelters],
        "resources": resources,
        "organisms": organisms,
        "telemetry": telemetry(model),
    }


__all__ = ["SPECIES_STYLE", "Viewport", "telemetry", "view"]
