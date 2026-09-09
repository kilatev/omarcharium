#!/usr/bin/env python3
"""Expose the installed Omarcharium renderer as request-driven JSON frames.

Only dimensions enter this process; authentication remains in Lock Explorer.
EOF (the lock surface disappearing) terminates the renderer.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import time


def main():
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    source = config_home / "omarchy/plugins/dailen.omarcharium/scripts/aquarium.py"
    spec = importlib.util.spec_from_file_location("omarcharium_renderer", source)
    aquarium = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = aquarium
    spec.loader.exec_module(aquarium)
    config = aquarium.load_config(aquarium.CONFIG_PATH)
    scene = aquarium.OceanScene(120, 40, config, time.time_ns() & 0xFFFFFFFF)
    previous = time.monotonic()
    for line in sys.stdin:
        request = json.loads(line)
        width = max(40, min(240, int(request[0])))
        height = max(16, min(100, int(request[1])))
        scene.resize(width, height)
        now = time.monotonic()
        scene.update(min(0.1, now - previous))
        previous = now
        frame = scene.render()
        if config["art"]["showTelemetry"]:
            # The terminal's dismissal hint does not apply to a secure lock.
            frame.chars[-1] = [" "] * frame.width
            hint = "[ enter password to unlock ]"
            frame.text(max(0, (frame.width - len(hint)) // 2), frame.height - 1,
                       hint, scene.palette["dim"])
        # Consecutive cells of one colour become a single canvas draw call.
        runs = []
        for y, row in enumerate(frame.chars):
            x = 0
            while x < frame.width:
                if row[x] == " ":
                    x += 1
                    continue
                start = x
                colour = frame.colours[y][x] or (255, 255, 255)
                x += 1
                while x < frame.width and frame.colours[y][x] == colour:
                    x += 1
                runs.append([start, y, "#%02x%02x%02x" % colour, "".join(row[start:x])])
        print(json.dumps({"width": frame.width, "height": frame.height,
                          "background": "#%02x%02x%02x" % scene.palette["background"],
                          "backdrop": config["backdrop"], "runs": runs},
                         separators=(",", ":")), flush=True)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
