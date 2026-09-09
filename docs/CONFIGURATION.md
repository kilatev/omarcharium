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
| Status display | On/off | On | Header, biomass, palette, and dismissal footer; rendered locally |
| Reef density | 0–100% | 50% | Height, branch tiers, and density of coral formations, kelp stalks, and sea flora |

The JSON key remains `showTelemetry` for configuration compatibility. It only toggles this local status display; Omarcharium does not collect or transmit usage data.

## Backdrop layers

| Setting | Range | Default | Effect |
|---|---:|---:|---|
| Source | Plain Depth, Pelagic Field, Custom Image | Plain Depth | Base layer behind the habitat |
| Image path | Local JPEG, PNG, GIF, BMP, or WebP | Empty | Selected image; only the first animated frame is used |
| Image fit | Cover, contain, center | Cover | Preprocessing crop and placement behavior |
| Image dimming | 0–90% | 45% | Reduces image brightness beneath fish and the status display |
| Pelagic effects | On/off | Off | Animated current bands, scanlines, and depth particles |
| Effect intensity | 0–100% | 55% | Density of the optional effects layer |

The background source and effects are independent. Pelagic effects can run over Plain Depth, Pelagic Field, or a custom image.

**Custom Image** uses Omarchy's fullscreen image picker. The renderer accepts local files only, limits inputs to 32 MiB and 24 megapixels, and forces ImageMagick to the decoder allowlisted for the selected suffix. Preprocessing runs with bounded memory, map, disk, and wall-clock resources in a private temporary directory. Derived mode-`0600` PNGs are cached under `~/.cache/omarcharium/`, with pruning at 16 files or 128 MiB. Ghostty and Kitty receive the cached PNG through the Kitty graphics protocol at negative z-order. Alacritty and Foot display a clear plain-depth fallback while preserving habitat, fish, the status display, and optional effects.

## Ambience

Audio is off by default. When enabled, `volume` controls the generated stream from 0–100%. Only one monitor instance emits audio. Water flow and bubble chirps can be toggled independently.

| Setting | Range | Default | Effect |
|---|---:|---:|---|
| Master audio | On/off | Off | Synthesised PipeWire ambience stream |
| Volume | 0–100% | 24% | Output stream volume |
| Water flow | On/off | On | Continuous filtered low-frequency water movement |
| Bubble chirps | On/off | On | Sparse rising-frequency bubble envelopes |

Use **Test 8s** in the control room, or run:

```sh
python3 scripts/aquarium.py --audio-test 8
```

The test does not require a TTY. It plays three rising tones and then the configured water texture and/or bubble chirps used by the screensaver. Audio follows the current PipeWire default sink.
## Idle integration

**Automatic Idle Immersion** uses `idle.screensaver` from `~/.config/omarchy/shell.json`. Locking remains under Omarchy's first-party idle service and continues to use `idle.lock`.

Disable automatic immersion to keep tray and manual launching while restoring the stock visualizer behavior.

## Ecosystem controls

The `ecosystem` section contains simulation-only controls. Values are normalized
before persistence and do not alter art, backdrop, sound, or integration settings.

| Setting | Range | Default | Meaning |
|---|---:|---:|---|
| `enabled` | On/off | On | Whether biological simulation updates run |
| `simulationSpeed` | 0.1–4.0× | 1.0× | Fixed-tick rate multiplier |
| `startingSeed` | signed 32-bit integer | 7 | Seed used by an explicit ecosystem reset |
| `foodAbundance` | 0–2.0× | 1.0× | Resource regeneration abundance |
| `mutationRate` | 0–1.0 | 0.08 | Probability of bounded trait mutation |
| `predatorPressure` | 0–2.0× | 1.0× | Predator feeding pressure |
| `diagnosticAccelerated` | On/off | Off | Enables intentionally accelerated simulation diagnostics |

Changing a control updates configuration only. **Reset ecosystem** is an explicit
service operation: it creates a new valid biological model from `startingSeed`
while preserving visual and audio configuration. The service remains the only
writer of biological state.

Normal simulation time advances in one biological minute per wall-clock minute.
This keeps maturity and reproduction on an hours-scale cadence. Diagnostic
acceleration is intentionally available for verification and demonstrations, not
as the normal screensaver setting.

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
    "showTelemetry": true,
    "reefDensity": 50
  },
  "backdrop": {
    "source": "image",
    "imagePath": "/home/user/Pictures/reef.png",
    "fitMode": "cover",
    "dimming": 35,
    "effectsEnabled": true,
    "effectIntensity": 35
  },
  "sound": {
    "enabled": false,
    "volume": 24,
    "water": true,
    "bubbles": true
  },
  "integration": {
    "idleEnabled": true,
    "exitOnPointerMotion": true
  },
  "ecosystem": {
    "enabled": true,
    "simulationSpeed": 1.0,
    "startingSeed": 7,
    "foodAbundance": 1.0,
    "mutationRate": 0.08,
    "predatorPressure": 1.0,
    "diagnosticAccelerated": false
  }
}
```

Unknown keys are ignored. Missing and malformed values fall back to packaged defaults; numeric values are clamped to supported ranges. Renderer configuration input is capped at 256 KiB, and requested render dimensions are clamped to 40–500 columns and 16–200 rows.

## Command-line diagnostics

```sh
# Produce deterministic plain-text art without opening a terminal surface
python3 scripts/aquarium.py --snapshot --width 120 --height 36 --seed 7

# Validate and cache the configured custom image
python3 scripts/aquarium.py --check-backdrop

# Force or suppress audio for an interactive terminal run
python3 scripts/aquarium.py --sound
python3 scripts/aquarium.py --no-sound
```

The last two commands require a real terminal. Use `--audio-test` for headless audio diagnostics.
