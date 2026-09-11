import unittest
from dataclasses import replace

from scripts.ecosystem_model import Advance, initial_model, model_from_json, model_to_json, update
from scripts.ecosystem_motion import start_scene


class MotionTests(unittest.TestCase):
    def test_moving_world_reaches_first_reproduction_window(self):
        """The service's movement path must reach arcade reproduction pacing."""

        model = initial_model(7)
        for _ in range(12 * 120):
            model = update(model, Advance(5.0))
        self.assertGreater(model.statistics.births, 0)

    def test_fractional_steps_replay_and_restart(self):
        model = initial_model(7)
        before = model_to_json(model)
        partial = update(model, Advance(0.035))
        restored = model_from_json(model_to_json(partial))
        self.assertEqual(update(restored, Advance(0.065)), update(model, Advance(0.1)))
        self.assertEqual(model_to_json(model), before)
        self.assertEqual(update(model, Advance(0)), model)

    def test_motion_bounds_and_pause_cap(self):
        model = initial_model(7)
        moved = update(model, Advance(100000))
        self.assertEqual(moved, update(model, Advance(5)))
        self.assertNotEqual(moved.organisms[0].x, model.organisms[0].x)
        self.assertTrue(all(0 <= f.x <= 1 and 0 <= f.y <= 1 for f in moved.organisms))
        self.assertEqual(moved.statistics, model.statistics)

    def test_single_scene_then_quiet_without_queue(self):
        model = initial_model(8)
        model = replace(model, world_time=replace(model.world_time, quiet_remaining=0))
        started = start_scene(model, "food", 1)
        self.assertEqual(start_scene(started, "hunt", 1), started)
        ended = update(started, Advance(1))
        self.assertEqual(ended.world_time.scene, "")
        self.assertEqual(ended.world_time.quiet_remaining, 30)
        self.assertEqual(start_scene(ended, "hunt", 1), ended)

    def test_schema_two_migrates_without_losing_biology(self):
        model = initial_model(8)
        payload = model_to_json(model)
        payload["schemaVersion"] = 2
        payload.pop("worldTime")
        payload.pop("shelters")
        for fish in payload["organisms"]:
            for key in ("vx", "vy", "behavior", "target", "cooldown"):
                fish.pop(key)
        self.assertEqual(model_from_json(payload), model)
