import copy
import unittest

from scripts.ecosystem_model import Tick, initial_model, update
from scripts.ecosystem_view import Viewport, telemetry, view


class EcosystemViewTests(unittest.TestCase):
    def test_same_model_and_viewport_produce_identical_frames(self) -> None:
        model = initial_model(7)
        viewport = Viewport(800, 480)
        self.assertEqual(view(model, viewport), view(model, viewport))

    def test_projection_is_bounded_and_sorted(self) -> None:
        model = update(initial_model(7), Tick(1))
        frame = view(model, Viewport(80, 24))
        self.assertEqual(frame["organisms"], sorted(frame["organisms"], key=lambda item: item["id"]))
        for item in frame["organisms"] + frame["resources"]:
            self.assertGreaterEqual(item["x"], 0)
            self.assertLessEqual(item["x"], 80)
            self.assertGreaterEqual(item["y"], 0)
            self.assertLessEqual(item["y"], 24)

    def test_view_does_not_change_model(self) -> None:
        model = initial_model(11)
        before = copy.deepcopy(model)
        view(model, Viewport(640, 360))
        self.assertEqual(model, before)

    def test_telemetry_reports_evolution_and_ecology(self) -> None:
        model = initial_model(7)
        payload = telemetry(model)
        self.assertEqual(payload["population"], len(model.organisms))
        self.assertEqual(payload["speciesPresent"], 8)
        self.assertEqual(payload["speciesTotal"], 8)
        self.assertEqual(payload["generation"], 0)
        self.assertEqual(payload["births"], 0)
        self.assertEqual(payload["deaths"], 0)
        self.assertEqual(payload["mutationEvents"], 0)
        self.assertEqual(sum(payload["speciesPopulation"].values()), payload["population"])
        self.assertGreater(payload["resourceAmount"], 0)

    def test_model_tick_changes_only_model_derived_motion(self) -> None:
        model = initial_model(7)
        first = view(model, Viewport(640, 360))
        second = view(update(model, Tick(1)), Viewport(640, 360))
        self.assertNotEqual(first, second)
        self.assertEqual(first["width"], second["width"])
        self.assertEqual(first["height"], second["height"])

    def test_invalid_viewport_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Viewport(0, 20)
        with self.assertRaises(ValueError):
            Viewport(20, -1)
