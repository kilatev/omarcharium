import importlib.util
import unittest
from pathlib import Path

from scripts.ecosystem_model import initial_model, model_to_json


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("omarcharium_lock_bridge", ROOT / "integrations/omarcharium-lock/bridge.py")
assert SPEC and SPEC.loader
BRIDGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BRIDGE)


class LockBridgeTests(unittest.TestCase):
    def test_frame_comes_from_service_snapshot(self) -> None:
        model = initial_model(7)
        frame = BRIDGE.render_snapshot([80, 24], lambda: {"snapshot": model_to_json(model)})
        self.assertEqual(frame["width"], 80)
        self.assertEqual(frame["height"], 24)
        self.assertEqual(frame["tick"], model.tick)
        self.assertEqual(frame["telemetry"]["population"], len(model.organisms))

    def test_service_failure_returns_empty_safe_frame(self) -> None:
        frame = BRIDGE.fallback_frame([80, 24], "service unavailable")
        self.assertEqual(frame["organisms"], [])
        self.assertEqual(frame["resources"], [])
        self.assertIn("service unavailable", frame["error"])

    def test_invalid_dimensions_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            BRIDGE.render_snapshot([True, 24], lambda: {})


if __name__ == "__main__":
    unittest.main()
