# Omarcharium lock-screen integration

Renders the shared Omarcharium ecosystem service snapshot inside a Lock Screen
Explorer custom design. This is live rendering, not a recording.
The existing DesignBase and PasswordField retain authentication and session-lock
handling. The Python subprocess receives only canvas dimensions, never input.

Installed files:

- `~/.config/omarchy/lock-designs/Omarcharium.qml`
- `~/.config/omarchy/lock-designs/FrameGeometry.js` (copy beside the QML design)
- `~/.config/omarchy/lock-designs/omarcharium/bridge.py`

Select: `omarchy-shell lock setDesign my-omarcharium`

Restore previous design: `omarchy-shell lock setDesign rain`

All monitors request read-only snapshots from the one service-owned world;
none starts a simulation or reads the checkpoint file. Animation pauses when
the lock host blanks the display and terminates when the surface closes. Frames
are requested at up to 10 FPS with only one request outstanding.
Password authentication and display blanking timings are unchanged.

This adapter uses the private local snapshot protocol and the pure view API.
Audio is not started by this adapter. Service failure holds the last good frame
at the current dimensions; before the first frame it shows a plain background.
The password field remains available.
