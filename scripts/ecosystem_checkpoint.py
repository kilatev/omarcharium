"""Durable, low-frequency JSON checkpoints for the ecosystem service.

This module is intentionally independent from the inherited terminal renderer.
The service owns the model in memory and uses these adapters only for restart
recovery and explicit durability events.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, Generic, TypeVar


ModelT = TypeVar("ModelT")


class CheckpointStore(Generic[ModelT]):
    """Atomically persist and recover one JSON-serializable model.

    The codec callbacks define the model seam. ``encode`` must return a JSON
    value and ``decode`` must validate the schema and return a model. Failed
    reads return ``fallback()``; failed writes raise so the service can retain
    the dirty flag and retry later.
    """

    def __init__(
        self,
        path: Path,
        encode: Callable[[ModelT], Any],
        decode: Callable[[Any], ModelT],
        fallback: Callable[[], ModelT],
        *,
        max_bytes: int = 4 * 1024 * 1024,
    ) -> None:
        if max_bytes < 1:
            raise ValueError("max_bytes must be positive")
        self.path = Path(path)
        self._encode = encode
        self._decode = decode
        self._fallback = fallback
        self.max_bytes = max_bytes

    def load(self) -> ModelT:
        """Load and validate the checkpoint, or return a safe initial model."""

        try:
            with self.path.open("rb") as stream:
                payload = stream.read(self.max_bytes + 1)
            if len(payload) > self.max_bytes:
                raise ValueError("checkpoint exceeds size limit")
            return self._decode(json.loads(payload.decode("utf-8")))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError, TypeError, ValueError):
            return self._fallback()

    def checkpoint(self, model: ModelT) -> None:
        """Write one compact, durable checkpoint with atomic replacement."""

        encoded = json.dumps(
            self._encode(model),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        if len(encoded) > self.max_bytes:
            raise ValueError("checkpoint exceeds size limit")

        parent = self.path.parent
        parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        temporary_path: Path | None = None
        descriptor: int | None = None
        try:
            descriptor, temporary_name = tempfile.mkstemp(
                prefix=f".{self.path.name}.",
                dir=parent,
            )
            temporary_path = Path(temporary_name)
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "wb") as stream:
                descriptor = None
                stream.write(encoded)
                stream.write(b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, self.path)
            temporary_path = None
            self._fsync_directory(parent)
        finally:
            if descriptor is not None:
                os.close(descriptor)
            if temporary_path is not None:
                try:
                    temporary_path.unlink()
                except FileNotFoundError:
                    pass

    @staticmethod
    def _fsync_directory(path: Path) -> None:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


class CheckpointScheduler(Generic[ModelT]):
    """Coalesce dirty model updates into infrequent checkpoint writes."""

    def __init__(self, store: CheckpointStore[ModelT], *, interval: float = 300.0) -> None:
        if interval <= 0:
            raise ValueError("interval must be positive")
        self.store = store
        self.interval = float(interval)
        self.dirty = False
        self.dirty_since: float | None = None
        self.last_checkpoint_at: float | None = None

    def mark_dirty(self) -> None:
        """Record that in-memory state has changed since the last checkpoint."""

        self.dirty = True

    def maybe_checkpoint(self, model: ModelT, now: float, *, force: bool = False) -> bool:
        """Checkpoint when due or forced; return whether a write succeeded."""

        if not self.dirty:
            return False
        if self.dirty_since is None:
            self.dirty_since = float(now)
        due = now - self.dirty_since >= self.interval
        if not force and not due:
            return False
        self.store.checkpoint(model)
        self.last_checkpoint_at = float(now)
        self.dirty = False
        self.dirty_since = None
        return True
