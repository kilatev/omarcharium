from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.ecosystem_checkpoint import CheckpointScheduler, CheckpointStore

try:
    from hypothesis import given, strategies as st
except ImportError:  # Keep the base test command usable without dev extras.
    given = None
    st = None


if given is None or st is None:

    class CheckpointHypothesisUnavailableTests(unittest.TestCase):
        @unittest.skip("install requirements-dev.txt to run Hypothesis properties")
        def test_checkpoint_properties(self) -> None:
            self.fail("Hypothesis is unavailable")

else:

    json_values = st.recursive(
        st.none() | st.booleans() | st.integers() | st.text(alphabet=st.characters(blacklist_categories=("Cs",))),
        lambda children: st.lists(children, max_size=4) | st.dictionaries(st.text(max_size=8), children, max_size=4),
        max_leaves=20,
    )

    class CheckpointHypothesisTests(unittest.TestCase):
        @given(json_values)
        def test_json_checkpoint_round_trip(self, value: object) -> None:
            with tempfile.TemporaryDirectory() as directory:
                store = CheckpointStore(
                    Path(directory) / "ecosystem.json",
                    lambda model: model,
                    lambda payload: payload,
                    lambda: None,
                )
                store.checkpoint(value)
                self.assertEqual(store.load(), value)

        @given(
            interval=st.integers(min_value=1, max_value=1_000),
            elapsed=st.integers(min_value=0, max_value=2_000),
        )
        def test_dirty_updates_are_coalesced_until_interval(
            self,
            interval: int,
            elapsed: int,
        ) -> None:
            writes: list[int] = []

            class FakeStore:
                def checkpoint(self, model: int) -> None:
                    writes.append(model)

            scheduler = CheckpointScheduler(FakeStore(), interval=interval)
            scheduler.mark_dirty()
            scheduler.maybe_checkpoint(1, 0)
            scheduler.maybe_checkpoint(2, elapsed)

            if elapsed < interval:
                self.assertEqual(writes, [])
                self.assertTrue(scheduler.dirty)
            else:
                self.assertEqual(writes, [2])
                self.assertFalse(scheduler.dirty)


if __name__ == "__main__":
    unittest.main()
