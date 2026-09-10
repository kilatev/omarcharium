"""Finite autonomous food portions and pure feeding decisions."""
from dataclasses import replace
import math
import random

try:
    from scripts.ecosystem_model import Crumb, HERBIVORES, Model, Organism
except ModuleNotFoundError:
    from ecosystem_model import Crumb, HERBIVORES, Model, Organism


def prepare_food(model: Model, dt: float) -> Model:
    clock = model.world_time
    timer = max(0.0, round(clock.food_in - dt, 6))
    crumbs = tuple(replace(c, y=c.y + 0.022 * dt, lifetime=round(c.lifetime - dt, 6))
                   for c in model.crumbs if c.lifetime > dt and c.y + 0.022 * dt <= 1 and c.amount > 0)
    model = replace(model, crumbs=crumbs, world_time=replace(clock, food_in=timer))
    if timer > 0:
        return model
    rng = random.Random(0)
    rng.setstate(model.random_state)
    # Missed opportunities are discarded even while disabled or another scene runs.
    clock = replace(model.world_time, food_in=round(rng.uniform(60, 180), 6))
    if model.settings["food_drops"] and not clock.scene and clock.quiet_remaining == 0 and not crumbs:
        centre = rng.uniform(0.15, 0.85)
        crumbs = tuple(Crumb(f"crumb-{clock.seconds:.1f}-{i}",
                            max(0.02, min(0.98, centre + rng.uniform(-0.08, 0.08))),
                            rng.uniform(0, 0.03)) for i in range(rng.randint(4, 10)))
        clock = replace(clock, scene="food", scene_remaining=30)
    return replace(model, crumbs=crumbs, world_time=clock, random_state=rng.getstate())


def food_target(fish: Organism, crumbs: tuple[Crumb, ...]) -> Crumb | None:
    if fish.species not in HERBIVORES or fish.energy >= 0.9:
        return None
    reachable = [c for c in crumbs if math.hypot(c.x - fish.x, c.y - fish.y) < c.lifetime * 0.05]
    return min(reachable, key=lambda c: (math.hypot(c.x - fish.x, c.y - fish.y), c.id), default=None)


def consume_food(model: Model) -> Model:
    available = {c.id: c for c in model.crumbs}
    fish = []
    for organism in sorted(model.organisms, key=lambda f: f.id):
        crumb = available.get(organism.target)
        if organism.behavior == "feed" and crumb and math.hypot(crumb.x - organism.x, crumb.y - organism.y) <= 0.025:
            meal = min(crumb.amount, 1 - organism.energy)
            organism = replace(organism, energy=organism.energy + meal, behavior="cruise", target="")
            if crumb.amount - meal > 1e-9:
                available[crumb.id] = replace(crumb, amount=crumb.amount - meal)
            else:
                del available[crumb.id]
        fish.append(organism)
    fish = tuple(replace(f, behavior="cruise", target="") if f.behavior == "feed" and f.target not in available else f for f in fish)
    return replace(model, organisms=fish, crumbs=tuple(available.values()))
