"""Rare predation scenes and their surrounding shoal response, without I/O."""
from dataclasses import replace
import math
import random

try:
    from scripts.ecosystem_model import Hunt, Model, Organism, PREDATORS
except ModuleNotFoundError:
    from ecosystem_model import Hunt, Model, Organism, PREDATORS


def distance(left, right):
    return math.hypot(left.x - right.x, left.y - right.y)


def toward(fish, x, y, speed):
    dx, dy = x - fish.x, y - fish.y
    length = max(0.001, math.hypot(dx, dy))
    return dx / length * speed, dy / length * speed


def finish_hunt(model: Model, *, success: bool = False) -> Model:
    hunt = model.hunt
    rng = random.Random(0)
    rng.setstate(model.random_state)
    actor = next((f for f in model.organisms if f.id == hunt.actor), None)
    cooldown = rng.uniform(180, 300) if actor and actor.species == "reef_hunter" else rng.uniform(120, 240)
    prey = next((f for f in model.organisms if f.id == hunt.target), None)
    meal = min(0.25, prey.energy * 0.6) if success and prey else 0
    fish = tuple(replace(f, energy=min(1, f.energy + meal), behavior="rest", target="", cooldown=cooldown)
                 if f.id == hunt.actor else f for f in model.organisms if not (success and f.id == hunt.target))
    clock = model.world_time
    if clock.scene == "hunt":
        clock = replace(clock, scene="", scene_remaining=0, quiet_remaining=30)
    stats = replace(model.statistics, deaths=model.statistics.deaths + int(success),
                    hunt_successes=model.statistics.hunt_successes + int(success))
    return replace(model, organisms=fish, world_time=clock, hunt=Hunt(), statistics=stats, random_state=rng.getstate())


def prepare_hunts(model: Model, dt: float) -> Model:
    hunt = model.hunt
    if hunt.actor:
        by_id = {f.id: f for f in model.organisms}
        actor, prey = by_id.get(hunt.actor), by_id.get(hunt.target)
        if (model.settings["predator_pressure"] <= 0 or actor is None or prey is None
                or actor.species not in PREDATORS or prey.species in PREDATORS
                or model.world_time.scene != "hunt"):
            return finish_hunt(model)
        return replace(model, hunt=replace(hunt, preparation=max(0, round(hunt.preparation - dt, 6)),
                                           remaining=max(0, round(hunt.remaining - dt, 6))))
    clock = replace(model.world_time, hunt_in=max(0, round(model.world_time.hunt_in - dt, 6)))
    model = replace(model, world_time=clock)
    if clock.hunt_in > 0:
        return model
    rng = random.Random(0)
    rng.setstate(model.random_state)
    clock = replace(clock, hunt_in=round(rng.uniform(45, 90) / max(.25, model.settings["predator_pressure"]), 6))
    model = replace(model, world_time=clock, random_state=rng.getstate())
    if clock.scene or clock.quiet_remaining > 0 or model.settings["predator_pressure"] <= 0 or not model.settings["hunts_enabled"]:
        return model
    candidates = []
    for predator in model.organisms:
        if predator.species not in PREDATORS or predator.energy >= .85 or predator.cooldown > 0:
            continue
        radius = .18 if predator.species == "reef_stalker" else .3
        prey = min((p for p in model.organisms if p.species not in PREDATORS and distance(predator, p) <= radius),
                   key=lambda p: (distance(predator, p), p.id), default=None)
        if prey:
            candidates.append((predator, prey))
    if not candidates:
        return model
    predator, prey = rng.choice(sorted(candidates, key=lambda pair: pair[0].id))
    duration = rng.uniform(2, 5) if predator.species == "reef_stalker" else rng.uniform(3, 8)
    return replace(model, hunt=Hunt(predator.id, prey.id, .7, duration + .7),
                   world_time=replace(clock, scene="hunt", scene_remaining=duration + .7),
                   statistics=replace(model.statistics, hunts=model.statistics.hunts + 1), random_state=rng.getstate())


def hunt_motion(model: Model, fish: Organism):
    """Override ordinary feeding/cruising for hunters and threatened shoals."""
    hunt = model.hunt
    if fish.id == hunt.actor:
        if hunt.preparation > 0:
            return 0.0, 0.0, "prepare", hunt.target
        prey = next((f for f in model.organisms if f.id == hunt.target), None)
        if prey:
            vx, vy = toward(fish, prey.x, prey.y, .13 if fish.species == "reef_stalker" else .11)
            return vx, vy, "pursue", prey.id
    if fish.species in PREDATORS:
        if fish.cooldown > 0:
            return fish.vx * .5, fish.vy * .5, "rest", ""
        if fish.species == "reef_stalker" and model.shelters:
            shelter = min(model.shelters, key=lambda s: distance(fish, s))
            vx, vy = toward(fish, shelter.x, shelter.y, .008 if distance(fish, shelter) > .03 else 0)
            return vx, vy, "ambush", ""
        return (.009 if fish.vx >= 0 else -.009), 0.001 * math.sin(model.world_time.seconds * .1), "patrol", ""
    nearby = [p for p in model.organisms if p.species in PREDATORS and distance(fish, p) < .2]
    threat = min(nearby, key=lambda p: (distance(fish, p), p.id), default=None)
    if threat and ((threat.id == hunt.actor and hunt.preparation == 0) or distance(fish, threat) < .07):
        speed = .095 + fish.aggression * .06 if threat.id == hunt.actor else .035
        vx, vy = toward(fish, fish.x * 2 - threat.x, fish.y * 2 - threat.y, speed)
        if vx == 0 and vy == 0:
            vx = speed
        return vx, vy, "flee", ""
    if fish.behavior in {"flee", "regroup"} and fish.cooldown > 0:
        peers = [p for p in model.organisms if p.species == fish.species and p.id != fish.id]
        if peers:
            vx, vy = toward(fish, sum(p.x for p in peers) / len(peers), sum(p.y for p in peers) / len(peers), .025)
            return vx, vy, "regroup", ""
    return None


def resolve_hunt(model: Model) -> Model:
    hunt = model.hunt
    if not hunt.actor:
        return model
    actor = next((f for f in model.organisms if f.id == hunt.actor), None)
    prey = next((f for f in model.organisms if f.id == hunt.target), None)
    if (actor is None or prey is None or model.settings["predator_pressure"] <= 0
            or hunt.remaining <= 0 or model.world_time.scene != "hunt"):
        return finish_hunt(model)
    if hunt.preparation == 0 and actor.species in PREDATORS and actor.behavior == "pursue" and prey.species not in PREDATORS and distance(actor, prey) <= .015:
        return finish_hunt(model, success=True)
    return model
