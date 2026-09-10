from dataclasses import replace
import unittest

from scripts.ecosystem_model import Advance, Hunt, Organism, Tick, initial_model, model_from_json, model_to_json, update
from scripts.ecosystem_hunts import prepare_hunts, resolve_hunt, hunt_motion


class HuntTests(unittest.TestCase):
    def ready(self, *, energy=.5, cooldown=0):
        base = initial_model(7)
        return replace(base, organisms=(Organism("hunter", "reef_stalker", .5, .5, energy, cooldown=cooldown),
                                        Organism("prey", "neon_tetra", .6, .5, .6)),
                       world_time=replace(base.world_time, hunt_in=0, quiet_remaining=0, food_in=1000))

    def test_only_hungry_available_predator_starts_and_then_prepares(self):
        model = prepare_hunts(self.ready(), .1)
        self.assertEqual(model.hunt.actor, "hunter")
        self.assertEqual(model.statistics.hunts, 1)
        self.assertEqual(hunt_motion(model, model.organisms[0])[2], "prepare")
        for other in (self.ready(energy=.95), self.ready(cooldown=120), replace(self.ready(), organisms=())):
            self.assertFalse(prepare_hunts(other, .1).hunt.actor)
        disabled = self.ready()
        disabled = replace(disabled, settings=dict(disabled.settings, predator_pressure=0))
        self.assertFalse(prepare_hunts(disabled, .1).hunt.actor)

    def test_contact_is_required_and_success_counts_once(self):
        model = self.ready()
        model = replace(model, hunt=Hunt("hunter", "prey", 0, 3),
            world_time=replace(model.world_time, scene="hunt", scene_remaining=3),
            organisms=(replace(model.organisms[0], behavior="pursue"), replace(model.organisms[1], x=.51)))
        result = resolve_hunt(model)
        self.assertEqual(len(result.organisms), 1)
        self.assertEqual(result.statistics.deaths, 1)
        self.assertEqual(result.statistics.hunt_successes, 1)
        self.assertAlmostEqual(result.organisms[0].energy, .75)
        self.assertGreaterEqual(result.organisms[0].cooldown, 120)
        self.assertEqual(resolve_hunt(result), result)
        self.assertEqual(resolve_hunt(replace(model, hunt=replace(model.hunt, preparation=.1))),
                         replace(model, hunt=replace(model.hunt, preparation=.1)))
        far = replace(model, organisms=(model.organisms[0], replace(model.organisms[1], x=.8)))
        self.assertEqual(resolve_hunt(far), far)

    def test_miss_missing_target_and_disabled_hunts_end_with_rest(self):
        active = prepare_hunts(self.ready(), .1)
        variants = (replace(active, hunt=replace(active.hunt, remaining=0)),
                    replace(active, organisms=active.organisms[:1]),
                    replace(active, settings=dict(active.settings, predator_pressure=0)))
        for model in variants:
            result = resolve_hunt(model)
            self.assertFalse(result.hunt.actor)
            self.assertEqual(result.statistics.hunt_successes, 0)
            self.assertEqual(result.organisms[0].behavior, "rest")
            self.assertGreaterEqual(result.organisms[0].cooldown, 120)

    def test_restart_mid_pursuit_preserves_outcome_and_statistics(self):
        model = prepare_hunts(self.ready(), .1)
        self.assertEqual(update(model_from_json(model_to_json(model)), Advance(3)), update(model, Advance(3)))
        biological = update(model, Tick(1))
        self.assertEqual(biological.statistics.hunts, 1)
        self.assertEqual(biological.hunt, model.hunt)

    def test_one_hunter_per_scene_and_no_kill_outside_scene(self):
        model = self.ready()
        model = replace(model, organisms=model.organisms + (replace(model.organisms[0], id="other"),))
        active = prepare_hunts(model, .1)
        self.assertEqual(prepare_hunts(active, .1).statistics.hunts, 1)
        outside = replace(active, hunt=replace(active.hunt, preparation=0),
                          world_time=replace(active.world_time, scene=""))
        self.assertEqual(resolve_hunt(outside).statistics.deaths, 0)

    def test_explicit_population_reset_introduces_selected_species_only(self):
        from scripts.ecosystem_service import EcosystemService
        from tests.test_ecosystem_service import FakeStore
        service = EcosystemService(FakeStore(initial_model(7)))
        response = service.handle_request({"operation": "reset", "seed": 9,
                       "starting_population": {"reef_stalker": 0, "reef_hunter": 2}})
        counts = [f["species"] for f in response["snapshot"]["organisms"]]
        self.assertEqual(counts.count("reef_stalker"), 0)
        self.assertEqual(counts.count("reef_hunter"), 2)

    def test_escape_and_regroup_have_priority_over_ordinary_motion(self):
        model = prepare_hunts(self.ready(), .1)
        model = replace(model, hunt=replace(model.hunt, preparation=0))
        prey = model.organisms[1]
        escape = hunt_motion(model, prey)
        self.assertEqual(escape[2], "flee")
        self.assertGreater(escape[0], 0)
        regroup = replace(model, hunt=Hunt(), organisms=(replace(prey, behavior="flee", cooldown=5),
                                                          replace(prey, id="peer", x=.7)))
        self.assertEqual(hunt_motion(regroup, regroup.organisms[0])[2], "regroup")

    def test_new_species_have_distinct_projection_and_old_population_is_preserved(self):
        from scripts.ecosystem_view import view, Viewport
        model = initial_model(7, {"species": {"reef_hunter": 1}})
        kinds = {fish["species"]: fish["kind"] for fish in view(model, Viewport(100, 30))["organisms"]}
        self.assertEqual(kinds["reef_stalker"], "stalker")
        self.assertEqual(kinds["reef_hunter"], "hunter")
        payload = model_to_json(model)
        payload["schemaVersion"] = 4
        payload["organisms"] = [f for f in payload["organisms"] if not f["species"].startswith("reef_")]
        payload.pop("hunt")
        payload["worldTime"].pop("hunt_in")
        restored = model_from_json(payload)
        self.assertEqual([f.id for f in restored.organisms], [f["id"] for f in payload["organisms"]])
