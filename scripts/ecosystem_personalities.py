"""Small deterministic individual behaviors and the bounded shrimp encounter."""
from dataclasses import replace
import math
import random

try:
    from scripts.ecosystem_model import Model, Shrimp, PREDATORS
except ModuleNotFoundError:
    from ecosystem_model import Model, Shrimp, PREDATORS


def distance(a, b):
    return math.hypot(a.x - b.x, a.y - b.y)


def personality(fish):
    if fish.aggression >= .7:
        return "territorial"
    if fish.diet_preference >= .82:
        return "curious"
    return "shy"


def update_shrimp(model: Model, dt: float) -> Model:
    clock = model.world_time
    shrimp = tuple(replace(s, y=max(.78, s.y + (.018 if s.fleeing else -.003) * dt),
                           lifetime=round(s.lifetime - dt, 6)) for s in model.shrimp if s.lifetime > dt)
    model = replace(model, shrimp=shrimp, world_time=replace(clock, shrimp_in=max(0, clock.shrimp_in - dt)))
    if model.shrimp:
        candidate = model.shrimp[0]
        threats = [f for f in model.organisms if f.species in PREDATORS and distance(f, candidate) < .14]
        if threats and not candidate.fleeing:
            model = replace(model, shrimp=(replace(candidate, fleeing=True),))
        hunter = min((f for f in model.organisms if f.species in PREDATORS),
                     key=lambda f: (distance(f, candidate), f.id), default=None)
        if hunter and distance(hunter, candidate) < .02:
            organisms = tuple(replace(f, energy=min(1, f.energy + .08), behavior="rest", cooldown=45)
                              if f.id == hunter.id else f for f in model.organisms)
            return replace(model, organisms=organisms, shrimp=(),
                           statistics=replace(model.statistics, shrimp_catches=model.statistics.shrimp_catches + 1),
                           world_time=replace(model.world_time, scene="", scene_remaining=0, quiet_remaining=30))
        return model
    if model.world_time.shrimp_in > 0 or model.world_time.scene or model.world_time.quiet_remaining > 0 or not model.settings["shrimp_enabled"]:
        return model
    rng = random.Random(0); rng.setstate(model.random_state)
    shrimp = Shrimp(f"shrimp-{int(model.world_time.seconds)}", rng.uniform(.12, .88), .84)
    return replace(model, shrimp=(shrimp,), random_state=rng.getstate(),
                   world_time=replace(model.world_time, shrimp_in=rng.uniform(180, 360), scene="shrimp", scene_remaining=20))


def behavior_motion(model: Model, fish):
    kind = personality(fish)
    if model.shrimp and kind == "curious" and fish.species not in PREDATORS:
        shrimp = model.shrimp[0]
        dx, dy = shrimp.x - fish.x, shrimp.y - fish.y
        length = max(.001, math.hypot(dx, dy))
        return dx / length * .035, dy / length * .025, "explore", shrimp.id
    if kind == "territorial" and fish.species not in PREDATORS:
        peers = [p for p in model.organisms if p.species == fish.species and p.id != fish.id]
        if peers:
            close = min(peers, key=lambda p: (distance(fish, p), p.id))
            if distance(fish, close) < .06:
                dx, dy = fish.x - close.x, fish.y - close.y
                length = max(.001, math.hypot(dx, dy))
                return dx / length * .04, dy / length * .02, "territorial", ""
    return None
