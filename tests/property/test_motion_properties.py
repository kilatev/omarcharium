import unittest
from dataclasses import replace

from hypothesis import given, settings, strategies as st
from scripts.ecosystem_model import Advance, initial_model, model_from_json, model_to_json, update


class MotionProperties(unittest.TestCase):
    @settings(max_examples=20, deadline=None, print_blob=True)
    @given(st.integers(-10000, 10000), st.integers(1, 10))
    def test_hunts_replay_and_never_double_count_a_kill(self, seed, steps):
        original = initial_model(seed)
        original = replace(original, world_time=replace(original.world_time, hunt_in=0, quiet_remaining=0, food_in=1000))
        before = model_to_json(original)
        left = right = original
        for _ in range(steps):
            left = update(left, Advance(1))
            right = update(model_from_json(model_to_json(right)), Advance(1))
        self.assertEqual(left, right)
        self.assertEqual(model_to_json(original), before)
        self.assertLessEqual(left.statistics.hunt_successes, left.statistics.hunts)
        self.assertEqual(len(original.organisms) - len(left.organisms), left.statistics.hunt_successes)
        self.assertTrue(all(0 <= f.energy <= 1 and f.cooldown >= 0 for f in left.organisms))

    @settings(max_examples=20, deadline=None, print_blob=True)
    @given(st.integers(-10000, 10000), st.integers(1, 50))
    def test_current_motion_stays_bounded_and_replayable(self, seed, steps):
        original = initial_model(seed)
        original = replace(original, world_time=replace(original.world_time, current_in=0,
            quiet_remaining=0, food_in=1000, hunt_in=1000, shrimp_in=1000))
        left = right = original
        for _ in range(steps):
            left = update(left, Advance(.1))
            right = update(model_from_json(model_to_json(right)), Advance(.1))
        self.assertEqual(left, right)
        self.assertTrue(all(0 <= fish.x <= 1 and 0 <= fish.y <= 1 for fish in left.organisms))
        self.assertTrue(0 <= left.world_time.current_strength <= 1)

    @settings(max_examples=20, deadline=None, print_blob=True)
    @given(st.integers(-10000, 10000), st.integers(1, 10))
    def test_food_scene_roundtrip_energy_and_entity_bounds(self, seed, steps):
        original = initial_model(seed)
        original = replace(original, world_time=replace(original.world_time, food_in=0, quiet_remaining=0))
        before = model_to_json(original)
        left = right = original
        for _ in range(steps):
            left = update(left, Advance(1))
            right = update(model_from_json(model_to_json(right)), Advance(1))
        self.assertEqual(left, right)
        self.assertEqual(model_to_json(original), before)
        self.assertLessEqual(len(left.crumbs), 10)
        self.assertTrue(all(0 <= f.energy <= 1 for f in left.organisms))
        self.assertTrue(all(0 <= c.amount <= .1 and 0 <= c.lifetime <= 30 for c in left.crumbs))

    @settings(max_examples=30, deadline=None, print_blob=True)
    @given(st.integers(-10000, 10000), st.lists(st.integers(0, 30), min_size=1, max_size=10))
    def test_partition_restart_and_bounds(self, seed, centiseconds):
        original = initial_model(seed)
        before = model_to_json(original)
        result = original
        for step in centiseconds:
            result = update(model_from_json(model_to_json(result)), Advance(step / 100))
        combined = update(original, Advance(sum(centiseconds) / 100))
        self.assertEqual(result, combined)
        self.assertEqual(model_to_json(original), before)
        for fish in result.organisms:
            self.assertTrue(0 <= fish.x <= 1 and 0 <= fish.y <= 1)
            self.assertTrue(-1 <= fish.vx <= 1 and -1 <= fish.vy <= 1)
