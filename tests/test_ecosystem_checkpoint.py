from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.ecosystem_checkpoint import CheckpointScheduler, CheckpointStore


class CheckpointStoreTests(unittest.TestCase):
    def test_checkpoint_is_compact_atomic_and_round_trips(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ecosystem.json"
            store = CheckpointStore(path, lambda value: value, lambda value: value, lambda: {"fallback": True})
            store.checkpoint({"z": 1, "a": [True, 2]})

            self.assertEqual(store.load(), {"z": 1, "a": [True, 2]})
            self.assertEqual(path.read_text(encoding="utf-8"), '{"a":[true,2],"z":1}\n')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)

    def test_invalid_and_oversized_checkpoints_use_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "ecosystem.json"
            path.write_text("not json", encoding="utf-8")
            store = CheckpointStore(path, lambda value: value, lambda value: value, lambda: {"fresh": True})
            self.assertEqual(store.load(), {"fresh": True})

            path.write_text(json.dumps({"too": "large"}), encoding="utf-8")
            limited = CheckpointStore(path, lambda value: value, lambda value: value, lambda: {"fresh": True}, max_bytes=2)
            self.assertEqual(limited.load(), {"fresh": True})


class CheckpointSchedulerTests(unittest.TestCase):
    def test_scheduler_coalesces_writes_until_due(self) -> None:
        writes: list[dict[str, int]] = []

        class FakeStore:
            def checkpoint(self, model: dict[str, int]) -> None:
                writes.append(model.copy())

        scheduler = CheckpointScheduler(FakeStore(), interval=300)
        scheduler.mark_dirty()
        self.assertFalse(scheduler.maybe_checkpoint({"tick": 1}, 0))
        self.assertFalse(scheduler.maybe_checkpoint({"tick": 2}, 299.9))
        self.assertTrue(scheduler.maybe_checkpoint({"tick": 3}, 300))
        self.assertFalse(scheduler.maybe_checkpoint({"tick": 4}, 301))
        self.assertEqual(writes, [{"tick": 3}])

    def test_forced_checkpoint_is_immediate_and_failed_write_stays_dirty(self) -> None:
        writes: list[int] = []

        class FlakyStore:
            fail = True

            def checkpoint(self, model: int) -> None:
                if self.fail:
                    raise OSError("temporary failure")
                writes.append(model)

        store = FlakyStore()
        scheduler = CheckpointScheduler(store, interval=300)
        scheduler.mark_dirty()
        with self.assertRaises(OSError):
            scheduler.maybe_checkpoint(1, 10, force=True)
        self.assertTrue(scheduler.dirty)
        store.fail = False
        self.assertTrue(scheduler.maybe_checkpoint(2, 11, force=True))
        self.assertEqual(writes, [2])


if __name__ == "__main__":
    unittest.main()
