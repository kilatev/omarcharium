import unittest
from dataclasses import replace

from scripts.ecosystem_model import Organism, Shrimp, initial_model, model_from_json, model_to_json
from scripts.ecosystem_personalities import behavior_motion, personality, update_shrimp


class PersonalityTests(unittest.TestCase):
    def test_personality_is_stable_and_uses_bounded_traits(self):
        self.assertEqual(personality(Organism("a", "neon_tetra", .5, .5, .5, aggression=.8)), "territorial")
        self.assertEqual(personality(Organism("b", "neon_tetra", .5, .5, .5, diet_preference=.9, aggression=.2)), "curious")
        self.assertEqual(personality(Organism("c", "neon_tetra", .5, .5, .5, diet_preference=.6, aggression=.2)), "shy")

    def test_territorial_and_curious_behaviors_are_short_nonlethal_overrides(self):
        base = initial_model(7)
        territorial = Organism("a", "clownfish", .5, .5, .5, aggression=.9)
        peer = Organism("b", "clownfish", .52, .5, .5, aggression=.2)
        self.assertEqual(behavior_motion(replace(base, organisms=(territorial, peer)), territorial)[2], "territorial")
        curious = Organism("c", "discus", .5, .5, .5, diet_preference=.9, aggression=.2)
        with_shrimp = replace(base, organisms=(curious,), shrimp=(Shrimp("shrimp", .6, .84),))
        self.assertEqual(behavior_motion(with_shrimp, curious)[2], "explore")

    def test_shrimp_spawns_once_flees_and_catches_without_death(self):
        initial = initial_model(4)
        base = replace(initial, world_time=replace(initial.world_time,
            shrimp_in=0, quiet_remaining=0, food_in=1000, hunt_in=1000),
            organisms=(Organism("pred", "reef_stalker", .1, .84, .5),))
        spawned = update_shrimp(base, .1)
        self.assertEqual(len(spawned.shrimp), 1)
        nearby = replace(spawned.organisms[0], x=max(.02, spawned.shrimp[0].x - .05))
        fleeing = update_shrimp(replace(spawned, organisms=(nearby,)), .1)
        self.assertTrue(fleeing.shrimp[0].fleeing)
        caught = update_shrimp(replace(fleeing, organisms=(replace(fleeing.organisms[0], x=fleeing.shrimp[0].x),)), .1)
        self.assertEqual(caught.shrimp, ())
        self.assertEqual(caught.statistics.shrimp_catches, 1)
        self.assertEqual(caught.statistics.deaths, 0)

    def test_expiration_and_json_replay_are_bounded(self):
        base = initial_model(4)
        model = replace(base, shrimp=(Shrimp("s", .5, .84, lifetime=.05),),
                        world_time=replace(base.world_time, scene="shrimp", scene_remaining=1))
        expired = update_shrimp(model, .1)
        self.assertEqual(expired.shrimp, ())
        self.assertEqual(model_from_json(model_to_json(model)), model)
