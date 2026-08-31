#!/usr/bin/env python3
"""Omarcharium: a terminal-native tropical aquarium for Omarchy.

The interactive path paints an ANSI true-colour scene until any keyboard or
mouse input arrives.  The snapshot and configuration modes are deterministic,
which keeps the renderer testable without a compositor or terminal emulator.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import json
import math
import os
import random
import select
import shutil
import signal
import struct
import subprocess
import sys
import termios
import threading
import time
import tty
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

PLUGIN_DIR = Path(__file__).resolve().parent.parent
DEFAULTS_PATH = PLUGIN_DIR / "defaults.json"
SPECIES_PATH = PLUGIN_DIR / "species.json"
CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "omarcharium" / "config.json"

RGB = tuple[int, int, int]

PALETTES: dict[str, dict[str, RGB]] = {
    "lagoon": {
        "background": (2, 18, 28), "water": (29, 120, 143), "caustic": (93, 230, 226),
        "sand": (180, 141, 86), "rock": (45, 82, 78), "kelp": (42, 167, 117),
        "coral": (255, 103, 126), "dim": (31, 79, 92), "text": (161, 241, 235),
    },
    "midnight": {
        "background": (1, 6, 18), "water": (24, 54, 111), "caustic": (95, 109, 232),
        "sand": (91, 81, 116), "rock": (39, 47, 82), "kelp": (29, 119, 119),
        "coral": (181, 80, 205), "dim": (31, 51, 94), "text": (147, 186, 255),
    },
    "coral": {
        "background": (21, 8, 20), "water": (138, 49, 93), "caustic": (255, 149, 111),
        "sand": (220, 151, 92), "rock": (91, 49, 68), "kelp": (103, 171, 113),
        "coral": (255, 82, 95), "dim": (95, 45, 76), "text": (255, 216, 175),
    },
    "phosphor": {
        "background": (0, 11, 8), "water": (20, 105, 66), "caustic": (99, 255, 169),
        "sand": (81, 149, 90), "rock": (30, 67, 47), "kelp": (49, 192, 91),
        "coral": (153, 255, 123), "dim": (22, 77, 48), "text": (155, 255, 189),
    },
}

FISH_COLOURS: dict[str, tuple[RGB, RGB, RGB]] = {
    "neon_tetra": ((52, 219, 255), (245, 76, 126), (157, 245, 255)),
    "clownfish": ((255, 132, 48), (255, 239, 191), (156, 54, 35)),
    "angelfish": ((242, 229, 175), (97, 208, 220), (147, 118, 94)),
    "discus": ((255, 92, 174), (80, 224, 211), (126, 52, 130)),
    "butterflyfish": ((255, 225, 70), (255, 250, 202), (44, 67, 79)),
    "royal_tang": ((65, 137, 255), (255, 227, 62), (20, 55, 138)),
    "betta": ((187, 93, 255), (64, 224, 239), (106, 43, 148)),
    "puffer": ((164, 232, 101), (255, 222, 90), (62, 104, 63)),
}

# Right-facing animation frames. Spaces are transparent; all glyphs are one
# terminal cell wide so geometry is stable under any monospace font.
SPRITES: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "neon_tetra": (
        ("  __/=>", "<==_o_>"),
        ("  __/=>", "<~=_o_>"),
    ),
    "clownfish": (
        ("   .---.  ", "<==|o|==)>", "   '---'  "),
        ("  .----.  ", "<~=|o|==)>", "  '----'  "),
    ),
    "angelfish": (
        ("    /|   ", " __/ |   ", "<== o|)>", "   \\ |   ", "    \\|   "),
        ("    /|   ", "  _/ |   ", "<~= o|)>", " __\\ |   ", "    \\|   "),
    ),
    "discus": (
        ("  .-===-. ", "<=| o  |)>", "  '-===-' "),
        ("  .-===-. ", "<~| o  |)>", "  '-===-' "),
    ),
    "butterflyfish": (
        ("    /\\   ", "<==/##\\  ", "  |#o#|)>", "   \\##/  "),
        ("   _/\\   ", "<~=/##\\  ", "  |#o#|)>", "   \\##/  "),
    ),
    "royal_tang": (
        ("   __---. ", "<==  @  )>", "   '--__' "),
        ("   __---. ", "<~=  @  )>", "   '--__' "),
    ),
    "betta": (
        ("     __   ", "<~~~~_o\\)>", "  ~~  /  ", "   ~~/   "),
        ("    ___   ", "<~~~__o\\)>", "   ~~ /  ", "  ~~ /   "),
    ),
    "puffer": (
        ("  ^-^-^  ", "<= (o ) >", "  v-v-v  "),
        ("  ^-^-^  ", "<~ (o ) >", "  v-v-v  "),
    ),
}

MIRROR_TABLE = str.maketrans("<>/\\(){}[]", "><\\/)(}{][")


def mirror_sprite(lines: Iterable[str]) -> tuple[str, ...]:
    return tuple(line.translate(MIRROR_TABLE)[::-1] for line in lines)


def deep_merge(base: dict[str, Any], overlay: Any) -> dict[str, Any]:
    result = copy.deepcopy(base)
    if not isinstance(overlay, dict):
        return result
    for key, value in overlay.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def clamp_number(value: Any, low: float, high: float, fallback: float) -> float:
    if isinstance(value, bool):
        return fallback
    try:
        number = float(value)
    except (TypeError, ValueError):
        return fallback
    if not math.isfinite(number):
        return fallback
    return max(low, min(high, number))


def read_json(path: Path, fallback: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return copy.deepcopy(fallback)


def normalise_config(raw: Any) -> dict[str, Any]:
    defaults = read_json(DEFAULTS_PATH, {})
    merged = deep_merge(defaults, raw)
    default_species = defaults.get("species", {})
    incoming_species = merged.get("species", {})
    species: dict[str, int] = {}
    for key, fallback in default_species.items():
        species[key] = int(clamp_number(incoming_species.get(key), 0, 20, fallback))

    art = merged.get("art", {})
    fallback_art = defaults.get("art", {})
    palette = str(art.get("palette", fallback_art.get("palette", "lagoon")))
    if palette not in PALETTES:
        palette = "lagoon"

    sound = merged.get("sound", {})
    fallback_sound = defaults.get("sound", {})
    integration = merged.get("integration", {})
    fallback_integration = defaults.get("integration", {})
    return {
        "schemaVersion": 1,
        "species": species,
        "art": {
            "palette": palette,
            "bubbleDensity": int(clamp_number(art.get("bubbleDensity"), 0, 100, fallback_art.get("bubbleDensity", 55))),
            "current": round(clamp_number(art.get("current"), 0.35, 1.8, fallback_art.get("current", 1.0)), 2),
            "showTelemetry": bool(art.get("showTelemetry", fallback_art.get("showTelemetry", True))),
        },
        "sound": {
            "enabled": bool(sound.get("enabled", fallback_sound.get("enabled", False))),
            "volume": int(clamp_number(sound.get("volume"), 0, 100, fallback_sound.get("volume", 24))),
        },
        "integration": {
            "idleEnabled": bool(integration.get("idleEnabled", fallback_integration.get("idleEnabled", True))),
        },
    }


def load_config(path: Path) -> dict[str, Any]:
    return normalise_config(read_json(path, {}))


@dataclass(slots=True)
class Fish:
    species: str
    x: float
    base_y: float
    direction: int
    speed: float
    phase: float
    bob_rate: float
    bob_height: float
    frame_phase: float


@dataclass(slots=True)
class Bubble:
    x: float
    y: float
    speed: float
    drift: float
    size: int
    phase: float


@dataclass(slots=True)
class Mote:
    x: float
    y: float
    phase: float
    speed: float


class FrameBuffer:
    __slots__ = ("width", "height", "chars", "colours")

    def __init__(self, width: int, height: int) -> None:
        self.width = width
        self.height = height
        self.chars = [[" "] * width for _ in range(height)]
        self.colours: list[list[RGB | None]] = [[None] * width for _ in range(height)]

    def put(self, x: int, y: int, char: str, colour: RGB | None) -> None:
        if 0 <= x < self.width and 0 <= y < self.height and char:
            self.chars[y][x] = char[0]
            self.colours[y][x] = colour

    def text(self, x: int, y: int, text: str, colour: RGB | None) -> None:
        for offset, char in enumerate(text):
            self.put(x + offset, y, char, colour)

    def plain(self) -> str:
        return "\n".join("".join(row).rstrip() for row in self.chars)

    def ansi(self) -> str:
        output: list[str] = ["\x1b[H"]
        current: RGB | None = None
        for y, row in enumerate(self.chars):
            last = self.width - 1
            while last >= 0 and row[last] == " ":
                last -= 1
            for x in range(last + 1):
                colour = self.colours[y][x]
                if colour is not None and colour != current:
                    output.append(f"\x1b[38;2;{colour[0]};{colour[1]};{colour[2]}m")
                    current = colour
                output.append(row[x])
            output.append("\x1b[K")
            if y != self.height - 1:
                output.append("\n")
        output.append("\x1b[0m")
        return "".join(output)


class OceanScene:
    def __init__(self, width: int, height: int, config: dict[str, Any], seed: int) -> None:
        self.width = max(40, width)
        self.height = max(16, height)
        self.config = config
        self.rng = random.Random(seed)
        self.elapsed = 0.0
        self.frame = 0
        self.fish: list[Fish] = []
        self.bubbles: list[Bubble] = []
        self.motes: list[Mote] = []
        self._populate()

    @property
    def palette(self) -> dict[str, RGB]:
        return PALETTES[self.config["art"]["palette"]]

    def _populate(self) -> None:
        self.fish.clear()
        for species, count in self.config["species"].items():
            if species not in SPRITES:
                continue
            for index in range(count):
                frame = SPRITES[species][0]
                depth_min = 5 + (index % 3)
                depth_max = max(depth_min + 1, self.height - len(frame) - 6)
                direction = self.rng.choice((-1, 1))
                base_speed = {
                    "neon_tetra": 8.0, "clownfish": 4.8, "angelfish": 2.4,
                    "discus": 2.9, "butterflyfish": 4.0, "royal_tang": 5.6,
                    "betta": 2.0, "puffer": 2.2,
                }.get(species, 3.5)
                self.fish.append(Fish(
                    species=species,
                    x=self.rng.uniform(-10, self.width + 10),
                    base_y=self.rng.uniform(depth_min, depth_max),
                    direction=direction,
                    speed=base_speed * self.rng.uniform(0.72, 1.28),
                    phase=self.rng.uniform(0, math.tau),
                    bob_rate=self.rng.uniform(0.45, 1.15),
                    bob_height=self.rng.uniform(0.35, 1.4),
                    frame_phase=self.rng.uniform(0, math.tau),
                ))

        density = self.config["art"]["bubbleDensity"]
        bubble_count = int((self.width * self.height) * density / 8500) + density // 12
        for _ in range(bubble_count):
            self.bubbles.append(self._new_bubble(self.rng.uniform(2, self.height - 3)))

        mote_count = max(10, self.width * self.height // 260)
        for _ in range(mote_count):
            self.motes.append(Mote(
                x=self.rng.uniform(0, self.width), y=self.rng.uniform(3, self.height - 4),
                phase=self.rng.uniform(0, math.tau), speed=self.rng.uniform(0.05, 0.24),
            ))

    def _new_bubble(self, y: float | None = None) -> Bubble:
        return Bubble(
            x=self.rng.uniform(2, self.width - 2),
            y=self.height - 3 if y is None else y,
            speed=self.rng.uniform(1.6, 4.8),
            drift=self.rng.uniform(0.3, 1.1),
            size=self.rng.choices((0, 1, 2), weights=(6, 3, 1))[0],
            phase=self.rng.uniform(0, math.tau),
        )

    def resize(self, width: int, height: int) -> None:
        if width == self.width and height == self.height:
            return
        self.width = max(40, width)
        self.height = max(16, height)
        for fish in self.fish:
            fish.x %= self.width + 20
            fish.base_y = max(4, min(self.height - 8, fish.base_y))
        for bubble in self.bubbles:
            bubble.x %= self.width
            bubble.y = max(3, min(self.height - 3, bubble.y))

    def update(self, dt: float) -> None:
        dt = min(0.1, max(0.0, dt))
        self.elapsed += dt
        self.frame += 1
        current = self.config["art"]["current"]
        for fish in self.fish:
            fish.x += fish.direction * fish.speed * current * dt
            sprite_width = max(map(len, SPRITES[fish.species][0]))
            if fish.direction > 0 and fish.x > self.width + sprite_width:
                fish.x = -sprite_width - self.rng.uniform(0, self.width * 0.25)
                fish.base_y = self.rng.uniform(5, max(6, self.height - 9))
            elif fish.direction < 0 and fish.x < -sprite_width * 2:
                fish.x = self.width + self.rng.uniform(0, self.width * 0.25)
                fish.base_y = self.rng.uniform(5, max(6, self.height - 9))

        for bubble in self.bubbles:
            bubble.y -= bubble.speed * dt
            bubble.x += math.sin(self.elapsed * 1.7 + bubble.phase) * bubble.drift * dt
            if bubble.y < 3:
                replacement = self._new_bubble()
                bubble.x, bubble.y = replacement.x, replacement.y
                bubble.speed, bubble.drift = replacement.speed, replacement.drift
                bubble.size, bubble.phase = replacement.size, replacement.phase

        for mote in self.motes:
            mote.x += math.sin(self.elapsed * mote.speed + mote.phase) * dt * 0.18
            mote.y += math.cos(self.elapsed * mote.speed * 0.7 + mote.phase) * dt * 0.08

    def _draw_water(self, canvas: FrameBuffer) -> None:
        palette = self.palette
        for x in range(0, self.width, 2):
            surface = 2 + int(round(math.sin(x * 0.13 + self.elapsed * 0.7)))
            char = "~" if (x // 2 + self.frame // 8) % 3 else "_"
            canvas.put(x, surface, char, palette["caustic"])
        for mote in self.motes:
            brightness = (math.sin(self.elapsed * 1.6 + mote.phase) + 1) * 0.5
            char = "." if brightness < 0.72 else "+"
            colour = palette["dim"] if char == "." else palette["water"]
            canvas.put(int(mote.x), int(mote.y), char, colour)

        # Narrow shafts of terminal light descend from the animated surface.
        for shaft in range(3):
            centre = int((self.width * (shaft + 0.7) / 3.5 + self.elapsed * (shaft + 1) * 0.35) % self.width)
            for y in range(4, min(self.height - 5, 15 + shaft * 3)):
                x = centre + int(math.sin(y * 0.22 + self.elapsed) * 2)
                if (y + shaft) % 3 == 0:
                    canvas.put(x, y, ":", palette["dim"])

    def _draw_habitat(self, canvas: FrameBuffer) -> None:
        palette = self.palette
        floor = self.height - 3
        for x in range(self.width):
            ridge = int(1.4 * math.sin(x * 0.09) + 0.7 * math.sin(x * 0.31))
            y = floor + ridge // 2
            canvas.put(x, y, "_" if x % 4 else ".", palette["sand"])
            if y + 1 < self.height:
                canvas.put(x, y + 1, ".", palette["rock"])

        # Kelp columns are deterministic functions, so they sway without object churn.
        kelp_positions = (8, 17, self.width - 14, self.width - 31)
        for plant, anchor in enumerate(kelp_positions):
            if not 2 <= anchor < self.width - 2:
                continue
            height = 5 + (plant * 3) % 8
            for segment in range(height):
                y = floor - segment
                sway = int(round(math.sin(self.elapsed * (0.7 + plant * 0.08) + segment * 0.55 + plant)))
                canvas.put(anchor + sway, y, "}" if sway >= 0 else "{", palette["kelp"])
            canvas.put(anchor, floor + 1, "Y", palette["kelp"])

        # A central branching coral acts as the visual signature of each scene.
        coral_x = self.width // 2 + int(math.sin(self.width) * self.width * 0.08)
        coral_lines = ("   \\ | /", "  \\ \\|/ /", "---\\ | /---", "    \\|/", "     Y")
        start_y = floor - len(coral_lines) + 2
        for row, line in enumerate(coral_lines):
            canvas.text(coral_x - 6, start_y + row, line, palette["coral"])

        for rock_x, glyph in ((2, "[__]"), (self.width // 3, "(_/\\_)"), (self.width - 9, "[___]")):
            canvas.text(rock_x, floor, glyph, palette["rock"])

    def _draw_bubbles(self, canvas: FrameBuffer) -> None:
        palette = self.palette
        glyphs = (".", "o", "O")
        for bubble in self.bubbles:
            canvas.put(int(bubble.x), int(bubble.y), glyphs[bubble.size], palette["caustic"])
            if bubble.size == 2 and bubble.y > 5:
                canvas.put(int(bubble.x) - 1, int(bubble.y), "·", palette["water"])

    def _draw_fish(self, canvas: FrameBuffer) -> None:
        for fish in sorted(self.fish, key=lambda item: item.base_y):
            frame_index = int(self.elapsed * (2.2 + fish.speed * 0.08) + fish.frame_phase) & 1
            lines = SPRITES[fish.species][frame_index]
            if fish.direction < 0:
                lines = mirror_sprite(lines)
            body, accent, shadow = FISH_COLOURS[fish.species]
            y = int(round(fish.base_y + math.sin(self.elapsed * fish.bob_rate + fish.phase) * fish.bob_height))
            x = int(round(fish.x))
            for row, line in enumerate(lines):
                for column, char in enumerate(line):
                    if char == " ":
                        continue
                    if char in "oO@#=|":
                        colour = accent
                    elif char in "_.'~-":
                        colour = shadow
                    else:
                        colour = body
                    canvas.put(x + column, y + row, char, colour)

    def _draw_telemetry(self, canvas: FrameBuffer) -> None:
        if not self.config["art"]["showTelemetry"]:
            return
        palette = self.palette
        fish_count = len(self.fish)
        title = " OMARCHARIUM // PELAGIC TERMINAL ENVIRONMENT "
        right = f" BIOMASS {fish_count:02d} // {self.config['art']['palette'].upper()} "
        canvas.text(1, 0, title[: max(0, self.width - 2)], palette["text"])
        if len(right) + 1 < self.width:
            canvas.text(self.width - len(right) - 1, 0, right, palette["caustic"])
        footer = "[ any key / pointer movement returns to surface ]"
        if len(footer) + 2 < self.width:
            canvas.text((self.width - len(footer)) // 2, self.height - 1, footer, palette["dim"])

    def render(self) -> FrameBuffer:
        canvas = FrameBuffer(self.width, self.height)
        self._draw_water(canvas)
        self._draw_habitat(canvas)
        self._draw_bubbles(canvas)
        self._draw_fish(canvas)
        self._draw_telemetry(canvas)
        return canvas


class AmbientAudio:
    """Water and bubble synthesis streamed directly to PipeWire."""

    def __init__(self, volume: int, runtime_dir: Path, diagnostic: bool = False) -> None:
        self.volume = max(0.0, min(1.0, volume / 100.0))
        self.runtime_dir = runtime_dir
        self.diagnostic = diagnostic
        self.stop_event = threading.Event()
        self.thread: threading.Thread | None = None
        self.process: subprocess.Popen[bytes] | None = None
        self.lock_file: Any = None
        self.last_error = ""
        self.rng = random.Random(os.getpid() ^ int(time.time()))

    @staticmethod
    def playback_command() -> list[str]:
        return [
            "pw-cat", "--playback", "--raw", "--format", "s16",
            "--rate", "24000", "--channels", "2", "-",
        ]

    def start(self) -> bool:
        if self.volume <= 0:
            self.last_error = "volume is zero"
            return False
        if not shutil.which("pw-cat"):
            self.last_error = "pw-cat is unavailable; install PipeWire tools"
            return False
        try:
            self.runtime_dir.mkdir(parents=True, exist_ok=True)
            self.lock_file = (self.runtime_dir / "omarcharium-audio.lock").open("w")
            fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            if self.lock_file:
                self.lock_file.close()
            self.lock_file = None
            self.last_error = "another Omarcharium process already owns the audio stream"
            return False
        except OSError as error:
            if self.lock_file:
                self.lock_file.close()
            self.lock_file = None
            self.last_error = f"cannot create the audio lock: {error}"
            return False
        try:
            self.process = subprocess.Popen(
                self.playback_command(),
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
        except OSError as error:
            self.last_error = f"cannot start pw-cat: {error}"
            self.close()
            return False
        self.thread = threading.Thread(target=self._synthesise, name="omarcharium-audio", daemon=True)
        self.thread.start()
        time.sleep(0.08)
        if self.process.poll() is not None:
            message = ""
            if self.process.stderr:
                try:
                    message = self.process.stderr.read().decode("utf-8", errors="replace").strip()
                except OSError:
                    pass
            self.last_error = message or f"pw-cat exited with status {self.process.returncode}"
            self.close()
            return False
        return True

    def _synthesise(self) -> None:
        assert self.process and self.process.stdin
        sample_rate = 24000
        block_size = 480
        low_noise = 0.0
        wave_phase = 0.0
        bubble_remaining = 0
        bubble_phase = 0.0
        bubble_length = 1
        bubble_start_frequency = 700.0
        rendered_samples = 0
        diagnostic_frequencies = (440.0, 660.0, 880.0)
        while not self.stop_event.is_set() and self.process.poll() is None:
            block = bytearray(block_size * 4)
            for index in range(block_size):
                low_noise = low_noise * 0.985 + self.rng.uniform(-1.0, 1.0) * 0.015
                wave_phase += math.tau * 0.17 / sample_rate
                water = low_noise * 1.35 + math.sin(wave_phase) * 0.12
                if bubble_remaining <= 0 and self.rng.random() < 0.00008:
                    bubble_length = self.rng.randint(1200, 3200)
                    bubble_remaining = bubble_length
                    bubble_start_frequency = self.rng.uniform(420.0, 920.0)
                    bubble_phase = 0.0
                bubble = 0.0
                if bubble_remaining > 0:
                    progress = 1.0 - bubble_remaining / bubble_length
                    frequency = bubble_start_frequency * (1.0 + progress * 1.7)
                    bubble_phase += math.tau * frequency / sample_rate
                    envelope = math.sin(math.pi * progress) ** 2
                    bubble = math.sin(bubble_phase) * envelope * 0.48
                    bubble_remaining -= 1

                diagnostic_tone = 0.0
                if self.diagnostic and rendered_samples < int(sample_rate * 1.8):
                    note = min(2, rendered_samples // int(sample_rate * 0.6))
                    note_sample = rendered_samples % int(sample_rate * 0.6)
                    note_progress = note_sample / (sample_rate * 0.6)
                    note_envelope = math.sin(math.pi * note_progress) ** 2
                    note_phase = math.tau * diagnostic_frequencies[note] * rendered_samples / sample_rate
                    diagnostic_tone = math.sin(note_phase) * note_envelope * 0.42

                sample = int(max(-1.0, min(1.0, (water + bubble + diagnostic_tone) * self.volume)) * 32767)
                struct.pack_into("<hh", block, index * 4, sample, sample)
                rendered_samples += 1
            try:
                self.process.stdin.write(block)
                self.process.stdin.flush()
            except (BrokenPipeError, OSError):
                break

    def close(self) -> None:
        self.stop_event.set()
        if self.thread and self.thread.is_alive() and threading.current_thread() is not self.thread:
            self.thread.join(timeout=0.3)
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=0.5)
            except subprocess.TimeoutExpired:
                self.process.kill()
        if self.lock_file:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
            self.lock_file.close()
            self.lock_file = None


class TerminalSession:
    def __init__(self, background: RGB) -> None:
        self.background = background
        self.original_attributes: list[Any] | None = None
        self.active = False

    def __enter__(self) -> "TerminalSession":
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            raise RuntimeError("Omarcharium interactive mode requires a terminal")
        self.original_attributes = termios.tcgetattr(sys.stdin.fileno())
        tty.setcbreak(sys.stdin.fileno())
        r, g, b = self.background
        sys.stdout.write(
            "\x1b[?1049h\x1b[2J\x1b[H\x1b[?25l"
            "\x1b[?1003h\x1b[?1006h"
            f"\x1b]11;rgb:{r:02x}/{g:02x}/{b:02x}\x07"
        )
        sys.stdout.flush()
        self.active = True
        return self

    def __exit__(self, *_: Any) -> None:
        if not self.active:
            return
        sys.stdout.write("\x1b[?1003l\x1b[?1006l\x1b[0m\x1b[?25h\x1b[?1049l")
        sys.stdout.flush()
        if self.original_attributes:
            termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, self.original_attributes)
        self.active = False


def terminal_size() -> tuple[int, int]:
    size = shutil.get_terminal_size(fallback=(120, 36))
    return max(40, size.columns), max(16, size.lines)


def dismiss_screensaver_windows() -> None:
    try:
        subprocess.Popen(
            ["pkill", "-f", "[o]rg.omarchy.screensaver"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def run_interactive(config: dict[str, Any], seed: int, sound_override: bool | None) -> int:
    width, height = terminal_size()
    scene = OceanScene(width, height, config, seed)
    palette = scene.palette
    runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/omarcharium-{os.getuid()}"))
    sound_enabled = config["sound"]["enabled"] if sound_override is None else sound_override
    audio = AmbientAudio(config["sound"]["volume"], runtime_dir)
    stop_requested = False
    user_dismissed = False

    def stop_handler(_signum: int, _frame: Any) -> None:
        nonlocal stop_requested
        stop_requested = True

    previous_handlers = {}
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP, signal.SIGQUIT):
        previous_handlers[sig] = signal.signal(sig, stop_handler)

    try:
        with TerminalSession(palette["background"]):
            if sound_enabled:
                audio.start()
            started = time.monotonic()
            previous = started
            next_frame = started
            while not stop_requested:
                now = time.monotonic()
                if now - started > 0.35 and select.select([sys.stdin], [], [], 0)[0]:
                    os.read(sys.stdin.fileno(), 4096)
                    user_dismissed = True
                    break
                new_width, new_height = terminal_size()
                scene.resize(new_width, new_height)
                scene.update(now - previous)
                previous = now
                sys.stdout.write(scene.render().ansi())
                sys.stdout.flush()
                next_frame += 1.0 / 24.0
                delay = next_frame - time.monotonic()
                if delay > 0:
                    time.sleep(delay)
                else:
                    next_frame = time.monotonic()
    finally:
        audio.close()
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
    if user_dismissed:
        dismiss_screensaver_windows()
    return 0

def run_audio_test(config: dict[str, Any], seconds: float) -> int:
    """Exercise PipeWire without requiring an interactive terminal."""
    runtime_dir = Path(os.environ.get("XDG_RUNTIME_DIR", f"/tmp/omarcharium-{os.getuid()}"))
    duration = max(1.0, min(60.0, seconds))
    volume = max(55, int(config["sound"]["volume"]))
    audio = AmbientAudio(volume, runtime_dir, diagnostic=True)
    if not audio.start():
        print(f"omarcharium audio test failed: {audio.last_error}", file=sys.stderr)
        return 3
    print(
        f"Omarcharium audio test active at {volume}% for {duration:g}s. "
        "Listen for three rising tones, then water and bubbles.",
        flush=True,
    )
    deadline = time.monotonic() + duration
    try:
        while time.monotonic() < deadline:
            if audio.process and audio.process.poll() is not None:
                print("omarcharium audio test failed: PipeWire stream stopped", file=sys.stderr)
                return 3
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        audio.close()
    print("Omarcharium audio test complete.", flush=True)
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TTE-inspired tropical terminal aquarium")
    parser.add_argument("--config", type=Path, default=CONFIG_PATH, help="configuration JSON path")
    parser.add_argument("--seed", type=int, default=None, help="deterministic scene seed")
    parser.add_argument("--snapshot", action="store_true", help="render one plain-text frame and exit")
    parser.add_argument("--width", type=int, default=100, help="snapshot width")
    parser.add_argument("--height", type=int, default=32, help="snapshot height")
    parser.add_argument("--check-config", action="store_true", help="print the normalised configuration and exit")
    parser.add_argument(
        "--audio-test", type=float, nargs="?", const=8.0, default=None, metavar="SECONDS",
        help="play an audible PipeWire diagnostic without requiring a terminal",
    )
    sound = parser.add_mutually_exclusive_group()
    sound.add_argument("--sound", action="store_true", help="enable ambience for this run")
    sound.add_argument("--no-sound", action="store_true", help="disable ambience for this run")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    config = load_config(args.config)
    if args.check_config:
        print(json.dumps(config, indent=2, sort_keys=True))
        return 0
    if args.audio_test is not None:
        return run_audio_test(config, args.audio_test)
    seed = args.seed if args.seed is not None else (os.getpid() ^ time.time_ns()) & 0xFFFFFFFF
    if args.snapshot:
        scene = OceanScene(args.width, args.height, config, seed)
        scene.update(1.0 / 24.0)
        print(scene.render().plain())
        return 0
    sound_override = True if args.sound else False if args.no_sound else None
    try:
        return run_interactive(config, seed, sound_override)
    except RuntimeError as error:
        print(f"omarcharium: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
