"""Pure fixed-step movement and the shared scene clock.

No wall clock or renderer participates here. A delayed message accepts at most
five active seconds; discarded sleep time never queues future scenes.
"""

from dataclasses import replace
import hashlib
import math

try:
    from scripts.ecosystem_model import Model, Tick, update
    from scripts.ecosystem_food import prepare_food, food_target, consume_food
except ModuleNotFoundError:
    from ecosystem_model import Model, Tick, update
    from ecosystem_food import prepare_food, food_target, consume_food

STEP = 0.1
MAX_CATCHUP = 5.0


def phase(identifier: str) -> float:
    return int.from_bytes(hashlib.blake2b(identifier.encode(), digest_size=2).digest(), "big") / 65535


def start_scene(model: Model, kind: str, duration: float) -> Model:
    """Acquire the single scene slot; rejected opportunities are not queued."""
    if kind not in {"food", "hunt", "shrimp", "current"} or not 0 < duration <= 30:
        raise ValueError("invalid scene")
    clock = model.world_time
    if clock.scene or clock.quiet_remaining > 0:
        return model
    return replace(model, world_time=replace(clock, scene=kind, scene_remaining=duration))


def _step(model: Model) -> Model:
    model = prepare_food(model, STEP)
    clock = model.world_time
    seconds = round(clock.seconds + STEP, 6)
    remaining = max(0.0, round(clock.scene_remaining - STEP, 6))
    finished = bool(clock.scene) and remaining == 0
    quiet = 30.0 if finished else max(0.0, round(clock.quiet_remaining - STEP, 6))
    organisms = []
    ordered = sorted(model.organisms, key=lambda item: item.id)
    for fish in ordered:
        heading = 1 if fish.vx >= 0 else -1
        vx = heading * (0.012 + phase(fish.id) * 0.016)
        vy = math.sin(seconds * 0.13 + phase(fish.id) * math.tau) * 0.004
        target = food_target(fish, model.crumbs)
        if target:
            dx, dy = target.x - fish.x, target.y - fish.y
            distance = max(0.001, math.hypot(dx, dy))
            vx, vy = dx / distance * 0.07, dy / distance * 0.07
        # Local separation reads only the previous state, with stable tie breaks.
        for other in ordered:
            if other.id == fish.id:
                continue
            dx, dy = fish.x - other.x, fish.y - other.y
            distance = math.hypot(dx, dy)
            if distance < 0.035:
                if distance < 1e-9:
                    dx, dy, distance = (1 if fish.id < other.id else -1), 0, 1
                force = 0.012 * max(0.1, 1 - distance / 0.035)
                vx += dx / distance * force
                vy += dy / distance * force
        limit = 0.08 if target else 0.03
        vx, vy = max(-0.08, min(0.08, vx)), max(-limit, min(limit, vy))
        x, y = fish.x + vx * STEP, fish.y + vy * STEP
        if x < 0.02 or x > 0.98:
            vx = abs(vx) if x < 0.02 else -abs(vx)
        if y < 0.08 or y > 0.92:
            vy = abs(vy) if y < 0.08 else -abs(vy)
        organisms.append(replace(fish, x=max(0.02, min(0.98, x)),
            y=max(0.08, min(0.92, y)), vx=vx, vy=vy,
            behavior="feed" if target else "cruise", target=target.id if target else "",
            cooldown=max(0.0, round(fish.cooldown - STEP, 6))))
    biology = round(clock.biology_remainder + STEP, 6)
    result = replace(model, organisms=tuple(organisms), world_time=replace(clock,
        seconds=seconds, scene="" if finished else clock.scene,
        scene_remaining=remaining, quiet_remaining=quiet,
        biology_remainder=biology % 60))
    if biology >= 60:
        result = update(result, Tick(1))
    return consume_food(result)


def advance(model: Model, seconds: float) -> Model:
    total = round(model.world_time.remainder + min(seconds, MAX_CATCHUP), 9)
    count = int((total + 1e-9) / STEP)
    result = model
    for _ in range(count):
        result = _step(result)
    return replace(result, world_time=replace(result.world_time,
        remainder=max(0.0, round(total - count * STEP, 9))))
