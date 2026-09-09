# Lock Screen Selector

An Omarchy shell plugin with the theme selector's carousel layout, live lock
screen previews, search, and click-to-apply selection.

Open **Super + Space → Style → Lock Screen**, or run:

```sh
omarchy-shell shell summon vetalik.lock-selector '{}'
```

- Click any preview to apply that design and close.
- Left/Right, Tab, or the mouse wheel browse without changing your lock screen.
- Enter applies the highlighted design.
- Type a name to search. Escape clears the search, then closes the selector.
- A checkmark identifies the currently applied design.

Requires `io.github.sirjul1337.lock-explorer`. Uses its current design registry,
including custom designs such as Omarcharium, and its existing `setDesign`
method. Authentication is handled entirely by Lock Screen Explorer.

The UI is adapted from Omarchy's `shell/plugins/image-picker/ImagePicker.qml`.
Only nearby previews are instantiated; video playback and Omarcharium rendering
run for the highlighted preview. Closing unloads the plugin and its previews.

Installed at `~/.config/omarchy/plugins/vetalik.lock-selector/`.

Validate:

```sh
omarchy plugin validate ~/.config/omarchy/plugins/vetalik.lock-selector
```

Remove with `omarchy plugin remove vetalik.lock-selector`, then remove the
`style.lockscreen` entry from `~/.config/omarchy/extensions/omarchy-menu.jsonc`
or change its action back to `omarchy-shell lock explore`.
