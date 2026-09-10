#!/usr/bin/env python3
"""Turn shared ecosystem snapshots into lock-surface render frames.

This process is a read-only renderer adapter. It never advances the model,
accepts lock input, or reads the checkpoint file.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys
from typing import Any, Callable


def _add_module_paths() -> None:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    candidates = (
        Path(__file__).resolve().parents[2],
        config_home / "omarchy/plugins/dailen.omarcharium/scripts",
    )
    for candidate in candidates:
        if candidate.is_dir() and str(candidate) not in sys.path:
            sys.path.insert(0, str(candidate))


_add_module_paths()
try:
    from scripts.ecosystem_client import request
    from scripts.ecosystem_model import model_from_json
    from scripts.ecosystem_view import Viewport, view
except ModuleNotFoundError:
    from ecosystem_client import request
    from ecosystem_model import model_from_json
    from ecosystem_view import Viewport, view


def _load_backdrop() -> dict[str, Any]:
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    try:
        raw = json.loads((config_home / "omarcharium/config.json").read_text(encoding="utf-8"))
        backdrop = raw.get("backdrop", {}) if isinstance(raw, dict) else {}
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        backdrop = {}
    if not isinstance(backdrop, dict):
        backdrop = {}
    source = backdrop.get("source") if backdrop.get("source") in {"plain", "pelagic", "image"} else "plain"
    fit_mode = backdrop.get("fitMode") if backdrop.get("fitMode") in {"cover", "contain", "center"} else "cover"
    image_path = backdrop.get("imagePath") if isinstance(backdrop.get("imagePath"), str) else ""
    dimming = backdrop.get("dimming", 45)
    if isinstance(dimming, bool) or not isinstance(dimming, (int, float)):
        dimming = 45
    return {"source": source, "imagePath": image_path, "fitMode": fit_mode,
            "dimming": max(0, min(90, int(dimming)))}


BACKDROP = _load_backdrop()


def _dimensions(payload: Any) -> tuple[int, int]:
    if not isinstance(payload, list) or len(payload) != 2:
        raise ValueError("frame dimensions must be a two-item array")
    width, height = payload
    if isinstance(width, bool) or isinstance(height, bool):
        raise ValueError("frame dimensions must be integers")
    return max(40, min(240, int(width))), max(16, min(100, int(height)))


def render_snapshot(payload: Any, snapshot_request: Callable[[], dict[str, Any]] | None = None) -> dict[str, Any]:
    """Build one lock frame from a service snapshot, without simulation work."""

    width, height = _dimensions(payload)
    response = (snapshot_request or (lambda: request({"operation": "snapshot"})))()
    snapshot = response.get("snapshot") if isinstance(response, dict) else None
    model = model_from_json(snapshot)
    frame = view(model, Viewport(width, height))
    frame["background"] = "#061219"
    frame["backdrop"] = BACKDROP.copy()
    frame["error"] = ""
    return frame


def fallback_frame(payload: Any, error: str) -> dict[str, Any]:
    width, height = _dimensions(payload)
    return {
        "schemaVersion": 1, "width": width, "height": height, "tick": 0,
        "resources": [], "organisms": [],
        "telemetry": {"population": 0, "resourceCount": 0, "generation": 0},
        "background": "#061219", "backdrop": BACKDROP.copy(), "error": error[:160],
    }


def main() -> None:
    last_frame = None
    for line in sys.stdin:
        try:
            payload = json.loads(line)
            frame = render_snapshot(payload, lambda: request({"operation": "snapshot"}))
            last_frame = frame
        except (OSError, ValueError, TypeError, RuntimeError, json.JSONDecodeError) as error:
            try:
                frame = fallback_frame(json.loads(line), str(error))
                if last_frame is not None and (frame["width"], frame["height"]) == (last_frame["width"], last_frame["height"]):
                    frame = dict(last_frame, error=str(error)[:160])
            except (ValueError, TypeError, json.JSONDecodeError):
                continue
        print(json.dumps(frame, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
