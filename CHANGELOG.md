# Changelog

All notable changes are documented here. This project follows [Semantic Versioning](https://semver.org/).

## [1.0.9] - 2026-08-31

### Security

- Hardened audio and backdrop lock files against symlink traversal with no-follow opens, ownership checks, and private permissions.
- Replaced path-only idle-toggle ownership with matching per-instance markers so a user-replaced toggle is never removed.
- Bounded configuration reads to 256 KiB, terminal allocation to 500 × 200 cells, and derived-image caching to 16 files and 128 MiB.
- Forced ImageMagick to allowlisted decoders and isolated its bounded temporary storage.
- Pinned GitHub Actions to verified full commit SHAs and added a restrictive Content Security Policy to the project site.

### Changed

- Configuration, cache, runtime, and integration-state directories now enforce private user-only permissions.
- Image selection rejects invalid, non-local, multiline, and stalled picker results.

## [1.0.8] - 2026-08-31

### Added

- **Reef density** control (`art.reefDensity`, 0–100%) that proportionately scales coral structures (height, branch tiers, staghorns, table corals, anemones) and kelp columns across the seabed.
- Renamed control-room setting to **Reef Density** with full backward compatibility for previous configuration keys.

## [1.0.7] - 2026-08-31

### Added

- **Vegetation volume** control (`art.vegetationVolume`, 0–100%) scaling the height, density, and variety of kelp stalks and marine flora.
- Water column control-room slider with live adjustments.

## [1.0.6] - 2026-08-31

### Removed

- Removed experimental image-to-ASCII backdrop in favor of high-fidelity native hardware-accelerated raster backdrops (Ghostty/Kitty) and procedural Pelagic Field layers.

### Fixed

- Restored seamless backdrop selection in the control room without unwanted source switching.

## [1.0.5] - 2026-08-31

### Added

- Native right-click tray menu for opening the control room, starting an immersion, or reporting a bug.

### Changed

- Renamed the local information overlay to **Status Display** in user-facing copy to avoid implying collection or transmission.

## [1.0.4] - 2026-08-31

### Added

- ASCII-fied local image backdrop source with glyph, colour, and dither controls.
- Deterministic cell-aspect ImageMagick sampling, binary cache keyed by settings and geometry, and bounded ANSI output.
- Independent pelagic effects layer atop ASCII backdrops.
- `--ascii-preview` and deterministic `--snapshot` integration.

## [1.0.3] - 2026-08-31

### Added

- Omarchy-native image picker and control-room preview for custom aquarium backdrops.
- Bounded ImageMagick preprocessing with fit, dimming, atomic caching, and invalid-file fallback.
- Native negative-z raster placement in Ghostty and Kitty with an explicit plain-depth fallback elsewhere.

## [1.0.2] - 2026-08-31

### Added

- Optional palette-aware Pelagic Field background source.
- Independently configurable animated current, scanline, and depth-particle effects.
- Explicit background, effects, habitat, fish, and status-display layer model.

## [1.0.1] - 2026-08-31

### Added

- Optional pointer-motion dismissal while preserving click and keyboard exit behavior.
- Buffered SGR mouse-event classification with safe terminal-mode restoration.

## [1.0.0] - 2026-08-31

### Added

- TTE-inspired ANSI aquarium with eight independently configurable tropical species.
- Animated caustics, motes, bubbles, kelp, coral, sand, and depth-aware fish rendering.
- Lagoon, Midnight, Coral, and Phosphor palettes.
- Multi-monitor Omarchy launcher for Alacritty, Foot, Ghostty, and Kitty.
- Tray-hosted Quickshell control room with pointer and keyboard navigation.
- Inhibitor-aware idle activation that preserves Omarchy lock timing.
- Conservative ownership lifecycle for the stock-screensaver toggle.
- Optional single-leader procedural PipeWire ambience.
- Headless audio diagnostic with explicit raw PCM negotiation.
- Deterministic renderer snapshots, configuration normalization, and behavioral tests.
- Marketplace manifest, preview artwork, actual screenshots, contributor guide, security policy, and CI validation.

[1.0.9]: https://github.com/DailenG/omarcharium/releases/tag/v1.0.9
[1.0.8]: https://github.com/DailenG/omarcharium/releases/tag/v1.0.8
[1.0.7]: https://github.com/DailenG/omarcharium/releases/tag/v1.0.7
[1.0.6]: https://github.com/DailenG/omarcharium/releases/tag/v1.0.6
[1.0.5]: https://github.com/DailenG/omarcharium/releases/tag/v1.0.5
[1.0.4]: https://github.com/DailenG/omarcharium/releases/tag/v1.0.4
[1.0.3]: https://github.com/DailenG/omarcharium/releases/tag/v1.0.3
[1.0.2]: https://github.com/DailenG/omarcharium/releases/tag/v1.0.2
[1.0.1]: https://github.com/DailenG/omarcharium/releases/tag/v1.0.1
[1.0.0]: https://github.com/DailenG/omarcharium/releases/tag/v1.0.0
