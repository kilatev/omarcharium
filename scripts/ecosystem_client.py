"""Small command-line client for the private ecosystem service protocol."""

from __future__ import annotations

import argparse
import json
import os
import socket
from pathlib import Path
from typing import Any


MAX_RESPONSE_BYTES = 4 * 1024 * 1024


def default_socket() -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime or not os.path.isabs(runtime):
        runtime = f"/tmp/omarcharium-{os.getuid()}"
    return Path(runtime) / "omarcharium" / "ecosystem.sock"


def request(payload: dict[str, Any], path: Path | None = None, timeout: float = 2.0) -> dict[str, Any]:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connection:
        connection.settimeout(timeout)
        connection.connect(str(path or default_socket()))
        connection.sendall((json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8"))
        raw = b""
        while not raw.endswith(b"\n") and len(raw) <= MAX_RESPONSE_BYTES:
            chunk = connection.recv(4096)
            if not chunk:
                break
            raw += chunk
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError("service response exceeds size limit")
    response = json.loads(raw.decode("utf-8"))
    if not isinstance(response, dict):
        raise ValueError("service response must be an object")
    if not response.get("ok", False):
        raise RuntimeError(str(response.get("error", "service request failed")))
    return response


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("snapshot", "reset", "settings", "save"))
    parser.add_argument("--seed", type=int)
    parser.add_argument("--settings", type=json.loads, default={})
    parser.add_argument("--socket", type=Path)
    args = parser.parse_args()
    payload: dict[str, Any] = {"operation": args.operation}
    if args.operation == "reset":
        if args.seed is None:
            parser.error("reset requires --seed")
        payload["seed"] = args.seed
        if args.settings:
            if not isinstance(args.settings, dict):
                parser.error("--settings must decode to an object")
            payload["settings"] = args.settings
    if args.operation == "settings":
        if not isinstance(args.settings, dict):
            parser.error("--settings must decode to an object")
        payload["settings"] = args.settings
    response = request(payload, args.socket)
    print(json.dumps(response, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
