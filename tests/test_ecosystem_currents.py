import unittest
from dataclasses import replace

from scripts.ecosystem_model import Advance, initial_model, model_from_json, model_to_json, update
from scripts.ecosystem_personalities import update_current


class CurrentTests(unittest.TestCase):
    def test_current_pulse_is_seeded_smooth_bounded_and_single_scene(self):
        base = initial_model(11)
        base = replace(base, world_time=replace(base.world_time, current_in=0, quiet_remaining=0,
                        food_in=1000, hunt_in=1000, shrimp_in=1000))
        started = update_current(base, .1)
        self.assertEqual(started.world_time.scene, "current")
        self.assertEqual(started.world_time.current_direction, -1)
        self.assertGreaterEqual(started.world_time.current_strength, .18)
        blocked = update_current(replace(started, world_time=replace(started.world_time, scene="hunt")), .1)
        self.assertEqual(blocked.world_time.current_strength, 0)
        self.assertLess(blocked.world_time.current_in, started.world_time.current_in)
        ended = started
        for _ in range(200):
            ended = update(ended, Advance(.1))
        self.assertEqual(ended.world_time.scene, "")
        self.assertEqual(ended.world_time.quiet_remaining, 30)
        self.assertEqual(ended.world_time.current_strength, 0)

    def test_disabled_current_does_not_accumulate_opportunities(self):
        base = initial_model(1)
        base = replace(base, settings=dict(base.settings, currents_enabled=False),
                       world_time=replace(base.world_time, current_in=0, quiet_remaining=0))
        result = update_current(base, .1)
        self.assertEqual(result.world_time.scene, "")
        self.assertEqual(result.world_time.current_strength, 0)
        self.assertGreater(result.world_time.current_in, 0)

    def test_current_state_round_trips_and_motion_replays(self):
        base = initial_model(3)
        base = replace(base, world_time=replace(base.world_time, current_in=0, quiet_remaining=0,
                        food_in=1000, hunt_in=1000, shrimp_in=1000))
        current = update(base, Advance(.1))
        restored = model_from_json(model_to_json(current))
        self.assertEqual(update(restored, Advance(2)), update(current, Advance(2)))
