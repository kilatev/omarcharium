# Security policy

## Supported version

Security fixes target the latest tagged release and the `main` branch.

## Reporting a vulnerability

Do not open a public issue for a vulnerability. Use GitHub's **Security → Report a vulnerability** flow for this repository, or privately contact the maintainer through the GitHub profile at <https://github.com/DailenG>.

Include:

- affected version and Omarchy version;
- reproduction steps;
- impact and required local permissions;
- relevant QML, Python, or shell paths;
- a proposed mitigation, if known.

You should receive an acknowledgment within seven days. Coordinated disclosure is preferred.

## Trust boundary

Omarcharium is an unsandboxed Omarchy shell plugin and runs with the current user's permissions. Its intended boundaries are deliberately narrow:

- no `sudo`, `pkexec`, package-manager, or installer execution;
- no network access or remote assets;
- no secrets, credentials, or telemetry collection;
- no writes to `/usr/share/omarchy/`;
- configuration only under `~/.config/omarcharium/`;
- selected backdrop images are local read-only inputs, limited to 32 MiB and 24 megapixels;
- derived, dimmed backdrop PNGs only under `~/.cache/omarcharium/`;
- owned integration state only under `~/.local/state/omarcharium/`;
- a temporary audio lock only under `$XDG_RUNTIME_DIR`;
- external processes limited to documented Omarchy, Hyprland, terminal, PipeWire, ImageMagick, and POSIX tools.

The idle helper preserves a pre-existing user-owned `screensaver-off` toggle and removes only a toggle for which it recorded ownership.

Backdrop paths are passed as direct process arguments, never interpolated into shell command strings. Remote URLs and unsupported file types are rejected. ImageMagick runs with explicit memory, map, disk, dimension, and wall-clock bounds.
