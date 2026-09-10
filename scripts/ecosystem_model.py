"""Serializable biological state for the autonomous aquarium.

The model deliberately contains simulation state only. Visual and audio
configuration remains owned by ``Config.qml`` and is not accepted here.
"""

from __future__ import annotations

import copy
import math
import random
from dataclasses import dataclass, replace
from collections.abc import Mapping
from typing import Any


MODEL_SCHEMA_VERSION = 3
LEGACY_MODEL_SCHEMA_VERSION = 1
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
RESOURCE_REGENERATION = 0.20
METABOLISM = 0.005
RESOURCE_MEAL = 0.02
PREDATOR_MEAL = 0.10
FEEDING_RADIUS = 0.16
PREDATION_RADIUS = 0.12
MATURITY_AGE = 720  # biological minutes; twelve hours at the default pace
REPRODUCTION_ENERGY = 0.72
REPRODUCTION_COST = 0.28
REPRODUCTION_COOLDOWN = 240  # four biological hours
MUTATION_RATE = 0.08
MUTATION_STEP = 0.12

# Traits remain inside these species-specific ecological niches.  Mutation can
# move a trait within a niche, but cannot turn a herbivore into a predator.
TRAIT_BOUNDS = {
    "neon_tetra": ((0.70, 1.00), (0.05, 0.35)),
    "clownfish": ((0.60, 0.95), (0.10, 0.45)),
    "angelfish": ((0.05, 0.35), (0.55, 1.00)),
    "discus": ((0.55, 0.90), (0.10, 0.40)),
    "butterflyfish": ((0.10, 0.40), (0.45, 0.95)),
    "royal_tang": ((0.75, 1.00), (0.05, 0.30)),
    "betta": ((0.05, 0.30), (0.65, 1.00)),
    "puffer": ((0.10, 0.45), (0.55, 1.00)),
}


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
    diet_preference: float = 0.5
    aggression: float = 0.5
    reproduction_cooldown: int = 0
    vx: float = 0.018
    vy: float = 0.0
    behavior: str = "cruise"
    target: str = ""
    cooldown: float = 0.0


@dataclass(frozen=True)
class WorldTime:
    seconds: float = 0.0
    remainder: float = 0.0
    biology_remainder: float = 0.0
    scene: str = ""
    scene_remaining: float = 0.0
    quiet_remaining: float = 30.0


@dataclass(frozen=True)
class Shelter:
    id: str
    x: float
    y: float


DEFAULT_SHELTERS = (Shelter("reef-left", 0.18, 0.82), Shelter("reef-right", 0.78, 0.82))


@dataclass(frozen=True)
class EvolutionStats:
    biological_minutes: float = 0.0
    births: int = 0
    deaths: int = 0
    mutation_events: int = 0


@dataclass(frozen=True)
class Model:
    schema_version: int
    seed: int
    tick: int
    settings: dict[str, Any]
    resources: tuple[Resource, ...]
    organisms: tuple[Organism, ...]
    random_state: tuple[Any, ...]
    statistics: EvolutionStats = EvolutionStats()
    world_time: WorldTime = WorldTime()
    shelters: tuple[Shelter, ...] = DEFAULT_SHELTERS


@dataclass(frozen=True)
class Advance:
    """Advance active world seconds; one biological minute takes sixty seconds."""

    seconds: float


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
        "mutation_rate": _number(incoming.get("mutation_rate", MUTATION_RATE), name="mutation_rate", minimum=0.0, maximum=1.0),
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
                    diet_preference=round(rng.uniform(*TRAIT_BOUNDS[species][0]), 6),
                    aggression=round(rng.uniform(*TRAIT_BOUNDS[species][1]), 6),
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


def _next_organism_serial(organisms: tuple[Organism, ...]) -> int:
    serials = []
    for organism in organisms:
        if organism.id.startswith("organism-"):
            try:
                serials.append(int(organism.id.removeprefix("organism-")))
            except ValueError:
                pass
    return max(serials, default=0) + 1


def _inherit_traits(
    parent: Organism, mate: Organism, rng: random.Random, mutation_rate: float,
) -> tuple[float, float, bool]:
    bounds = TRAIT_BOUNDS[parent.species]
    mutated = False

    def inherit(value_a: float, value_b: float, trait_bounds: tuple[float, float]) -> float:
        nonlocal mutated
        value = (value_a + value_b) / 2
        if rng.random() < mutation_rate:
            mutated = True
            value += rng.uniform(-MUTATION_STEP, MUTATION_STEP)
        return round(max(trait_bounds[0], min(trait_bounds[1], value)), 6)

    return (
        inherit(parent.diet_preference, mate.diet_preference, bounds[0]),
        inherit(parent.aggression, mate.aggression, bounds[1]),
        mutated,
    )


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
            organism.age + max(1, int(dt)) if dt > 0 else organism.age,
            organism.generation,
            organism.diet_preference,
            organism.aggression,
            max(0, organism.reproduction_cooldown - max(1, int(dt))) if dt > 0 else organism.reproduction_cooldown,
        )
        for organism in sorted(model.organisms, key=lambda item: item.id)
    ]
    before_starvation = len(living)
    living = [organism for organism in living if organism.energy > 0]
    deaths = before_starvation - len(living)

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
        meal = min(RESOURCE_MEAL * organism.diet_preference * max(0.0, dt), resource.amount)
        resources[resource_index] = Resource(
            resource.id, resource.kind, resource.x, resource.y, resource.amount - meal
        )
        updated = living[index]
        living[index] = Organism(
            updated.id, updated.species, updated.x, updated.y,
            min(1.0, updated.energy + meal), updated.age, updated.generation,
            updated.diet_preference, updated.aggression, updated.reproduction_cooldown,
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
            and _distance(predator, prey) <= PREDATION_RADIUS * predator.aggression
        ]
        if not candidates:
            continue
        prey = min(candidates, key=lambda item: item.id)
        eaten.add(prey.id)
        current = living_by_id[predator.id]
        meal = PREDATOR_MEAL * min(1.0, pressure)
        living_by_id[predator.id] = Organism(
            current.id, current.species, current.x, current.y,
            min(1.0, current.energy + meal), current.age, current.generation,
            current.diet_preference, current.aggression, current.reproduction_cooldown,
        )

    organisms = tuple(
        living_by_id[organism.id] for organism in living
        if organism.id not in eaten and living_by_id[organism.id].energy > 0
    )
    deaths += len(eaten)
    rng = random.Random(0)
    rng.setstate(model.random_state)
    next_serial = _next_organism_serial(organisms)
    births: list[Organism] = []
    mutation_events = 0
    counts = {species: sum(item.species == species for item in organisms) for species in SPECIES}
    for parent in organisms:
        if parent.age < MATURITY_AGE or parent.energy < REPRODUCTION_ENERGY:
            continue
        if parent.reproduction_cooldown > 0 or counts[parent.species] >= MAX_POPULATION[parent.species]:
            continue
        mate = next(
            (candidate for candidate in organisms
             if candidate.id != parent.id and candidate.species == parent.species
             and candidate.age >= MATURITY_AGE and candidate.energy >= REPRODUCTION_ENERGY
             and candidate.reproduction_cooldown == 0
             and _distance(parent, candidate) <= FEEDING_RADIUS),
            None,
        )
        if mate is None:
            continue
        parent_index = next(index for index, item in enumerate(organisms) if item.id == parent.id)
        mate_index = next(index for index, item in enumerate(organisms) if item.id == mate.id)
        parent_updated = organisms[parent_index]
        mate_updated = organisms[mate_index]
        # Pair once per tick: both parents pay the cost and receive a cooldown.
        organisms = tuple(
            Organism(item.id, item.species, item.x, item.y,
                     item.energy - REPRODUCTION_COST if item.id in {parent.id, mate.id} else item.energy,
                     item.age, item.generation, item.diet_preference, item.aggression,
                     REPRODUCTION_COOLDOWN if item.id in {parent.id, mate.id} else item.reproduction_cooldown)
            for item in organisms
        )
        diet, aggression, mutated = _inherit_traits(
            parent_updated, mate_updated, rng, model.settings["mutation_rate"]
        )
        mutation_events += int(mutated)
        births.append(Organism(
            id=f"organism-{next_serial:04d}", species=parent.species,
            x=round((parent.x + mate.x) / 2, 6), y=round((parent.y + mate.y) / 2, 6),
            energy=REPRODUCTION_COST, age=0, generation=max(parent.generation, mate.generation) + 1,
            diet_preference=diet, aggression=aggression,
        ))
        next_serial += 1
        counts[parent.species] += 1
    organisms += tuple(births)
    previous_stats = model.statistics
    statistics = EvolutionStats(
        biological_minutes=round(previous_stats.biological_minutes + dt, 6),
        births=previous_stats.births + len(births),
        deaths=previous_stats.deaths + deaths,
        mutation_events=previous_stats.mutation_events + mutation_events,
    )
    # Biological operations preserve movement state for surviving individuals.
    previous = {item.id: item for item in model.organisms}
    organisms = tuple(replace(item, vx=previous[item.id].vx, vy=previous[item.id].vy,
                              behavior=previous[item.id].behavior, target=previous[item.id].target,
                              cooldown=previous[item.id].cooldown)
                      if item.id in previous else item for item in organisms)
    return replace(model, tick=model.tick + 1, settings=copy.deepcopy(model.settings),
                   resources=tuple(resources), organisms=organisms,
                   random_state=rng.getstate(), statistics=statistics)


def update(model: Model, message: Tick | Reset | Advance) -> Model:
    """Apply one pure biological message and return a new model."""

    if not isinstance(model, Model):
        raise TypeError("model must be a Model")
    if isinstance(message, Advance):
        try:
            from scripts.ecosystem_motion import advance
        except ModuleNotFoundError:
            from ecosystem_motion import advance
        return advance(model, _valid_dt(message.seconds))
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
        "statistics": {
            "biologicalMinutes": model.statistics.biological_minutes,
            "births": model.statistics.births,
            "deaths": model.statistics.deaths,
            "mutationEvents": model.statistics.mutation_events,
        },
        "randomState": _json_value(model.random_state),
        "worldTime": model.world_time.__dict__.copy(),
        "shelters": [item.__dict__.copy() for item in model.shelters],
    }
    return _json_value(payload)


def _object(value: Any, *, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelValidationError(f"{name} must be an object")
    return value


def model_from_json(payload: Any) -> Model:
    """Validate and decode a persisted model without mutating ``payload``."""

    root = _object(payload, name="model")
    schema_version = root.get("schemaVersion")
    if isinstance(schema_version, bool) or schema_version not in {1, 2, MODEL_SCHEMA_VERSION}:
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
    if len(raw_resources) > 256 or len(raw_organisms) > sum(MAX_POPULATION.values()):
        raise ModelValidationError("model entity limit exceeded")

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
        diet_preference = _number(item.get("diet_preference", item.get("dietPreference", 0.5)), name="organism.diet_preference", minimum=0, maximum=1)
        aggression = _number(item.get("aggression", 0.5), name="organism.aggression", minimum=0, maximum=1)
        cooldown = _integer(item.get("reproduction_cooldown", item.get("reproductionCooldown", 0)), name="organism.reproduction_cooldown")
        organisms.append(Organism(
            organism_id, species,
            _number(item.get("x"), name="organism.x", minimum=0, maximum=1),
            _number(item.get("y"), name="organism.y", minimum=0, maximum=1),
            _number(item.get("energy"), name="organism.energy", minimum=0, maximum=1),
            _integer(item.get("age", 0), name="organism.age"),
            _integer(item.get("generation", 0), name="organism.generation"),
            diet_preference, aggression, cooldown,
            _number(item.get("vx", 0.018), name="vx", minimum=-1, maximum=1),
            _number(item.get("vy", 0.0), name="vy", minimum=-1, maximum=1),
            _choice(item.get("behavior", "cruise"), ("cruise",), "behavior"),
            _identity(item.get("target", ""), "target", empty=True),
            _number(item.get("cooldown", 0.0), name="cooldown", minimum=0, maximum=3600),
        ))

    ids = [item.id for item in organisms]
    if len(ids) != len(set(ids)) or any(sum(item.species == species for item in organisms) > limit
                                      for species, limit in MAX_POPULATION.items()):
        raise ModelValidationError("duplicate organism ID or species population limit exceeded")
    random_state = root.get("randomState")
    if not isinstance(random_state, list):
        raise ModelValidationError("randomState must be an array")
    try:
        state = tuple(_restore_tuple(random_state))
        checker = random.Random(0)
        checker.setstate(state)
    except (TypeError, ValueError, IndexError):
        raise ModelValidationError("randomState is invalid") from None
    raw_statistics = root.get("statistics", {})
    if not isinstance(raw_statistics, dict):
        raise ModelValidationError("statistics must be an object")
    statistics = EvolutionStats(
        biological_minutes=_number(
            raw_statistics.get("biologicalMinutes", 0.0),
            name="statistics.biologicalMinutes", minimum=0.0, maximum=float("inf"),
        ),
        births=_integer(raw_statistics.get("births", 0), name="statistics.births"),
        deaths=_integer(raw_statistics.get("deaths", 0), name="statistics.deaths"),
        mutation_events=_integer(
            raw_statistics.get("mutationEvents", 0), name="statistics.mutationEvents"
        ),
    )
    raw_time = _object(root.get("worldTime", {}), name="worldTime")
    world_time = WorldTime(**{
        key: (_choice(raw_time.get(key, default), ("", "food", "hunt", "shrimp", "current"), key)
              if key == "scene" else _number(raw_time.get(key, default), name=key,
                  minimum=0, maximum={"remainder": 0.1, "biology_remainder": 60,
                                      "scene_remaining": 3600, "quiet_remaining": 3600}.get(key, float("inf"))))
        for key, default in WorldTime().__dict__.items()
    })
    raw_shelters = root.get("shelters", [item.__dict__ for item in DEFAULT_SHELTERS])
    if not isinstance(raw_shelters, list) or len(raw_shelters) > 16:
        raise ModelValidationError("shelters must be a bounded array")
    shelters = []
    for raw in raw_shelters:
        item = _object(raw, name="shelter")
        shelters.append(Shelter(_identity(item.get("id"), "shelter.id"),
            _number(item.get("x"), name="shelter.x", minimum=0, maximum=1),
            _number(item.get("y"), name="shelter.y", minimum=0, maximum=1)))
    return Model(MODEL_SCHEMA_VERSION, seed, tick, settings, tuple(resources),
                 tuple(organisms), state, statistics, world_time, tuple(shelters))


def _identity(value: Any, name: str, *, empty: bool = False) -> str:
    if not isinstance(value, str) or len(value) > 128 or (not empty and not value):
        raise ModelValidationError(f"invalid {name}")
    return value


def _choice(value: Any, choices: tuple[str, ...], name: str) -> str:
    if not isinstance(value, str) or value not in choices:
        raise ModelValidationError(f"invalid {name}")
    return value


def _restore_tuple(value: Any) -> Any:
    if isinstance(value, list):
        return tuple(_restore_tuple(item) for item in value)
    return value


__all__ = [
    "DEFAULT_POPULATION",
    "EvolutionStats",
    "LEGACY_MODEL_SCHEMA_VERSION",
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
