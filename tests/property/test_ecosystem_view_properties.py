import copy
import unittest

from hypothesis import given, strategies as st

from scripts.ecosystem_model import Tick, initial_model, update
from scripts.ecosystem_view import Viewport, view


@st.composite
def viewports(draw):
    return Viewport(draw(st.integers(min_value=1, max_value=240)), draw(st.integers(min_value=1, max_value=140)))


class EcosystemViewHypothesisTests(unittest.TestCase):
    @given(seed=st.integers(min_value=-100_000, max_value=100_000), viewport=viewports())
    def test_projection_is_deterministic_and_bounded(self, seed, viewport):
        model = initial_model(seed)
        frame = view(model, viewport)
        assert frame == view(model, viewport)
        assert frame["width"] == viewport.width
        assert frame["height"] == viewport.height
        for item in frame["organisms"] + frame["resources"]:
            assert 0 <= item["x"] <= viewport.width
            assert 0 <= item["y"] <= viewport.height

    @given(seed=st.integers(min_value=-100_000, max_value=100_000), viewport=viewports())
    def test_projection_does_not_mutate_model(self, seed, viewport):
        model = initial_model(seed)
        before = copy.deepcopy(model)
        view(model, viewport)
        assert model == before

    @given(seed=st.integers(min_value=-100_000, max_value=100_000), viewport=viewports())
    def test_tick_motion_is_replayable(self, seed, viewport):
        model = initial_model(seed)
        stepped = update(model, Tick(1))
        assert view(stepped, viewport) == view(update(model, Tick(1)), viewport)
