# Omarcharium lock-screen integration

Runs the installed Omarcharium `OceanScene` simulation and renderer inside a
Lock Screen Explorer custom design. This is live rendering, not a recording.
The existing DesignBase and PasswordField retain authentication and session-lock
handling. The Python subprocess receives only canvas dimensions, never input.

Installed files:

- `~/.config/omarchy/lock-designs/Omarcharium.qml`
- `~/.config/omarchy/lock-designs/omarcharium/bridge.py`

Select: `omarchy-shell lock setDesign my-omarcharium`

Restore previous design: `omarchy-shell lock setDesign rain`

Fish, palette, water, and backdrop settings are read from Omarcharium's existing
configuration when the lock surface opens. Animation pauses when the lock host
blanks the display and terminates when the surface closes. Frames are requested
at up to 24 FPS with only one request outstanding. Each monitor has its own
renderer. Password authentication and display blanking timings are unchanged.

This adapter uses Omarcharium's internal Python API, so an upstream change to
that API may require updating the bridge. Audio is not started by this adapter.
Renderer failure leaves the password field available against a plain background.
