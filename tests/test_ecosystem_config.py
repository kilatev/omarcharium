from __future__ import annotations

import copy
import unittest

from scripts.ecosystem_config import (
    DEFAULT_ECOSYSTEM_CONFIG,
    apply_ecosystem_control,
    model_settings,
    normalise_ecosystem_config,
    reset_config,
)


class EcosystemConfigTests(unittest.TestCase):
    def test_new_species_starting_population_is_bounded_and_malformed_safe(self):
        result = model_settings({"species": {"reef_stalker": 999, "reef_hunter": "bad"}})
        self.assertEqual(result["species"]["reef_stalker"], 3)
        self.assertEqual(result["species"]["reef_hunter"], 0)

    def test_normalization_bounds_controls_and_ignores_malformed_values(self) -> None:
        normalized = normalise_ecosystem_config({
            "enabled": "false", "simulationSpeed": 99, "startingSeed": 2**50,
            "foodAbundance": -1, "mutationRate": 4, "predatorPressure": float("inf"),
            "diagnosticAccelerated": 1,
        })
        self.assertEqual(normalized, {
            "enabled": False, "simulationSpeed": 4.0, "startingSeed": 2**31 - 1,
            "foodAbundance": 0.0, "mutationRate": 1.0, "predatorPressure": 1.0,
            "diagnosticAccelerated": False, "foodDrops": True,
        })

    def test_control_update_preserves_other_controls_and_returns_fresh_data(self) -> None:
        original = {"simulationSpeed": 2.0, "foodAbundance": 0.5}
        updated = apply_ecosystem_control(original, "mutationRate", 0.4)
        self.assertEqual(updated["simulationSpeed"], 2.0)
        self.assertEqual(updated["foodAbundance"], 0.5)
        self.assertEqual(updated["mutationRate"], 0.4)
        self.assertNotEqual(id(updated), id(original))
        with self.assertRaises(KeyError):
            apply_ecosystem_control(original, "species", 2)

    def test_reset_preserves_visual_and_audio_sections(self) -> None:
        config = {
            "art": {"palette": "coral"}, "sound": {"enabled": True},
            "ecosystem": {"startingSeed": 42},
        }
        before = copy.deepcopy(config)
        reset = reset_config(config)
        self.assertEqual(config, before)
        self.assertEqual(reset["art"], config["art"])
        self.assertEqual(reset["sound"], config["sound"])
        self.assertEqual(reset["ecosystem"], DEFAULT_ECOSYSTEM_CONFIG)

    def test_model_settings_uses_only_biological_controls(self) -> None:
        settings = model_settings({"ecosystem": {"foodAbundance": 1.5, "mutationRate": 0.2, "predatorPressure": 0.4, "simulationSpeed": 4}})
        self.assertEqual(settings, {"food_abundance": 1.5, "mutation_rate": 0.2, "predator_pressure": 0.4, "food_drops": True})


if __name__ == "__main__":
    unittest.main()
