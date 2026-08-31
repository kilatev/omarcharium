# Continuation handoff

Last updated: 2026-08-31 during the `v1.0.4` worktree.

## User requirements

Review all four GitHub issues, implement them in practical ease/dependency order, and for **each completed issue** advance one patch version, commit, push, publish a GitHub release, close the issue, and confirm CI. Keep this file current so another session can resume without reconstructing state.

## Repository state

- Repository: <https://github.com/DailenG/omarcharium>
- Branch: `main`
- Last published commit: `41bdebc` (`v1.0.3`)
- Plugin ID: `dailen.omarcharium`
- Current worktree contains uncommitted `v1.0.4` ASCII-backdrop work.
- Omarchy rule: never modify `/usr/share/omarchy/`; reading it is allowed.

## Completed and published

1. **Issue #1 — optional pointer-motion dismissal**
   - Released as [`v1.0.1`](https://github.com/DailenG/omarcharium/releases/tag/v1.0.1).
   - Commit `917f7eb`; CI passed.
   - Motion can be ignored; click and keyboard dismissal remain unconditional.
2. **Issue #2 — Pelagic Field backdrop and independent effects**
   - Released as [`v1.0.2`](https://github.com/DailenG/omarcharium/releases/tag/v1.0.2).
   - Commit `730b40c`; CI passed.
   - Added Plain/Pelagic sources, intensity, and independent source/effects layers.
3. **Issue #3 — user-selected image backdrop**
   - Released as [`v1.0.3`](https://github.com/DailenG/omarcharium/releases/tag/v1.0.3).
   - Commit `41bdebc`; CI passed.
   - Omarchy native image picker, preview, fit, dimming, validation, ImageMagick cache, Ghostty/Kitty negative-z raster placement, and explicit Alacritty/Foot plain fallback.
   - Live Ghostty raster rendering and native picker selection were visually verified.

## In progress: Issue #4 / `v1.0.4`

Target: ASCII-fy the selected local image while preserving optional pelagic effects.

Already edited but **not yet committed**:

- `defaults.json`
  - Added `backdrop.ascii`: `detail`, `glyphMode`, `colorMode`, `dither`.
- `scripts/aquarium.py`
  - Accepts `backdrop.source = "ascii"`.
  - Added strict ASCII-setting normalization.
  - Added `OceanScene.ascii_backdrop` and ASCII source rendering below effects/habitat/fish/telemetry.
  - Refactored image dimension identification into `RasterBackdrop.identify_dimensions`.
  - Added `AsciiBackdrop` with cell-aspect-aware ImageMagick sampling, deterministic glyph/color conversion, binary cache keyed by source metadata/settings/terminal geometry, bounded dimensions, and cache decoding.
  - Added interactive launch and resize integration.
  - Added `--ascii-preview`; deterministic `--snapshot` now loads ASCII sources.
  - `python3 -m py_compile scripts/aquarium.py` passed after the latest source edits.
- `Config.qml`
  - Added ASCII source chip and live preview process.
  - Added detail, ramp/block glyph, truecolor/palette/monochrome, and dither controls.
  - Pelagic effects remain independently configurable below ASCII controls.
- `CONTINUE.md`
  - This handoff.

A temporary ASCII smoke config was about to be written when the continuity request arrived; that write was skipped and must be retried.

## Exact next actions

1. Write `/tmp/omarcharium-ascii-smoke/omarcharium/config.json` using `preview.png`, source `ascii`, detail 70, ramp, truecolor, dither on, dimming 35, effects on at 35%.
2. Run `python3 scripts/aquarium.py --config <temp-config> --ascii-preview --width 80 --height 24` and inspect output.
3. Add focused tests for:
   - ASCII setting normalization;
   - deterministic RGB-to-cell conversion;
   - glyph/color modes and dithering;
   - corrupt RGB/image input fallback;
   - cache-key invalidation on settings/source metadata/geometry changes;
   - ANSI output size bound.
4. Run full unit tests. Fix failures at the source.
5. Runtime-load `Config.qml` through the existing temporary Quickshell wrapper and check for new `WARN scene` parse messages.
6. Open the live control room, navigate to ASCII controls, and visually inspect the expanded layout and generated preview.
7. Launch the actual ASCII aquarium in Ghostty and inspect/capture the result. Verify effects on top.
8. Update `manifest.json` to `1.0.4`, `CHANGELOG.md`, README, configuration, architecture, and security documentation.
9. Run `bash -n`, `omarchy plugin validate .`, full tests, actual snapshot/smoke, and `git diff --check`.
10. Commit `v1.0.4`, tag/push, publish the GitHub release, close issue #4, and confirm CI success.
11. Run final cross-feature verification, verify releases/issues/Pages, update this file to completed state, commit any final documentation only if needed, and leave the worktree clean.

## Release discipline

Do not combine an unfinished issue with a release. Every patch release must have its behavior exercised before commit and GitHub publication. Do not close issue #4 until `v1.0.4` is live.
