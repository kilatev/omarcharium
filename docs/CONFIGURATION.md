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

During terminal immersion, the status display also shows read-only evolution
telemetry from the shared ecosystem service: biological elapsed time, current
population, species present, maximum generation, and mutation events. Press
`I` or `i` to open the full-screen statistics view. The view includes per-species
population, births, deaths, resources, and food/predator/mutation settings.
Statistics polling occurs approximately once per second and does not pause or
accelerate the simulation. If the service is unavailable, the aquarium remains
usable and shows `EVO OFFLINE`; all other keyboard input still dismisses the
terminal immersion.

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
| `mutationRate` | 0–1.0 | 0.20 | Probability of bounded trait mutation at each birth |
| `predatorPressure` | 0–2.0× | 1.0× | Predator feeding pressure |
| `diagnosticAccelerated` | On/off | Off | Enables intentionally accelerated simulation diagnostics |

Changing a control updates configuration only. **Reset ecosystem** is an explicit
service operation: it creates a new valid biological model from `startingSeed`
while preserving visual and audio configuration. The service remains the only
writer of biological state.

Normal simulation time advances in one biological minute per wall-clock minute.
The arcade defaults make organisms mature after about one hour and allow another
birth after roughly thirty biological minutes. Mutation is still probabilistic:
the 20% rate is evaluated independently for each inherited trait at birth, so no
fixed wall-clock interval guarantees a mutation. Diagnostic acceleration is
intentionally available for verification and demonstrations, not as the normal
screensaver setting.

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
    "mutationRate": 0.20,
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

## Autonomous food drops

`ecosystem.foodDrops` defaults to `true`. The control room's **Automatic food
drops** toggle enables small portions falling from above without keyboard or
pointer interaction. After an initial 90 active seconds, opportunities recur at
seeded intervals of 60–180 seconds. An occupied scene or quiet interval skips an
opportunity; skipped portions are never queued. Simulation speed scales these
intervals together with movement.

A portion contains 4–10 finite crumbs, sinking for up to 30 seconds. Hungry
herbivores approach reachable crumbs and compete for them; each crumb transfers
only its remaining energy. Unconsumed crumbs expire without regenerating or
accumulating on the bottom. Disabling drops prevents new portions while existing
crumbs can still be eaten or expire. `foodAbundance` continues to control algae
regeneration independently. Saves preserve in-flight food and the next timer.

## Predators and rare hunts

Two artistic reef species are available: `reef_stalker` (a broad-bodied shelter
ambusher, default 1) and `reef_hunter` (a slender patrol fish, default 0), each
capped at 3. Existing saves retain their actual populations. Species controls
select starting counts; **Reset world to configured populations** explicitly
replaces the world and restores default ecosystem settings. No new species is
silently inserted into a loaded checkpoint.

All predators, including the original four species, now require an active hunt
and physical contact to eat fish. Energy below 0.85 and completed recovery make
a predator eligible; only one scene runs at a time. Preparation lasts 0.7 active
seconds, followed by a 2–5 second ambush or 3–8 second pursuit. Every attempt ends
in 120–240 seconds of recovery (180–300 for the patrol species). A satiated
predator waits longer until hungry. Prey avoid nearby predators, burst away
during pursuit, and regroup with their species afterward.

`predatorPressure: 0` prevents hunts and cancels an active pursuit. Positive
pressure scales the opportunity interval (45–90 active seconds at 1.0), while
individual cooldowns, hunger and scene quiet periods still apply. A successful
kill transfers at most 0.25 energy and never more than 60% of the prey's remaining
energy. Hunt attempts and successes are exposed in shared telemetry. Save/load
preserves preparation, targets and recovery; missing targets abort the hunt.

## Personalities and shrimp

Individual behavior is derived from inherited traits. High aggression produces
brief territorial nudges, high diet preference produces curious exploration, and
other fish tend toward shy shelter-aware cruising. Threat avoidance and active
hunting always take priority, and each episode returns to ordinary motion.

`ecosystem.shrimpEnabled` defaults to `true`. At seeded intervals of 180–360
active seconds, one temporary shrimp may appear near the bottom when the scene is
quiet. It flees toward the reef when a predator approaches, can be eaten through
the same contact rules, and expires after 45 seconds. A catch transfers 0.08 energy
and increments `shrimpCatches`; it is separate from fish death statistics. There
is no shrimp reproduction. Disabling shrimp prevents new appearances while an
existing shrimp can still flee, be caught, or expire. Checkpoints preserve the
active shrimp and timer.

## Currents and event controls

`ecosystem.currentsEnabled` and `ecosystem.huntsEnabled` default to `true` and
are independent of visual `art.current`. A current pulse lasts 20 active seconds,
ramp ups and down, and then observes a seeded 120–300 second interval. It shares
the single major-scene slot with food, hunts and shrimp, so quiet periods prevent
overlapping scenes. Simulation speed scales all biological timers; disabling an
event skips future opportunities without queuing them. In-flight entities finish
or abort through their normal bounded cleanup paths.
