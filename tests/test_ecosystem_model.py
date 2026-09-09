from __future__ import annotations

import copy
import json
import unittest

from scripts.ecosystem_model import (
    MODEL_SCHEMA_VERSION,
    Model,
    ModelValidationError,
    Organism,
    Resource,
    Reset,
    Tick,
    initial_model,
    model_from_json,
    model_to_json,
    update,
)


class EcosystemModelTests(unittest.TestCase):
    @staticmethod
    def _empty_model(seed: int) -> Model:
        model = initial_model(seed, {"species": {
            species: 0 for species in (
                "neon_tetra", "clownfish", "angelfish", "discus",
                "butterflyfish", "royal_tang", "betta", "puffer",
            )
        }})
        return model

    def test_tick_consumes_resource_and_metabolizes_fish(self) -> None:
        model = self._empty_model(1)
        model = Model(model.schema_version, model.seed, model.tick, model.settings,
                      (Resource("food", "seaweed", 0.5, 0.5, 0.5),),
                      (Organism("fish", "neon_tetra", 0.5, 0.5, 0.5),), model.random_state)
        next_model = update(model, Tick(1.0))
        self.assertLess(next_model.resources[0].amount, 0.5)
        self.assertGreater(next_model.organisms[0].energy, 0.5 - 0.035)

    def test_tick_predation_and_starvation_are_bounded(self) -> None:
        model = self._empty_model(2)
        model = Model(model.schema_version, model.seed, model.tick, model.settings, (), (
            Organism("prey", "neon_tetra", 0.5, 0.5, 0.5),
            Organism("predator", "puffer", 0.5, 0.5, 0.5),
        ), model.random_state)
        next_model = update(model, Tick(1.0))
        self.assertEqual([item.id for item in next_model.organisms], ["predator"])
        self.assertLessEqual(next_model.organisms[0].energy, 1.0)
        starving = Model(
            model.schema_version, model.seed, model.tick, model.settings, (),
            (Organism("fish", "neon_tetra", 0.5, 0.5, 0.001),),
            model.random_state,
        )
        self.assertEqual(update(starving, Tick(1.0)).organisms, ())

    def test_tick_is_deterministic_and_does_not_mutate_input(self) -> None:
        model = initial_model(9)
        before = model_to_json(model)
        self.assertEqual(update(model, Tick(1.5)), update(model, Tick(1.5)))
        self.assertEqual(model_to_json(model), before)

    def test_reset_preserves_simulation_settings_and_uses_population(self) -> None:
        model = initial_model(9, {"food_abundance": 1.5, "predator_pressure": 0.25})
        reset = update(model, Reset(42, {"betta": 2}))
        self.assertEqual(reset.seed, 42)
        self.assertEqual(reset.settings["food_abundance"], 1.5)
        self.assertEqual(reset.settings["predator_pressure"], 0.25)
        self.assertEqual(sum(item.species == "betta" for item in reset.organisms), 2)

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
