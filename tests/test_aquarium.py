from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("omarcharium_aquarium", ROOT / "scripts" / "aquarium.py")
assert SPEC and SPEC.loader
AQUARIUM = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = AQUARIUM
SPEC.loader.exec_module(AQUARIUM)


class ConfigurationTests(unittest.TestCase):
    def test_normalisation_clamps_public_configuration_contract(self) -> None:
        config = AQUARIUM.normalise_config({
            "species": {"neon_tetra": 999, "puffer": -4, "unknown": 12},
            "art": {"palette": "not-a-palette", "bubbleDensity": 155, "current": 0, "showTelemetry": 0},
            "sound": {"enabled": 1, "volume": "41"},
            "integration": {"idleEnabled": False},
        })

        self.assertEqual(config["species"]["neon_tetra"], 20)
        self.assertEqual(config["species"]["puffer"], 0)
        self.assertNotIn("unknown", config["species"])
        self.assertEqual(config["art"]["palette"], "lagoon")
        self.assertEqual(config["art"]["bubbleDensity"], 100)
        self.assertEqual(config["art"]["current"], 0.35)
        self.assertFalse(config["art"]["showTelemetry"])
        self.assertTrue(config["sound"]["enabled"])
        self.assertEqual(config["sound"]["volume"], 41)
        self.assertFalse(config["integration"]["idleEnabled"])

    def test_invalid_file_uses_complete_packaged_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text("{ definitely not json", encoding="utf-8")
            config = AQUARIUM.load_config(path)

        defaults = json.loads((ROOT / "defaults.json").read_text(encoding="utf-8"))
        self.assertEqual(config, defaults)


class RendererTests(unittest.TestCase):
    def test_mirroring_is_an_involution_for_every_fish_frame(self) -> None:
        for species, frames in AQUARIUM.SPRITES.items():
            for frame in frames:
                with self.subTest(species=species, frame=frame):
                    self.assertEqual(AQUARIUM.mirror_sprite(AQUARIUM.mirror_sprite(frame)), frame)

    def test_scene_population_and_snapshot_dimensions_match_configuration(self) -> None:
        config = AQUARIUM.normalise_config({
            "species": {key: 0 for key in AQUARIUM.SPRITES},
            "art": {"showTelemetry": False},
        })
        config["species"]["angelfish"] = 2
        config["species"]["puffer"] = 3
        scene = AQUARIUM.OceanScene(80, 24, config, seed=17)
        scene.update(1 / 24)
        snapshot = scene.render().plain().split("\n")

        self.assertEqual(len(scene.fish), 5)
        self.assertEqual(len(snapshot), 24)
        self.assertTrue(all(len(line) <= 80 for line in snapshot))
        self.assertIn("Y", "\n".join(snapshot))


class AudioTests(unittest.TestCase):
    def test_pipewire_stream_is_explicitly_raw_pcm(self) -> None:
        command = AQUARIUM.AmbientAudio.playback_command()
        self.assertIn("--raw", command)
        self.assertEqual(command[-1], "-")
        self.assertEqual(command[command.index("--format") + 1], "s16")

    def test_audio_test_defaults_to_eight_seconds_without_a_tty(self) -> None:
        arguments = AQUARIUM.parse_args(["--audio-test"])
        self.assertEqual(arguments.audio_test, 8.0)


class IdleIntegrationTests(unittest.TestCase):
    def run_helper(self, state_home: Path, action: str) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["XDG_STATE_HOME"] = str(state_home)
        return subprocess.run(
            ["bash", str(ROOT / "scripts" / "idle-integration"), action],
            check=True,
            text=True,
            capture_output=True,
            env=environment,
        )

    def test_owned_stock_toggle_is_released(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            self.run_helper(state, "enable")
            toggle = state / "omarchy" / "toggles" / "screensaver-off"
            owner = state / "omarcharium" / "owns-screensaver-off"
            self.assertTrue(toggle.exists())
            self.assertTrue(owner.exists())

            self.run_helper(state, "disable")
            self.assertFalse(toggle.exists())
            self.assertFalse(owner.exists())

    def test_preexisting_user_toggle_is_never_removed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            toggle = state / "omarchy" / "toggles" / "screensaver-off"
            toggle.parent.mkdir(parents=True)
            toggle.touch()

            self.run_helper(state, "enable")
            self.run_helper(state, "disable")
            self.assertTrue(toggle.exists())
            self.assertFalse((state / "omarcharium" / "owns-screensaver-off").exists())


if __name__ == "__main__":
    unittest.main()
