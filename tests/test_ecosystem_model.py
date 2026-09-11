from __future__ import annotations

import copy
import json
import unittest

from scripts.ecosystem_model import (
    MODEL_SCHEMA_VERSION,
    MAX_POPULATION,
    REPRODUCTION_COST,
    REPRODUCTION_COOLDOWN,
    MATURITY_AGE,
    Model,
    ModelValidationError,
    Organism,
    Resource,
    Reset,
    Tick,
    TRAIT_BOUNDS,
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
        model = Model(model.schema_version, model.seed, model.tick, dict(model.settings, food_abundance=0.0),
                      (Resource("food", "seaweed", 0.5, 0.5, 1.0),),
                      (Organism("fish", "neon_tetra", 0.5, 0.5, 0.5),), model.random_state)
        next_model = update(model, Tick(1.0))
        self.assertLess(next_model.resources[0].amount, 1.0)
        self.assertGreater(next_model.organisms[0].energy, 0.5 - 0.005)

    def test_biological_tick_never_kills_by_proximity_and_starvation_is_bounded(self) -> None:
        model = self._empty_model(2)
        model = Model(model.schema_version, model.seed, model.tick, model.settings, (), (
            Organism("prey", "neon_tetra", 0.5, 0.5, 0.5),
            Organism("predator", "puffer", 0.5, 0.5, 0.5),
        ), model.random_state)
        next_model = update(model, Tick(1.0))
        self.assertEqual([item.id for item in next_model.organisms], ["predator", "prey"])
        self.assertEqual(next_model.statistics.deaths, 0)
        self.assertEqual(next_model.statistics.biological_minutes, 1.0)
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

    def test_legacy_schema_defaults_statistics_without_losing_state(self) -> None:
        payload = model_to_json(initial_model(17))
        payload["schemaVersion"] = 1
        payload.pop("statistics")
        restored = model_from_json(payload)
        self.assertEqual(restored.schema_version, MODEL_SCHEMA_VERSION)
        self.assertEqual(restored.statistics.biological_minutes, 0.0)
        self.assertEqual(restored.statistics.births, 0)
        self.assertEqual(restored.statistics.deaths, 0)
        self.assertEqual(restored.statistics.mutation_events, 0)

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
        self.assertEqual(set(model.settings), {"species", "food_abundance", "mutation_rate", "predator_pressure", "food_drops", "shrimp_enabled", "currents_enabled", "hunts_enabled"})

    def test_mature_pair_reproduces_with_inherited_bounded_traits(self) -> None:
        model = self._empty_model(4)
        parents = (
            Organism("organism-0001", "neon_tetra", 0.5, 0.5, 0.9, MATURITY_AGE, 2, 0.8, 0.2),
            Organism("organism-0002", "neon_tetra", 0.5, 0.5, 0.9, MATURITY_AGE, 3, 0.9, 0.3),
        )
        model = Model(model.schema_version, model.seed, model.tick, model.settings, (), parents, model.random_state)
        next_model = update(model, Tick(1.0))
        child = next(item for item in next_model.organisms if item.id == "organism-0003")
        self.assertEqual(child.generation, 4)
        self.assertEqual(child.age, 0)
        self.assertEqual(child.energy, REPRODUCTION_COST)
        diet_bounds, aggression_bounds = TRAIT_BOUNDS[child.species]
        self.assertTrue(diet_bounds[0] <= child.diet_preference <= diet_bounds[1])
        self.assertTrue(aggression_bounds[0] <= child.aggression <= aggression_bounds[1])
        self.assertEqual({item.reproduction_cooldown for item in next_model.organisms if item.id in {"organism-0001", "organism-0002"}}, {REPRODUCTION_COOLDOWN})

    def test_reproduction_records_one_mutation_event_per_mutated_offspring(self) -> None:
        model = self._empty_model(14)
        parents = (
            Organism("organism-0001", "neon_tetra", 0.5, 0.5, 0.9, MATURITY_AGE, 0, 0.8, 0.2),
            Organism("organism-0002", "neon_tetra", 0.5, 0.5, 0.9, MATURITY_AGE, 0, 0.9, 0.3),
        )
        model = Model(
            model.schema_version, model.seed, model.tick,
            dict(model.settings, mutation_rate=1.0), (), parents, model.random_state,
        )
        next_model = update(model, Tick(1.0))
        self.assertEqual(next_model.statistics.births, 1)
        self.assertEqual(next_model.statistics.mutation_events, 1)

    def test_reproduction_is_bounded_and_cooldown_prevents_immediate_growth(self) -> None:
        model = self._empty_model(5)
        parents = tuple(
            Organism(f"organism-{index:04d}", "clownfish", 0.5, 0.5, 1.0, MATURITY_AGE, 0, 0.8, 0.2)
            for index in (1, 2)
        )
        model = Model(model.schema_version, model.seed, model.tick, model.settings, (), parents, model.random_state)
        first = update(model, Tick(1.0))
        second = update(first, Tick(1.0))
        self.assertEqual(len(first.organisms), 3)
        self.assertEqual(len(second.organisms), 3)
        self.assertLessEqual(len(second.organisms), 12)

    def test_unpaired_population_can_go_extinct(self) -> None:
        model = self._empty_model(6)
        lone = Organism("organism-0001", "betta", 0.5, 0.5, 0.2, 0, 0, 0.1, 0.8)
        model = Model(model.schema_version, model.seed, model.tick, model.settings, (), (lone,), model.random_state)
        for _ in range(50):
            model = update(model, Tick(1.0))
        self.assertEqual(model.organisms, ())

    def test_two_thousand_biological_minutes_remain_calm_and_observable(self) -> None:
        model = initial_model(7)
        initial_ids = {organism.id for organism in model.organisms}
        for _ in range(2000):
            model = update(model, Tick(1.0))
        self.assertNotEqual(model.organisms, ())
        self.assertTrue(any(organism.generation > 0 for organism in model.organisms))
        self.assertTrue(any(organism.id not in initial_ids for organism in model.organisms))
        self.assertTrue(any(organism.id not in {item.id for item in model.organisms} for organism in initial_model(7).organisms))
        for species in MAX_POPULATION:
            self.assertLessEqual(sum(item.species == species for item in model.organisms), MAX_POPULATION[species])


if __name__ == "__main__":
    unittest.main()
