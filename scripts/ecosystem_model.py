"""Serializable biological state for the autonomous aquarium.

The model deliberately contains simulation state only. Visual and audio
configuration remains owned by ``Config.qml`` and is not accepted here.
"""

from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass
from collections.abc import Mapping
from typing import Any


MODEL_SCHEMA_VERSION = 1
SPECIES = (
    "neon_tetra",
    "clownfish",
    "angelfish",
    "discus",
    "butterflyfish",
    "royal_tang",
    "betta",
    "puffer",
)
DEFAULT_POPULATION = {
    "neon_tetra": 10,
    "clownfish": 4,
    "angelfish": 3,
    "discus": 3,
    "butterflyfish": 2,
    "royal_tang": 3,
    "betta": 1,
    "puffer": 2,
}
MAX_POPULATION = {
    "neon_tetra": 20,
    "clownfish": 12,
    "angelfish": 10,
    "discus": 10,
    "butterflyfish": 10,
    "royal_tang": 12,
    "betta": 6,
    "puffer": 10,
}

HERBIVORES = frozenset(("neon_tetra", "clownfish", "discus", "royal_tang"))
PREDATORS = frozenset(("angelfish", "butterflyfish", "betta", "puffer"))
RESOURCE_REGENERATION = 0.08
METABOLISM = 0.035
RESOURCE_MEAL = 0.18
PREDATOR_MEAL = 0.35
FEEDING_RADIUS = 0.16
PREDATION_RADIUS = 0.12


class ModelValidationError(ValueError):
    """Raised when persisted biological state is not a valid model."""


@dataclass(frozen=True)
class Resource:
    id: str
    kind: str
    x: float
    y: float
    amount: float


@dataclass(frozen=True)
class Organism:
    id: str
    species: str
    x: float
    y: float
    energy: float
    age: int = 0
    generation: int = 0


@dataclass(frozen=True)
class Model:
    schema_version: int
    seed: int
    tick: int
    settings: dict[str, Any]
    resources: tuple[Resource, ...]
    organisms: tuple[Organism, ...]
    random_state: tuple[Any, ...]


@dataclass(frozen=True)
class Tick:
    """Advance the biological model by a non-negative number of seconds."""

    dt: float


@dataclass(frozen=True)
class Reset:
    """Create a new deterministic world without changing visual configuration."""

    seed: int
    starting_population: Mapping[str, int] | None = None


def _json_value(value: Any) -> Any:
    """Copy tuples into JSON arrays without retaining caller-owned objects."""

    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    raise ModelValidationError(f"value is not JSON serializable: {type(value).__name__}")


def _number(value: Any, *, name: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ModelValidationError(f"{name} must be a number")
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        raise ModelValidationError(f"{name} must be finite")
    if not minimum <= number <= maximum:
        raise ModelValidationError(f"{name} is outside its allowed range")
    return number


def _integer(value: Any, *, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ModelValidationError(f"{name} must be an integer >= {minimum}")
    return value


def _settings(settings: Mapping[str, Any] | None, *, normalize: bool = True) -> dict[str, Any]:
    incoming = settings if settings is not None else {}
    if not isinstance(incoming, Mapping):
        raise ModelValidationError("settings must be an object")
    population = incoming.get("species", incoming.get("starting_population", {}))
    if population is None:
        population = {}
    if not isinstance(population, Mapping):
        raise ModelValidationError("species must be an object")
    for species, value in population.items():
        if species in SPECIES and (isinstance(value, bool) or not isinstance(value, int)):
            raise ModelValidationError(f"population for {species} must be an integer")
    normalized_population = {}
    for species in SPECIES:
        value = population.get(species, DEFAULT_POPULATION[species])
        if normalize:
            value = max(0, min(MAX_POPULATION[species], value))
        elif value < 0 or value > MAX_POPULATION[species]:
            raise ModelValidationError(f"population for {species} is outside its allowed range")
        normalized_population[species] = value
    return {
        "species": normalized_population,
        "food_abundance": _number(incoming.get("food_abundance", 1.0), name="food_abundance", minimum=0.0, maximum=2.0),
        "predator_pressure": _number(incoming.get("predator_pressure", 1.0), name="predator_pressure", minimum=0.0, maximum=2.0),
    }


def initial_model(seed: int, settings: Mapping[str, Any] | None = None) -> Model:
    """Build the same viable initial world for the same seed and settings."""

    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    normalized = _settings(settings)
    rng = random.Random(seed)
    resources = tuple(
        Resource(
            id=f"resource-{index:04d}",
            kind="seaweed",
            x=round(rng.random(), 6),
            y=round(rng.random(), 6),
            amount=round(0.65 + rng.random() * 0.35, 6),
        )
        for index in range(24)
    )
    organisms: list[Organism] = []
    serial = 0
    for species in SPECIES:
        for _ in range(normalized["species"][species]):
            serial += 1
            organisms.append(
                Organism(
                    id=f"organism-{serial:04d}",
                    species=species,
                    x=round(rng.random(), 6),
                    y=round(rng.random(), 6),
                    energy=round(0.7 + rng.random() * 0.3, 6),
                )
            )
    return Model(
        schema_version=MODEL_SCHEMA_VERSION,
        seed=seed,
        tick=0,
        settings=copy.deepcopy(normalized),
        resources=resources,
        organisms=tuple(organisms),
        random_state=rng.getstate(),
    )


def _distance(left: Organism, right: Organism | Resource) -> float:
    """Return toroidal distance, matching the normalized aquarium coordinates."""

    dx = abs(left.x - right.x)
    dy = abs(left.y - right.y)
    dx = min(dx, 1.0 - dx)
    dy = min(dy, 1.0 - dy)
    return math.hypot(dx, dy)


def _valid_dt(dt: Any) -> float:
    if isinstance(dt, bool) or not isinstance(dt, (int, float)):
        raise ValueError("Tick.dt must be a number")
    value = float(dt)
    if not math.isfinite(value) or value < 0:
        raise ValueError("Tick.dt must be finite and non-negative")
    return value


def _tick(model: Model, message: Tick) -> Model:
    dt = _valid_dt(message.dt)
    abundance = model.settings["food_abundance"]
    pressure = model.settings["predator_pressure"]
    resources = [
        Resource(resource.id, resource.kind, resource.x, resource.y,
                 min(1.0, resource.amount + RESOURCE_REGENERATION * abundance * dt))
        for resource in model.resources
    ]

    # Metabolism happens before feeding, so a fish cannot survive indefinitely
    # on a depleted resource.  Processing in stable ID order makes collisions
    # deterministic and independent of container identity.
    living = [
        Organism(
            organism.id,
            organism.species,
            organism.x,
            organism.y,
            organism.energy - METABOLISM * dt,
            organism.age + (1 if dt > 0 else 0),
            organism.generation,
        )
        for organism in sorted(model.organisms, key=lambda item: item.id)
    ]
    living = [organism for organism in living if organism.energy > 0]

    for index, organism in enumerate(living):
        if organism.species not in HERBIVORES:
            continue
        nearby = [
            (resource_index, resource)
            for resource_index, resource in enumerate(resources)
            if resource.amount > 0 and _distance(organism, resource) <= FEEDING_RADIUS
        ]
        if not nearby:
            continue
        resource_index, resource = min(nearby, key=lambda pair: (pair[1].id, pair[0]))
        meal = min(RESOURCE_MEAL * max(0.0, dt), resource.amount)
        resources[resource_index] = Resource(
            resource.id, resource.kind, resource.x, resource.y, resource.amount - meal
        )
        updated = living[index]
        living[index] = Organism(
            updated.id, updated.species, updated.x, updated.y,
            min(1.0, updated.energy + meal), updated.age, updated.generation
        )

    living_by_id = {organism.id: organism for organism in living}
    eaten: set[str] = set()
    for predator in sorted(living, key=lambda item: item.id):
        if predator.species not in PREDATORS or pressure <= 0:
            continue
        candidates = [
            prey for prey in living
            if prey.id != predator.id and prey.id not in eaten
            and prey.species not in PREDATORS
            and _distance(predator, prey) <= PREDATION_RADIUS
        ]
        if not candidates:
            continue
        prey = min(candidates, key=lambda item: item.id)
        eaten.add(prey.id)
        current = living_by_id[predator.id]
        meal = PREDATOR_MEAL * min(1.0, pressure)
        living_by_id[predator.id] = Organism(
            current.id, current.species, current.x, current.y,
            min(1.0, current.energy + meal), current.age, current.generation
        )

    organisms = tuple(
        living_by_id[organism.id] for organism in living
        if organism.id not in eaten and living_by_id[organism.id].energy > 0
    )
    return Model(
        model.schema_version,
        model.seed,
        model.tick + 1,
        copy.deepcopy(model.settings),
        tuple(resources),
        organisms,
        copy.deepcopy(model.random_state),
    )


def update(model: Model, message: Tick | Reset) -> Model:
    """Apply one pure biological message and return a new model."""

    if not isinstance(model, Model):
        raise TypeError("model must be a Model")
    if isinstance(message, Tick):
        return _tick(model, message)
    if isinstance(message, Reset):
        if isinstance(message.seed, bool) or not isinstance(message.seed, int):
            raise ValueError("Reset.seed must be an integer")
        settings = copy.deepcopy(model.settings)
        if message.starting_population is not None:
            settings["species"] = copy.deepcopy(dict(message.starting_population))
        return initial_model(message.seed, settings)
    raise TypeError("message must be Tick or Reset")


def model_to_json(model: Model) -> dict[str, Any]:
    """Return a fresh JSON-compatible payload for ``model``."""

    if not isinstance(model, Model):
        raise TypeError("model must be a Model")
    payload = {
        "schemaVersion": model.schema_version,
        "seed": model.seed,
        "tick": model.tick,
        "settings": copy.deepcopy(model.settings),
        "resources": [resource.__dict__.copy() for resource in model.resources],
        "organisms": [organism.__dict__.copy() for organism in model.organisms],
        "randomState": _json_value(model.random_state),
    }
    return _json_value(payload)


def _object(value: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelValidationError(f"{name} must be an object")
    return value


def model_from_json(payload: Any) -> Model:
    """Validate and decode a persisted model without mutating ``payload``."""

    root = _object(payload, name="model")
    if root.get("schemaVersion") != MODEL_SCHEMA_VERSION:
        raise ModelValidationError("unsupported model schema version")
    seed = root.get("seed")
    tick = _integer(root.get("tick"), name="tick")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ModelValidationError("seed must be an integer")
    settings = _settings(_object(root.get("settings"), name="settings"), normalize=False)

    raw_resources = root.get("resources")
    raw_organisms = root.get("organisms")
    if not isinstance(raw_resources, list) or not isinstance(raw_organisms, list):
        raise ModelValidationError("resources and organisms must be arrays")

    resources: list[Resource] = []
    for raw in raw_resources:
        item = _object(raw, name="resource")
        resource_id = item.get("id")
        kind = item.get("kind")
        if not isinstance(resource_id, str) or not resource_id or not isinstance(kind, str) or not kind:
            raise ModelValidationError("resource identity is invalid")
        resources.append(Resource(resource_id, kind, _number(item.get("x"), name="resource.x", minimum=0, maximum=1), _number(item.get("y"), name="resource.y", minimum=0, maximum=1), _number(item.get("amount"), name="resource.amount", minimum=0, maximum=1)))

    organisms: list[Organism] = []
    for raw in raw_organisms:
        item = _object(raw, name="organism")
        organism_id = item.get("id")
        species = item.get("species")
        if not isinstance(organism_id, str) or not organism_id or species not in SPECIES:
            raise ModelValidationError("organism identity is invalid")
        organisms.append(Organism(organism_id, species, _number(item.get("x"), name="organism.x", minimum=0, maximum=1), _number(item.get("y"), name="organism.y", minimum=0, maximum=1), _number(item.get("energy"), name="organism.energy", minimum=0, maximum=1), _integer(item.get("age", 0), name="organism.age"), _integer(item.get("generation", 0), name="organism.generation")))

    random_state = root.get("randomState")
    if not isinstance(random_state, list):
        raise ModelValidationError("randomState must be an array")
    try:
        state = tuple(_restore_tuple(random_state))
        checker = random.Random()
        checker.setstate(state)
    except (TypeError, ValueError, IndexError):
        raise ModelValidationError("randomState is invalid") from None
    return Model(MODEL_SCHEMA_VERSION, seed, tick, settings, tuple(resources), tuple(organisms), state)


def _restore_tuple(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_restore_tuple(item) for item in value)
    return value


__all__ = [
    "DEFAULT_POPULATION",
    "MODEL_SCHEMA_VERSION",
    "Model",
    "ModelValidationError",
    "Organism",
    "Resource",
    "Reset",
    "Tick",
    "initial_model",
    "model_from_json",
    "model_to_json",
    "update",
]
