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
            "backdrop": {"source": "unknown", "effectsEnabled": "yes", "effectIntensity": 400},
            "sound": {"enabled": 1, "volume": "41"},
            "integration": {"idleEnabled": False, "exitOnPointerMotion": False},
        })

        self.assertEqual(config["species"]["neon_tetra"], 20)
        self.assertEqual(config["species"]["puffer"], 0)
        self.assertNotIn("unknown", config["species"])
        self.assertEqual(config["art"]["palette"], "lagoon")
        self.assertEqual(config["art"]["bubbleDensity"], 100)
        self.assertEqual(config["art"]["current"], 0.35)
        self.assertFalse(config["art"]["showTelemetry"])
        self.assertEqual(config["backdrop"]["source"], "plain")
        self.assertFalse(config["backdrop"]["effectsEnabled"])
        self.assertEqual(config["backdrop"]["effectIntensity"], 100)
        self.assertTrue(config["sound"]["enabled"])
        self.assertEqual(config["sound"]["volume"], 41)
        self.assertFalse(config["integration"]["idleEnabled"])
        self.assertFalse(config["integration"]["exitOnPointerMotion"])

    def test_malformed_pointer_motion_setting_uses_safe_default(self) -> None:
        config = AQUARIUM.normalise_config({"integration": {"exitOnPointerMotion": "false"}})
        self.assertTrue(config["integration"]["exitOnPointerMotion"])

    def test_invalid_file_uses_complete_packaged_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text("{ definitely not json", encoding="utf-8")
            config = AQUARIUM.load_config(path)

        defaults = json.loads((ROOT / "defaults.json").read_text(encoding="utf-8"))
        self.assertEqual(config, defaults)

    def test_image_backdrop_settings_are_normalized(self) -> None:
        config = AQUARIUM.normalise_config({
            "backdrop": {
                "source": "image",
                "imagePath": "/tmp/reef image.png",
                "fitMode": "invalid",
                "dimming": -20,
            },
        })
        self.assertEqual(config["backdrop"]["source"], "image")
        self.assertEqual(config["backdrop"]["imagePath"], "/tmp/reef image.png")
        self.assertEqual(config["backdrop"]["fitMode"], "cover")
        self.assertEqual(config["backdrop"]["dimming"], 0)

    def test_ascii_backdrop_settings_are_normalized(self) -> None:
        config = AQUARIUM.normalise_config({
            "backdrop": {
                "source": "ascii",
                "ascii": {
                    "detail": 999,
                    "glyphMode": "letters",
                    "colorMode": "indexed",
                    "dither": "yes",
                },
            },
        })
        self.assertEqual(config["backdrop"]["source"], "ascii")
        self.assertEqual(config["backdrop"]["ascii"], {
            "detail": 100,
            "glyphMode": "ramp",
            "colorMode": "truecolor",
            "dither": True,
        })


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

    def test_pelagic_backdrop_and_effect_overlay_are_independent_and_deterministic(self) -> None:
        base = {
            "species": {key: 0 for key in AQUARIUM.SPRITES},
            "art": {"showTelemetry": False},
            "backdrop": {"source": "pelagic", "effectsEnabled": False},
        }
        without_effects = AQUARIUM.OceanScene(80, 24, AQUARIUM.normalise_config(base), seed=23)
        first = without_effects.render().plain()
        repeated = AQUARIUM.OceanScene(80, 24, AQUARIUM.normalise_config(base), seed=23).render().plain()

        base["backdrop"]["effectsEnabled"] = True
        with_effects = AQUARIUM.OceanScene(80, 24, AQUARIUM.normalise_config(base), seed=23)
        effected = with_effects.render().plain()

        self.assertEqual(first, repeated)
        self.assertNotEqual(first, effected)
        self.assertIn("·", first)
        self.assertIn("~", effected)

    def test_pelagic_backdrop_renders_in_every_palette(self) -> None:
        for palette in AQUARIUM.PALETTES:
            config = AQUARIUM.normalise_config({
                "art": {"palette": palette, "showTelemetry": False},
                "backdrop": {"source": "pelagic", "effectsEnabled": True},
            })
            scene = AQUARIUM.OceanScene(80, 24, config, seed=5)
            with self.subTest(palette=palette):
                self.assertIn("·", scene.render().plain())


class RasterBackdropTests(unittest.TestCase):
    def test_source_validation_accepts_only_bounded_local_images(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "reef image.png"
            image.write_bytes(b"not decoded during path validation")
            config = AQUARIUM.normalise_config({
                "backdrop": {"source": "image", "imagePath": str(image)},
            })
            raster = AQUARIUM.RasterBackdrop(config)
            self.assertEqual(raster._source_path(), image.resolve())

            text = root / "reef.txt"
            text.write_text("not an image", encoding="utf-8")
            config["backdrop"]["imagePath"] = str(text)
            rejected = AQUARIUM.RasterBackdrop(config)
            self.assertIsNone(rejected._source_path())
            self.assertIn("unsupported", rejected.error)

    def test_missing_image_uses_a_clear_fallback(self) -> None:
        config = AQUARIUM.normalise_config({
            "backdrop": {"source": "image", "imagePath": "/definitely/missing/reef.png"},
        })
        raster = AQUARIUM.RasterBackdrop(config)
        self.assertFalse(raster.prepare())
        self.assertIn("using plain depth", raster.error)

    def test_terminal_compatibility_and_protocol_placement_are_explicit(self) -> None:
        self.assertTrue(AQUARIUM.RasterBackdrop.terminal_supported({"TERM_PROGRAM": "ghostty"}))
        self.assertTrue(AQUARIUM.RasterBackdrop.terminal_supported({"TERM": "xterm-kitty"}))
        self.assertFalse(AQUARIUM.RasterBackdrop.terminal_supported({"TERM": "xterm-256color"}))

        sequence = AQUARIUM.RasterBackdrop.placement_sequence(Path("/tmp/reef.png"), 120, 36)
        self.assertIn("a=T", sequence)
        self.assertIn("t=f", sequence)
        self.assertIn("z=-1", sequence)
        self.assertIn("c=120,r=36", sequence)


class AsciiBackdropTests(unittest.TestCase):
    @staticmethod
    def config(**ascii_overrides: object) -> dict[str, object]:
        return AQUARIUM.normalise_config({
            "species": {key: 0 for key in AQUARIUM.SPRITES},
            "art": {"showTelemetry": False},
            "backdrop": {
                "source": "ascii",
                "effectsEnabled": False,
                "ascii": {
                    "detail": 70,
                    "glyphMode": "ramp",
                    "colorMode": "truecolor",
                    "dither": False,
                    **ascii_overrides,
                },
            },
        })

    def test_rgb_conversion_is_deterministic_and_cell_bounded(self) -> None:
        converter = AQUARIUM.AsciiBackdrop(self.config())
        raw = bytes((
            0, 0, 0, 255, 255, 255,
            255, 0, 0, 0, 180, 255,
        ))
        first = converter._build_payload(raw, 2, 2, 8, 4)
        second = converter._build_payload(raw, 2, 2, 8, 4)
        grid = converter._decode_payload(first, 8, 4)

        self.assertEqual(first, second)
        self.assertEqual(len(first), 8 * 4 * 4)
        self.assertEqual((len(grid), len(grid[0])), (4, 8))
        self.assertTrue(all(glyph in converter.GLYPHS["ramp"] for row in grid for glyph, _ in row))

    def test_glyph_colour_and_dither_modes_change_the_payload(self) -> None:
        raw = bytes((116, 129, 171)) * 16
        truecolor = AQUARIUM.AsciiBackdrop(self.config())._build_payload(raw, 4, 4, 4, 4)
        palette_config = self.config(glyphMode="blocks", colorMode="palette", dither=True)
        palette_converter = AQUARIUM.AsciiBackdrop(palette_config)
        palette_payload = palette_converter._build_payload(raw, 4, 4, 4, 4)
        palette_grid = palette_converter._decode_payload(palette_payload, 4, 4)
        allowed_colours = {
            AQUARIUM.PALETTES["lagoon"][key]
            for key in ("background", "dim", "water", "caustic", "text")
        }

        self.assertNotEqual(truecolor, palette_payload)
        self.assertTrue(all(glyph in palette_converter.GLYPHS["blocks"] for row in palette_grid for glyph, _ in row))
        self.assertTrue(all(colour in allowed_colours for row in palette_grid for _, colour in row))

    def test_cache_key_tracks_geometry_settings_and_source_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.png"
            source.write_bytes(b"source")
            converter = AQUARIUM.AsciiBackdrop(self.config())
            initial = converter.cache_signature(source, 80, 24)
            self.assertNotEqual(initial, converter.cache_signature(source, 81, 24))

            converter.settings["ascii"]["detail"] = 71
            settings_changed = converter.cache_signature(source, 80, 24)
            self.assertNotEqual(initial, settings_changed)

            converter.settings["ascii"]["detail"] = 70
            metadata = source.stat()
            os.utime(source, ns=(metadata.st_atime_ns, metadata.st_mtime_ns + 1_000_000))
            self.assertNotEqual(initial, converter.cache_signature(source, 80, 24))

    def test_corrupt_payload_and_missing_source_use_safe_fallbacks(self) -> None:
        converter = AQUARIUM.AsciiBackdrop(self.config())
        with self.assertRaises(ValueError):
            converter._build_payload(b"\x00", 2, 2, 4, 4)

        missing_config = self.config()
        missing_config["backdrop"]["imagePath"] = "/definitely/missing/ascii-source.png"
        missing = AQUARIUM.AsciiBackdrop(missing_config)
        self.assertFalse(missing.prepare(40, 16))
        self.assertIn("using plain depth", missing.error)

    def test_ascii_scene_ansi_output_has_a_linear_size_bound(self) -> None:
        config = self.config()
        scene = AQUARIUM.OceanScene(40, 16, config, seed=7)
        scene.ascii_backdrop = [
            [
                ("▓", ((x * 17) % 256, (y * 29) % 256, ((x + y) * 11) % 256))
                for x in range(scene.width)
            ]
            for y in range(scene.height)
        ]
        rendered = scene.render().ansi()
        self.assertLess(len(rendered), scene.width * scene.height * 32)
        self.assertIn("\x1b[38;2;", rendered)


class DismissalInputTests(unittest.TestCase):
    def test_pointer_motion_follows_setting(self) -> None:
        report = b"\x1b[<35;42;9M"
        self.assertTrue(AQUARIUM.DismissalInput(True).feed(report, now=1.0))
        self.assertFalse(AQUARIUM.DismissalInput(False).feed(report, now=1.0))

    def test_click_and_keyboard_always_dismiss(self) -> None:
        decoder = AQUARIUM.DismissalInput(False)
        self.assertTrue(decoder.feed(b"\x1b[<0;42;9M", now=1.0))
        self.assertTrue(AQUARIUM.DismissalInput(False).feed(b"x", now=1.0))

    def test_fragmented_motion_report_is_not_misclassified(self) -> None:
        decoder = AQUARIUM.DismissalInput(False)
        self.assertFalse(decoder.feed(b"\x1b[<35;42", now=1.0))
        self.assertFalse(decoder.feed(b";9M", now=1.01))

    def test_standalone_escape_expires_as_keyboard_input(self) -> None:
        decoder = AQUARIUM.DismissalInput(False)
        self.assertFalse(decoder.feed(b"\x1b", now=1.0))
        self.assertTrue(decoder.expired(now=1.07))


class AudioTests(unittest.TestCase):
    def test_pipewire_stream_is_explicitly_raw_pcm(self) -> None:
        command = AQUARIUM.AmbientAudio.playback_command()
        self.assertIn("--raw", command)
        self.assertEqual(command[-1], "-")
        self.assertEqual(command[command.index("--format") + 1], "s16")

    def test_audio_test_defaults_to_eight_seconds_without_a_tty(self) -> None:
        arguments = AQUARIUM.parse_args(["--audio-test"])
        self.assertEqual(arguments.audio_test, 8.0)
        self.assertTrue(AQUARIUM.parse_args(["--check-backdrop"]).check_backdrop)
        self.assertTrue(AQUARIUM.parse_args(["--ascii-preview"]).ascii_preview)


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
