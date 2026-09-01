# Omarcharium development notes

Repository-specific guidance for future development sessions. Keep machine- and user-specific information out of this file.

## Plugin lifecycle

- The repository is the source of truth. A user installation lives at `$HOME/.config/omarchy/plugins/dailen.omarcharium/`.
- This workstation's installed copy is not a Git checkout, so `omarchy plugin update dailen.omarcharium` cannot update it. Synchronize validated repository files into the installation, then run `omarchy restart shell`.
- `omarchy-shell shell rescanPlugins` refreshes discovery, but a long-lived service or already-loaded overlay can retain old QML. Use `omarchy restart shell` after changing `Service.qml`, `Config.qml`, or packaged defaults.
- Confirm discovery with `omarchy plugin catalog`; `sourceDir` must point at the user-owned plugin directory.
- Never modify `/usr/share/omarchy/`.

## Tray integration

- `Qt.labs.platform` tray menus must be assigned through `Platform.SystemTrayIcon.menu`:

  ```qml
  Platform.SystemTrayIcon {
    menu: Platform.Menu { /* items */ }
  }
  ```

- Do not create a bare child `Platform.Menu` and call `popup()` from `SystemTrayIcon.Context`; the status-notifier backend owns context-menu activation.
- Keep the menu short. Detailed aquarium controls belong in `Config.qml`.

## Control room

- `Config.qml` is an overlay loaded by the Omarchy shell. If Configure shows stale controls while repository and installed files match, restart the shell to discard the loaded QML component.
- Configuration is stored at `$HOME/.config/omarcharium/config.json` and normalized independently in QML and Python. Update both normalizers when changing the public schema.
- QML mutations of nested `var` values must assign fresh objects so change notifications fire.

## Renderer and backdrops

- `scripts/aquarium.py` owns animation, input, image conversion, and audio. The shell only launches it.
- Custom raster images are validated and converted once with bounded ImageMagick resources. Ghostty and Kitty use negative-z Kitty graphics placement; other terminals use the explicit plain fallback.
- Preserve the established render order: source, optional pelagic effects, water/habitat, fish, status display, notices.

## Audio

- One renderer wins the private no-follow `$XDG_RUNTIME_DIR/omarcharium/audio.lock` and streams raw signed 16-bit stereo PCM at 24 kHz to `pw-cat`; the private cache is the fallback when no absolute runtime directory exists.
- `--audio-test` intentionally raises diagnostic volume to at least 55%; interactive ambience uses the configured volume. A successful diagnostic does not prove that a low interactive volume is audible.
- Interactive mode requires a real TTY.

## Verification

Run the checks that cover the changed surface:

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/aquarium.py
bash -n scripts/launch-aquarium scripts/idle-integration scripts/select-backdrop
omarchy plugin validate .
git diff --check
```

For QML changes, load the actual plugin through Omarchy, inspect shell logs for QML errors, and exercise the affected tray or overlay interaction. For renderer changes, run the actual aquarium in a supported terminal.

## Releases

- One completed issue per patch release.
- Update `manifest.json`, `CHANGELOG.md`, user documentation, and relevant screenshots before tagging.
- Commit, tag, push, create the GitHub release, close the issue with the release link, and require CI success.
- `CONTINUE.md` is a local handoff and is intentionally ignored; do not commit it.
