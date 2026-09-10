from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.ecosystem_model import initial_model, model_to_json

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
            "art": {"palette": "not-a-palette", "bubbleDensity": 155, "current": 0, "showTelemetry": 0, "reefDensity": 400},
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
        self.assertEqual(config["art"]["reefDensity"], 100)
        self.assertEqual(config["backdrop"]["source"], "plain")
        self.assertFalse(config["backdrop"]["effectsEnabled"])
        self.assertEqual(config["backdrop"]["effectIntensity"], 100)
        self.assertTrue(config["sound"]["enabled"])
        self.assertEqual(config["sound"]["volume"], 41)
        self.assertTrue(config["sound"]["water"])
        self.assertTrue(config["sound"]["bubbles"])
        self.assertFalse(config["integration"]["idleEnabled"])
        self.assertFalse(config["integration"]["exitOnPointerMotion"])

    def test_legacy_vegetation_volume_key_is_accepted_as_reef_density(self) -> None:
        config = AQUARIUM.normalise_config({"art": {"vegetationVolume": 75}})
        self.assertEqual(config["art"]["reefDensity"], 75)

    def test_sound_channels_are_normalized_and_accept_aliases(self) -> None:
        config = AQUARIUM.normalise_config({
            "sound": {"water": False, "bubbles": True},
        })
        self.assertFalse(config["sound"]["water"])
        self.assertTrue(config["sound"]["bubbles"])

        config_alias = AQUARIUM.normalise_config({
            "sound": {"waterFlow": False, "bubblesEnabled": False},
        })
        self.assertFalse(config_alias["sound"]["water"])
        self.assertFalse(config_alias["sound"]["bubbles"])

        config_enabled_alias = AQUARIUM.normalise_config({
            "sound": {"waterEnabled": False},
        })
        self.assertFalse(config_enabled_alias["sound"]["water"])
        self.assertTrue(config_enabled_alias["sound"]["bubbles"])

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

    def test_malformed_sections_use_packaged_defaults(self) -> None:
        config = AQUARIUM.normalise_config({
            "species": "many",
            "art": [],
            "backdrop": 42,
            "sound": None,
            "integration": "enabled",
        })
        defaults = json.loads((ROOT / "defaults.json").read_text(encoding="utf-8"))
        self.assertEqual(config, defaults)

    def test_oversized_configuration_is_rejected_before_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.json"
            path.write_bytes(b" " * (AQUARIUM.MAX_CONFIG_BYTES + 1))
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

    def test_evolution_status_and_statistics_overlay_use_shared_telemetry(self) -> None:
        config = AQUARIUM.normalise_config({"art": {"showTelemetry": True}})
        scene = AQUARIUM.OceanScene(100, 28, config, seed=17)
        scene.evolution_telemetry = {
            "biologicalMinutes": 125.0,
            "population": 31,
            "speciesPresent": 7,
            "speciesTotal": 8,
            "generation": 3,
            "mutationEvents": 4,
            "births": 12,
            "deaths": 5,
            "resourceCount": 24,
            "resourceAmount": 18.5,
            "foodAbundance": 1.0,
            "predatorPressure": 1.0,
            "mutationRate": 0.08,
            "speciesPopulation": {"neon_tetra": 10},
        }
        status = scene.render().plain()
        self.assertIn("LIFE 2h 05m", status)
        self.assertIn("POP 31", status)
        scene.statistics_visible = True
        statistics = scene.render().plain()
        self.assertIn("EVOLUTION TELEMETRY", statistics)
        self.assertIn("MUTATION EVENTS   4", statistics)

    def test_scene_dimensions_are_bounded(self) -> None:
        self.assertEqual(
            AQUARIUM.clamp_dimensions(10**9, 10**9),
            (AQUARIUM.MAX_TERMINAL_COLUMNS, AQUARIUM.MAX_TERMINAL_LINES),
        )
        self.assertEqual(AQUARIUM.clamp_dimensions(-1, -1), (40, 16))

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


    def test_reef_density_scales_coral_and_kelp(self) -> None:
        base = {
            "species": {key: 0 for key in AQUARIUM.SPRITES},
            "art": {"showTelemetry": False, "reefDensity": 0},
            "backdrop": {"source": "plain", "effectsEnabled": False},
        }
        bare = AQUARIUM.OceanScene(100, 28, AQUARIUM.normalise_config(base), seed=7).render().plain()
        self.assertNotIn("}", bare)
        self.assertNotIn("{", bare)
        self.assertNotIn("\\ | /", bare)

        base["art"]["reefDensity"] = 25
        low = AQUARIUM.OceanScene(100, 28, AQUARIUM.normalise_config(base), seed=7).render().plain()
        low_stalk_chars = low.count("}") + low.count("{")
        low_coral_chars = low.count("\\") + low.count("/") + low.count("|")

        base["art"]["reefDensity"] = 100
        dense = AQUARIUM.OceanScene(100, 28, AQUARIUM.normalise_config(base), seed=7).render().plain()
        dense_stalk_chars = dense.count("}") + dense.count("{")
        dense_coral_chars = dense.count("\\") + dense.count("/") + dense.count("|")

        self.assertGreater(low_stalk_chars, 0)
        self.assertGreater(dense_stalk_chars, low_stalk_chars * 2)
        self.assertGreater(dense_coral_chars, low_coral_chars * 2)
class EvolutionTelemetryTests(unittest.TestCase):
    def test_refresh_reads_shared_snapshot_and_coalesces_polls(self) -> None:
        calls = []

        def requester(payload, timeout):
            calls.append((payload, timeout))
            return {"snapshot": model_to_json(initial_model(7))}

        adapter = AQUARIUM.EvolutionTelemetry(requester)
        self.assertTrue(adapter.refresh(0.0))
        self.assertFalse(adapter.refresh(0.05))
        self.assertTrue(adapter.refresh(0.1))
        self.assertEqual(len(calls), 2)
        self.assertEqual(adapter.data["population"], 29)
        self.assertEqual(calls[0][0], {"operation": "snapshot"})
        self.assertEqual(calls[0][1], 0.02)

    def test_refresh_falls_back_without_breaking_the_renderer(self) -> None:
        def requester(_payload, _timeout):
            raise OSError("service unavailable")

        adapter = AQUARIUM.EvolutionTelemetry(requester)
        self.assertTrue(adapter.refresh(0.0))
        self.assertIsNone(adapter.data)
        self.assertEqual(adapter.error, "EVO OFFLINE")

    def test_i_toggles_statistics_but_other_input_dismisses(self) -> None:
        config = AQUARIUM.normalise_config({"art": {"showTelemetry": False}})
        scene = AQUARIUM.OceanScene(80, 24, config, seed=7)
        dismissal = AQUARIUM.DismissalInput(False)
        self.assertFalse(AQUARIUM.handle_terminal_input(b"i", scene, dismissal, 0.0))
        self.assertTrue(scene.statistics_visible)
        self.assertFalse(AQUARIUM.handle_terminal_input(b"I", scene, dismissal, 0.1))
        self.assertFalse(scene.statistics_visible)
        self.assertTrue(AQUARIUM.handle_terminal_input(b"x", scene, dismissal, 0.2))


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

    def test_image_decoder_is_forced_from_the_allowed_suffix(self) -> None:
        self.assertEqual(
            AQUARIUM.RasterBackdrop.image_spec(Path("/tmp/reef image.png")),
            "png:/tmp/reef image.png[0]",
        )

    def test_cache_pruning_keeps_current_and_enforces_file_limit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory)
            current = cache / "backdrop-current.png"
            current.write_bytes(b"current")
            for index in range(AQUARIUM.RasterBackdrop.MAX_CACHE_FILES + 5):
                (cache / f"backdrop-{index:02d}.png").write_bytes(b"x")

            AQUARIUM.RasterBackdrop.prune_cache(cache, current)
            remaining = list(cache.glob("backdrop-*.png"))

        self.assertIn(current.name, {path.name for path in remaining})
        self.assertLessEqual(len(remaining), AQUARIUM.RasterBackdrop.MAX_CACHE_FILES)


class FilesystemSecurityTests(unittest.TestCase):
    def test_lock_open_refuses_symlinks_without_touching_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_text("preserve me", encoding="utf-8")
            lock = root / "audio.lock"
            lock.symlink_to(target)

            with self.assertRaises(OSError):
                AQUARIUM.open_lock_file(lock)

            self.assertEqual(target.read_text(encoding="utf-8"), "preserve me")

    def test_runtime_fallback_stays_in_the_private_user_cache(self) -> None:
        original_runtime = os.environ.pop("XDG_RUNTIME_DIR", None)
        try:
            runtime = AQUARIUM.runtime_directory()
        finally:
            if original_runtime is not None:
                os.environ["XDG_RUNTIME_DIR"] = original_runtime

        self.assertEqual(runtime, AQUARIUM.user_cache_home() / "omarcharium" / "runtime")



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
    def test_ambient_audio_accepts_individual_channel_toggles(self) -> None:
        audio = AQUARIUM.AmbientAudio(50, Path("/tmp"), water=False, bubbles=True)
        self.assertFalse(audio.water)
        self.assertTrue(audio.bubbles)

    def test_ambient_audio_refuses_start_when_all_channels_disabled(self) -> None:
        audio = AQUARIUM.AmbientAudio(50, Path("/tmp"), water=False, bubbles=False)
        self.assertFalse(audio.start())
        self.assertEqual(audio.last_error, "water and bubble audio components are both disabled")

    def test_ambient_audio_refuses_start_when_volume_is_zero(self) -> None:
        audio = AQUARIUM.AmbientAudio(0, Path("/tmp"), water=True, bubbles=True)
        self.assertFalse(audio.start())
        self.assertEqual(audio.last_error, "volume is zero")
    def test_ambient_audio_synthesises_expected_channels(self) -> None:
        audio_water = AQUARIUM.AmbientAudio(100, Path("/tmp"), diagnostic=False, water=True, bubbles=False)
        self.assertTrue(audio_water.water)
        self.assertFalse(audio_water.bubbles)

        audio_bubbles = AQUARIUM.AmbientAudio(100, Path("/tmp"), diagnostic=False, water=False, bubbles=True)
        self.assertFalse(audio_bubbles.water)
        self.assertTrue(audio_bubbles.bubbles)




class IdleIntegrationTests(unittest.TestCase):
    def run_helper(
        self, state_home: Path, action: str, *, check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["XDG_STATE_HOME"] = str(state_home)
        return subprocess.run(
            ["bash", str(ROOT / "scripts" / "idle-integration"), action],
            check=check,
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

    def test_legacy_empty_ownership_state_is_migrated_before_release(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            toggle = state / "omarchy" / "toggles" / "screensaver-off"
            owner = state / "omarcharium" / "owns-screensaver-off"
            toggle.parent.mkdir(parents=True)
            owner.parent.mkdir(parents=True)
            toggle.touch()
            owner.touch()

            self.run_helper(state, "enable")
            status = self.run_helper(state, "status")

            self.assertGreater(toggle.stat().st_size, 0)
            self.assertEqual(toggle.read_bytes(), owner.read_bytes())
            self.assertEqual(status.stdout.strip(), "owned")
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

    def test_replaced_toggle_is_not_mistaken_for_owned_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            self.run_helper(state, "enable")
            toggle = state / "omarchy" / "toggles" / "screensaver-off"
            owner = state / "omarcharium" / "owns-screensaver-off"
            toggle.unlink()
            toggle.touch()

            self.run_helper(state, "disable")

            self.assertTrue(toggle.exists())
            self.assertFalse(owner.exists())

    def test_symlinked_owner_is_refused_without_modifying_target(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            owner = state / "omarcharium" / "owns-screensaver-off"
            owner.parent.mkdir(parents=True)
            target = state / "target"
            target.write_text("preserve me", encoding="utf-8")
            owner.symlink_to(target)

            result = self.run_helper(state, "enable", check=False)

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(target.read_text(encoding="utf-8"), "preserve me")
            self.assertFalse((state / "omarchy" / "toggles" / "screensaver-off").exists())

    def test_owned_state_is_private_and_reports_owned(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            self.run_helper(state, "enable")
            toggle = state / "omarchy" / "toggles" / "screensaver-off"
            owner_dir = state / "omarcharium"
            owner = owner_dir / "owns-screensaver-off"

            status = self.run_helper(state, "status")

            self.assertEqual(status.stdout.strip(), "owned")
            self.assertEqual(owner_dir.stat().st_mode & 0o777, 0o700)
            self.assertEqual(toggle.stat().st_mode & 0o777, 0o600)
            self.assertEqual(owner.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
