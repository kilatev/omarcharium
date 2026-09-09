from __future__ import annotations

import copy
import json
import unittest

from scripts.ecosystem_model import (
    MODEL_SCHEMA_VERSION,
    ModelValidationError,
    initial_model,
    model_from_json,
    model_to_json,
)


class EcosystemModelTests(unittest.TestCase):
    def test_initial_state_is_deterministic(self) -> None:
        self.assertEqual(initial_model(7), initial_model(7))
        self.assertNotEqual(initial_model(7), initial_model(8))

    def test_json_round_trip_preserves_future_random_state(self) -> None:
        model = initial_model(17, {"species": {"betta": 2}})
        restored = model_from_json(json.loads(json.dumps(model_to_json(model))))
        self.assertEqual(restored, model)
        self.assertEqual(model_to_json(restored), model_to_json(model))

    def test_serialization_and_parsing_do_not_mutate_inputs(self) -> None:
        settings = {"species": {"puffer": 3}, "food_abundance": 1.2}
        before = copy.deepcopy(settings)
        model = initial_model(3, settings)
        payload = model_to_json(model)
        payload_before = copy.deepcopy(payload)
        model_from_json(payload)
        self.assertEqual(settings, before)
        self.assertEqual(payload, payload_before)

    def test_schema_version_and_malformed_entities_are_rejected(self) -> None:
        payload = model_to_json(initial_model(3))
        payload["schemaVersion"] = MODEL_SCHEMA_VERSION + 1
        with self.assertRaises(ModelValidationError):
            model_from_json(payload)

        payload = model_to_json(initial_model(3))
        payload["organisms"][0]["x"] = 2
        with self.assertRaises(ModelValidationError):
            model_from_json(payload)

        payload = model_to_json(initial_model(3))
        payload["settings"]["species"]["puffer"] = 999
        with self.assertRaises(ModelValidationError):
            model_from_json(payload)

    def test_model_settings_do_not_include_visual_configuration(self) -> None:
        model = initial_model(3, {"palette": "coral", "species": {"puffer": 1}})
        self.assertEqual(set(model.settings), {"species", "food_abundance", "predator_pressure"})


if __name__ == "__main__":
    unittest.main()
