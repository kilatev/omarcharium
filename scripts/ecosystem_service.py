"""Authoritative in-memory ecosystem service and private snapshot protocol.

The terminal renderer is a client of this module.  It never owns biological
time or reads the checkpoint directly; only ``EcosystemService`` updates and
persists the model.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import signal
import socketserver
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

try:
    from scripts.ecosystem_checkpoint import CheckpointScheduler, CheckpointStore
    from scripts.ecosystem_model import Model, Reset, Tick, initial_model, model_from_json, model_to_json, update
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from ecosystem_checkpoint import CheckpointScheduler, CheckpointStore
    from ecosystem_model import Model, Reset, Tick, initial_model, model_from_json, model_to_json, update
try:
    from scripts.ecosystem_config import model_settings, normalise_ecosystem_config
except ModuleNotFoundError:  # Direct execution from the scripts directory.
    from ecosystem_config import model_settings, normalise_ecosystem_config


MAX_REQUEST_BYTES = 64 * 1024
DEFAULT_TICK_INTERVAL = 60.0


class ServiceProtocolError(ValueError):
    """Raised for a malformed or unsupported public service request."""


class EcosystemService:
    """Own one model and expose deterministic operations around the pure core."""

    def __init__(
        self,
        store: CheckpointStore[Model],
        *,
        seed: int = 7,
        settings: Mapping[str, Any] | None = None,
        tick_interval: float = DEFAULT_TICK_INTERVAL,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if tick_interval <= 0:
            raise ValueError("tick_interval must be positive")
        self.store = store
        self.scheduler = CheckpointScheduler(store)
        self.tick_interval = float(tick_interval)
        self.clock = clock
        self.simulation_enabled = True
        self.simulation_speed = 1.0
        self.diagnostic_accelerated = False
        self.model = store.load()
        if not isinstance(self.model, Model):
            self.model = initial_model(seed, settings)
        self._last_tick_at: float | None = None
        self._lock = threading.RLock()

    def start(self, now: float | None = None) -> None:
        """Start biological time without advancing the model immediately."""

        with self._lock:
            self._last_tick_at = self.clock() if now is None else float(now)

    def advance(self, now: float | None = None) -> int:
        """Apply elapsed fixed-size ticks and return the number of ticks applied."""

        with self._lock:
            current = self.clock() if now is None else float(now)
            if self._last_tick_at is None:
                self._last_tick_at = current
                return 0
            if not self.simulation_enabled:
                self._last_tick_at = current
                return 0
            elapsed = current - self._last_tick_at
            multiplier = self.simulation_speed * (10.0 if self.diagnostic_accelerated else 1.0)
            effective_interval = self.tick_interval / multiplier
            if elapsed < effective_interval:
                return 0
            count = int(elapsed // effective_interval)
            for _ in range(count):
                self.model = update(self.model, Tick(1.0))
                self.scheduler.mark_dirty()
            self._last_tick_at += count * effective_interval
            self.scheduler.maybe_checkpoint(self.model, current)
            return count

    def snapshot(self) -> dict[str, Any]:
        """Return a fresh read-only JSON snapshot from memory."""

        with self._lock:
            return model_to_json(self.model)

    def reset(self, seed: int, starting_population: Mapping[str, int] | None = None) -> dict[str, Any]:
        with self._lock:
            self.model = update(self.model, Reset(seed, starting_population))
            self.scheduler.mark_dirty()
            self.scheduler.maybe_checkpoint(self.model, self.clock(), force=True)
            return self.snapshot()

    def set_simulation_settings(self, settings: Mapping[str, Any]) -> dict[str, Any]:
        """Update simulation-only settings and force a durable checkpoint."""

        if not isinstance(settings, Mapping):
            raise ServiceProtocolError("settings must be an object")
        with self._lock:
            merged = dict(self.model.settings)
            biological = {
                key: settings[key] for key in ("food_abundance", "mutation_rate", "predator_pressure")
                if key in settings
            }
            merged.update(biological)
            if "enabled" in settings:
                self.simulation_enabled = settings["enabled"] is True
            if "simulation_speed" in settings:
                speed = float(settings["simulation_speed"])
                if not math.isfinite(speed) or speed <= 0:
                    raise ServiceProtocolError("simulation_speed must be positive")
                self.simulation_speed = min(4.0, speed)
            if "diagnostic_accelerated" in settings:
                self.diagnostic_accelerated = settings["diagnostic_accelerated"] is True
            replacement = initial_model(self.model.seed, merged)
            # A settings change must not reset biological state or PRNG history.
            self.model = Model(
                self.model.schema_version, self.model.seed, self.model.tick,
                replacement.settings, self.model.resources, self.model.organisms,
                self.model.random_state,
            )
            self.scheduler.mark_dirty()
            self.scheduler.maybe_checkpoint(self.model, self.clock(), force=True)
            return self.snapshot()

    def save(self) -> bool:
        with self._lock:
            self.scheduler.mark_dirty()
            return self.scheduler.maybe_checkpoint(self.model, self.clock(), force=True)

    def handle_request(self, request: Any) -> dict[str, Any]:
        """Handle one decoded request and return a JSON-compatible response."""

        if not isinstance(request, dict):
            raise ServiceProtocolError("request must be an object")
        operation = request.get("operation")
        if operation == "snapshot":
            return {"ok": True, "snapshot": self.snapshot()}
        if operation == "reset":
            seed = request.get("seed")
            if isinstance(seed, bool) or not isinstance(seed, int):
                raise ServiceProtocolError("seed must be an integer")
            population = request.get("starting_population")
            if population is not None and not isinstance(population, dict):
                raise ServiceProtocolError("starting_population must be an object")
            response = self.reset(seed, population)
            settings = request.get("settings")
            if settings is not None:
                response = self.set_simulation_settings(settings)
            return {"ok": True, "snapshot": response}
        if operation == "settings":
            return {"ok": True, "snapshot": self.set_simulation_settings(request.get("settings", {}))}
        if operation == "save":
            return {"ok": True, "saved": self.save()}
        raise ServiceProtocolError("unsupported operation")


class _RequestHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        service: EcosystemService = self.server.service  # type: ignore[attr-defined]
        raw = self.rfile.readline(MAX_REQUEST_BYTES + 1)
        try:
            if len(raw) > MAX_REQUEST_BYTES:
                raise ServiceProtocolError("request exceeds size limit")
            request = json.loads(raw.decode("utf-8"))
            response = service.handle_request(request)
        except (ServiceProtocolError, UnicodeDecodeError, json.JSONDecodeError, RecursionError, TypeError, ValueError) as error:
            response = {"ok": False, "error": str(error)}
        self.wfile.write((json.dumps(response, separators=(",", ":")) + "\n").encode("utf-8"))
        self.wfile.flush()


class _UnixServer(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, path: str, service: EcosystemService) -> None:
        self.service = service
        super().__init__(path, _RequestHandler)


class ServiceRuntime:
    """Own the private lock/socket lifecycle for a running service."""

    def __init__(self, service: EcosystemService, socket_path: Path, lock_path: Path) -> None:
        self.service = service
        self.socket_path = Path(socket_path)
        self.lock_path = Path(lock_path)
        self._lock_file: Any = None
        self._server: _UnixServer | None = None
        self._stop_requested = threading.Event()

    def __enter__(self) -> "ServiceRuntime":
        self.lock_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._lock_file = self.lock_path.open("a+")
        os.chmod(self.lock_path, 0o600)
        try:
            import fcntl
            fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (ImportError, OSError):
            self._lock_file.close()
            self._lock_file = None
            raise RuntimeError("another ecosystem service is already running") from None
        self.socket_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        try:
            self.socket_path.unlink()
        except FileNotFoundError:
            pass
        self._server = _UnixServer(str(self.socket_path), self.service)
        os.chmod(self.socket_path, 0o600)
        self.service.start()
        return self

    def serve_forever(self) -> None:
        if self._server is None:
            raise RuntimeError("service runtime is not started")
        self._server.timeout = 0.25
        while not self._stop_requested.is_set():
            self.service.advance()
            self._server.handle_request()

    def request_stop(self) -> None:
        self._stop_requested.set()

    def handle_once(self) -> None:
        """Handle one IPC request; useful for embedders and focused tests."""

        if self._server is None:
            raise RuntimeError("service runtime is not started")
        self._server.handle_request()

    def __exit__(self, *_: Any) -> None:
        try:
            self.service.save()
        finally:
            if self._server is not None:
                self._server.server_close()
            try:
                self.socket_path.unlink()
            except FileNotFoundError:
                pass
            if self._lock_file is not None:
                self._lock_file.close()


def _default_paths() -> tuple[Path, Path]:
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    if not runtime or not os.path.isabs(runtime):
        runtime = f"/tmp/omarcharium-{os.getuid()}"
    root = Path(runtime) / "omarcharium"
    return root / "ecosystem.sock", root / "ecosystem.lock"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--socket", type=Path)
    parser.add_argument("--lock", type=Path)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    default_socket, default_lock = _default_paths()
    config_path = Path(os.environ.get("OMARCHARIUM_CONFIG", Path.home() / ".config/omarcharium/config.json"))
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        config = {}
    ecosystem = normalise_ecosystem_config(config.get("ecosystem", {}) if isinstance(config, dict) else {})
    if not isinstance(config, dict) or "ecosystem" not in config:
        ecosystem["startingSeed"] = args.seed
    store = CheckpointStore(
        Path(os.environ.get("OMARCHARIUM_STATE", Path.home() / ".local/state/omarcharium/ecosystem.json")),
        model_to_json, model_from_json,
        lambda: initial_model(ecosystem["startingSeed"], model_settings({"ecosystem": ecosystem})),
    )
    service = EcosystemService(store, seed=ecosystem["startingSeed"], settings=model_settings({"ecosystem": ecosystem}))
    service.simulation_enabled = ecosystem["enabled"]
    service.simulation_speed = ecosystem["simulationSpeed"]
    service.diagnostic_accelerated = ecosystem["diagnosticAccelerated"]
    runtime = ServiceRuntime(service, args.socket or default_socket, args.lock or default_lock)
    with runtime:
        signal.signal(signal.SIGTERM, lambda _signum, _frame: runtime.request_stop())
        signal.signal(signal.SIGINT, lambda _signum, _frame: runtime.request_stop())
        runtime.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
