from __future__ import annotations

import unittest

from scripts.ecosystem_config import CONTROL_KEYS, apply_ecosystem_control, normalise_ecosystem_config

try:
    from hypothesis import given, strategies as st
except ImportError:
    given = None
    st = None


if given is None or st is None:

    class EcosystemConfigPropertyTests(unittest.TestCase):
        @unittest.skip("install requirements-dev.txt to run Hypothesis properties")
        def test_config_properties(self) -> None:
            self.fail("Hypothesis is unavailable")

else:

    class EcosystemConfigPropertyTests(unittest.TestCase):
        @given(
            st.floats(allow_nan=True, allow_infinity=True),
            st.floats(allow_nan=True, allow_infinity=True),
            st.integers(),
        )
        def test_controls_always_normalize_to_safe_values(self, speed: float, mutation: float, seed: int) -> None:
            config = normalise_ecosystem_config({
                "simulationSpeed": speed, "mutationRate": mutation, "startingSeed": seed,
            })
            self.assertTrue(0.1 <= config["simulationSpeed"] <= 4.0)
            self.assertTrue(0.0 <= config["mutationRate"] <= 1.0)
            self.assertTrue(-(2**31) <= config["startingSeed"] <= 2**31 - 1)

        @given(st.sampled_from(sorted(CONTROL_KEYS)), st.integers())
        def test_control_updates_remain_normalized(self, key: str, value: int) -> None:
            config = apply_ecosystem_control({}, key, value)
            self.assertEqual(config, normalise_ecosystem_config(config))


if __name__ == "__main__":
    unittest.main()
