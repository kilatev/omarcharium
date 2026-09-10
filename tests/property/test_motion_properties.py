import unittest

from hypothesis import given, settings, strategies as st
from scripts.ecosystem_model import Advance, initial_model, model_from_json, model_to_json, update


class MotionProperties(unittest.TestCase):
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
