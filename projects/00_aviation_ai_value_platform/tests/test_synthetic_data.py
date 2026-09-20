import unittest

import numpy as np

from fuelops import config, synthetic_data
from tests.fixtures import pipeline


class TestFeatureContract(unittest.TestCase):
    """Leakage discipline is enforced by test, not by convention."""

    def test_no_ground_truth_column_is_a_model_feature(self):
        leaked = [c for c in config.FEATURES if c.startswith("true_") or c == config.TARGET]
        self.assertEqual(leaked, [])

    def test_every_lever_has_a_benchmark_and_label(self):
        self.assertEqual(set(config.CONTROLLABLE_FEATURES), set(config.LEVER_BENCHMARKS))
        self.assertEqual(set(config.CONTROLLABLE_FEATURES), set(config.LEVER_LABELS))

    def test_segment_key_derived_from_distance_is_not_a_feature(self):
        self.assertNotIn("route_family", config.FEATURES)


class TestSimulator(unittest.TestCase):
    def setUp(self):
        self.df = pipeline()["df"]

    def test_shape_and_cleanliness(self):
        self.assertEqual(len(self.df), 12_000)
        self.assertFalse(self.df[config.FEATURES + [config.TARGET]].isna().any().any())
        self.assertTrue((self.df[config.TARGET] >= 0).all())

    def test_components_add_up_to_target(self):
        raw = self.df["true_contextual_kg"] + self.df["true_controllable_kg"] + self.df["true_noise_kg"]
        clipped = (raw < 0).mean()
        self.assertLess(clipped, 0.01, "target clipping at zero should be rare")
        np.testing.assert_allclose(self.df[config.TARGET], np.clip(raw, 0, None), rtol=0, atol=1e-9)

    def test_lever_columns_sum_to_controllable(self):
        lever_cols = [c for c in config.GROUND_TRUTH_COLUMNS if c.startswith("true_lever_")]
        np.testing.assert_allclose(self.df[lever_cols].sum(axis=1), self.df["true_controllable_kg"], rtol=1e-9)

    def test_controllable_at_benchmark_is_zero(self):
        at_benchmark = self.df.copy()
        for lever, value in config.LEVER_BENCHMARKS.items():
            at_benchmark[lever] = value
        contributions = synthetic_data.lever_contributions(at_benchmark)
        self.assertAlmostEqual(float(contributions.abs().to_numpy().max()), 0.0)

    def test_problem_is_neither_trivial_nor_hopeless(self):
        share = self.df["true_controllable_kg"].sum() / (
            self.df["true_controllable_kg"].sum() + self.df["true_contextual_kg"].sum()
        )
        self.assertTrue(0.25 < share < 0.55, f"controllable share {share:.2f} outside the intended band")
        signal = (self.df["true_contextual_kg"] + self.df["true_controllable_kg"]).var()
        ceiling = signal / (signal + self.df["true_noise_kg"].var())
        self.assertTrue(0.80 < ceiling < 0.97, f"R² ceiling {ceiling:.2f} makes the benchmark meaningless")

    def test_dates_are_sorted_and_span_two_years(self):
        d = self.df["flight_date"]
        self.assertTrue(d.is_monotonic_increasing)
        self.assertGreaterEqual((d.max() - d.min()).days, 700)

    def test_generation_is_reproducible(self):
        a = synthetic_data.generate(500, seed=3)
        b = synthetic_data.generate(500, seed=3)
        self.assertTrue(a.equals(b))


if __name__ == "__main__":
    unittest.main()
