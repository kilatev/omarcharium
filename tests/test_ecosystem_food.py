import unittest
from dataclasses import replace

from scripts.ecosystem_model import Advance, Crumb, Organism, initial_model, model_from_json, model_to_json, update
from scripts.ecosystem_food import consume_food
from scripts.ecosystem_config import apply_ecosystem_control, model_settings
from scripts.ecosystem_view import Viewport, view


class FoodTests(unittest.TestCase):
    def ready(self):
        model = initial_model(7)
        return replace(model, world_time=replace(model.world_time, food_in=0, quiet_remaining=0))

    def test_seeded_drop_is_bounded_and_restarts_identically(self):
        original = self.ready()
        before = model_to_json(original)
        model = update(original, Advance(.1))
        self.assertEqual(model.world_time.scene, "food")
        self.assertTrue(4 <= len(model.crumbs) <= 10)
        self.assertTrue(all(0 <= c.y <= .03 for c in model.crumbs))
        self.assertEqual(update(model_from_json(model_to_json(model)), Advance(5)), update(model, Advance(5)))
        self.assertEqual(model_to_json(original), before)
        self.assertEqual(len(view(model, Viewport(80, 24))["crumbs"]), len(model.crumbs))

    def test_hungry_fish_approaches_intercepts_and_returns_to_cruise(self):
        model = replace(initial_model(8), organisms=(Organism("fish", "neon_tetra", .4, .5, .4),),
                        crumbs=(Crumb("crumb", .5, .4),))
        first = update(model, Advance(.1))
        self.assertEqual(first.organisms[0].behavior, "feed")
        self.assertGreater(first.organisms[0].x, .4)
        for _ in range(5):
            first = update(first, Advance(1))
        self.assertEqual(first.crumbs, ())
        self.assertAlmostEqual(first.organisms[0].energy, .435)
        self.assertEqual(first.organisms[0].behavior, "cruise")
        self.assertEqual(first.organisms[0].target, "")

    def test_competing_consumers_transfer_finite_energy_once(self):
        model = replace(initial_model(8), organisms=tuple(Organism(i, "neon_tetra", .5, .5, .4,
                         behavior="feed", target="crumb") for i in ("b", "a")), crumbs=(Crumb("crumb", .5, .5),))
        result = consume_food(model)
        self.assertAlmostEqual(sum(f.energy for f in result.organisms), .835)
        self.assertEqual(result.organisms[0].id, "a")
        self.assertEqual(result.crumbs, ())
        self.assertTrue(all(f.target == "" for f in result.organisms))

    def test_disabled_or_busy_opportunity_is_discarded_and_existing_food_expires(self):
        ready = self.ready()
        for model in (replace(ready, settings=dict(ready.settings, food_drops=False)),
                      replace(ready, world_time=replace(ready.world_time, scene="hunt", scene_remaining=1))):
            result = update(model, Advance(.1))
            self.assertEqual(result.crumbs, ())
            self.assertGreaterEqual(result.world_time.food_in, 60)
        model = replace(ready, organisms=(), crumbs=(Crumb("crumb", .4, .4, lifetime=.2),),
                        settings=dict(ready.settings, food_drops=False))
        result = update(model, Advance(.1))
        self.assertGreater(result.crumbs[0].y, .4)
        result = update(result, Advance(.1))
        self.assertEqual(result.crumbs, ())
        self.assertEqual(result.resources, model.resources)

    def test_legacy_save_and_control_toggle(self):
        model = initial_model(9)
        payload = model_to_json(model)
        payload["schemaVersion"] = 3
        payload.pop("crumbs")
        payload["worldTime"].pop("food_in")
        payload["settings"].pop("food_drops")
        self.assertEqual(model_from_json(payload), model)
        config = apply_ecosystem_control({}, "foodDrops", False)
        self.assertFalse(model_settings(config)["food_drops"])
