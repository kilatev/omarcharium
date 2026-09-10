import importlib.util
import unittest
import io
import json
from unittest.mock import patch
from pathlib import Path

from scripts.ecosystem_model import Advance, initial_model, model_to_json, update
from scripts.aquarium import OceanScene, normalise_config


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("omarcharium_lock_bridge", ROOT / "integrations/omarcharium-lock/bridge.py")
assert SPEC and SPEC.loader
BRIDGE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BRIDGE)


class LockBridgeTests(unittest.TestCase):
    def test_terminal_and_lock_share_motion_and_hold_stale_state(self):
        model = update(initial_model(7), Advance(1))
        before = model_to_json(model)
        terminal = OceanScene(80, 24, normalise_config({}), 7)
        terminal.shared_world = True
        terminal.shared_model = model
        frame = BRIDGE.render_snapshot([80, 24], lambda: {"snapshot": before})
        terminal.update(0.1)
        terminal.render()
        self.assertEqual(terminal.shared_frame()["organisms"], frame["organisms"])
        self.assertEqual(terminal.shared_frame()["shelters"], frame["shelters"])
        self.assertEqual(model_to_json(model), before)
        output = io.StringIO()
        with patch.object(BRIDGE.sys, "stdin", io.StringIO('[80,24]\n[80,24]\n')), patch.object(BRIDGE.sys, "stdout", output), patch.object(BRIDGE, "request", side_effect=[{"snapshot": before}, OSError("offline")]):
            BRIDGE.main()
        first, stale = map(json.loads, output.getvalue().splitlines())
        self.assertEqual(stale["organisms"], first["organisms"])
        self.assertEqual(stale["error"], "offline")

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
