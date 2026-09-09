from __future__ import annotations

import copy
import json
import unittest

from scripts.ecosystem_model import Tick, initial_model, model_from_json, model_to_json, update

try:
    from hypothesis import given, strategies as st
except ImportError:  # Keep the base test command usable without dev extras.
    given = None
    st = None


if given is None or st is None:

    class EcosystemPropertyTests(unittest.TestCase):
        @unittest.skip("install requirements-dev.txt to run Hypothesis properties")
        def test_model_properties(self) -> None:
            self.fail("Hypothesis is unavailable")

else:

    class EcosystemPropertyTests(unittest.TestCase):
        @given(st.integers())
        def test_valid_models_round_trip_and_are_deterministic(self, seed: int) -> None:
            model = initial_model(seed)
            payload = model_to_json(model)
            self.assertEqual(model_from_json(json.loads(json.dumps(payload))), model)
            self.assertEqual(model, initial_model(seed))

        @given(st.integers())
        def test_malformed_payloads_are_rejected_without_mutation(self, seed: int) -> None:
            payload = model_to_json(initial_model(seed))
            payload["schemaVersion"] = 999
            before = copy.deepcopy(payload)
            with self.assertRaises(ValueError):
                model_from_json(payload)
            self.assertEqual(payload, before)

        @given(st.integers())
        def test_json_contract_contains_no_python_only_values(self, seed: int) -> None:
            self.assertIsInstance(json.dumps(model_to_json(initial_model(seed))), str)

        @given(st.integers(), st.lists(st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False), max_size=8))
        def test_tick_replay_is_deterministic_and_bounded(self, seed: int, timesteps: list[float]) -> None:
            model = initial_model(seed)
            replay = initial_model(seed)
            for dt in timesteps:
                model = update(model, Tick(dt))
                replay = update(replay, Tick(dt))
            self.assertEqual(model, replay)
            self.assertTrue(all(0 <= resource.amount <= 1 for resource in model.resources))
            self.assertTrue(all(0 <= organism.energy <= 1 for organism in model.organisms))

        @given(st.integers(), st.lists(st.floats(min_value=0, max_value=10, allow_nan=False, allow_infinity=False), max_size=8))
        def test_tick_does_not_mutate_input(self, seed: int, timesteps: list[float]) -> None:
            model = initial_model(seed)
            before = model_to_json(model)
            for dt in timesteps:
                update(model, Tick(dt))
            self.assertEqual(model_to_json(model), before)


if __name__ == "__main__":
    unittest.main()
