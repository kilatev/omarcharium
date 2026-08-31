# Configuration reference

The tray control room is the supported configuration surface. It writes `~/.config/omarcharium/config.json` atomically and applies changes to the next immersion.

## Species

Each species has an independent exact population. Setting a species to zero removes it from the habitat.

| Key | Display name | Maximum | Motion character |
|---|---|---:|---|
| `neon_tetra` | Neon tetra | 20 | Fast schooling streaks |
| `clownfish` | Clownfish | 12 | Warm mid-water reef dancers |
| `angelfish` | Angelfish | 10 | Tall, slow silhouettes |
| `discus` | Discus | 10 | Round chromatic drifters |
| `butterflyfish` | Butterflyfish | 10 | Sharp reef geometry |
| `royal_tang` | Royal tang | 12 | Fast cobalt current runners |
| `betta` | Betta | 6 | Solitary trailing fins |
| `puffer` | Puffer | 10 | Slow buoyant sentries |

## Water column

| Setting | Range | Default | Effect |
|---|---:|---:|---|
| Palette | Lagoon, Midnight, Coral, Phosphor | Lagoon | Complete habitat color system |
| Bubble density | 0–100% | 55% | Number of animated bubble entities |
| Current | 0.35–1.8× | 1.0× | Horizontal fish velocity multiplier |
| Telemetry | On/off | On | Header, biomass, palette, and dismissal footer |

## Ambience

Audio is off by default. When enabled, `volume` controls the generated stream from 0–100%. Only one monitor instance emits audio.

Use **Test 8s** in the control room, or run:

```sh
python3 scripts/aquarium.py --audio-test 8
```

The test does not require a TTY. It plays three rising tones and then the same generated water texture used by the screensaver. Audio follows the current PipeWire default sink.

## Idle integration

**Automatic Idle Immersion** uses `idle.screensaver` from `~/.config/omarchy/shell.json`. Locking remains under Omarchy's first-party idle service and continues to use `idle.lock`.

Disable automatic immersion to keep tray and manual launching while restoring the stock visualizer behavior.

## Surface control

**Exit on pointer movement** defaults to on, matching the original screensaver behavior. Disable it to move the pointer without surfacing; mouse clicks and keyboard input always dismiss every monitor instance.

## JSON example

```json
{
  "schemaVersion": 1,
  "species": {
    "neon_tetra": 10,
    "clownfish": 4,
    "angelfish": 3,
    "discus": 3,
    "butterflyfish": 2,
    "royal_tang": 3,
    "betta": 1,
    "puffer": 2
  },
  "art": {
    "palette": "lagoon",
    "bubbleDensity": 55,
    "current": 1.0,
    "showTelemetry": true
  },
  "sound": {
    "enabled": false,
    "volume": 24
  },
  "integration": {
    "idleEnabled": true,
    "exitOnPointerMotion": true
  }
}
```

Unknown keys are ignored. Missing and malformed values fall back to packaged defaults; numeric values are clamped to supported ranges.

## Command-line diagnostics

```sh
# Print the effective normalized configuration
python3 scripts/aquarium.py --check-config

# Produce deterministic plain-text art without opening a terminal surface
python3 scripts/aquarium.py --snapshot --width 120 --height 36 --seed 7

# Force or suppress audio for an interactive terminal run
python3 scripts/aquarium.py --sound
python3 scripts/aquarium.py --no-sound
```

The last two commands require a real terminal. Use `--audio-test` for headless audio diagnostics.
