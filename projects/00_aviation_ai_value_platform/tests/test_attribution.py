import unittest

import numpy as np

from fuelops import attribution, config
from tests.fixtures import pipeline


class TestShapleyDecomposition(unittest.TestCase):
    def setUp(self):
        p = pipeline()
        self.attr, self.test, self.models = p["attr"], p["test"], p["models"]

    def test_efficiency_levers_sum_exactly_to_controllable(self):
        lever_cols = [f"lever_{l}_kg" for l in attribution.LEVERS]
        np.testing.assert_allclose(self.attr[lever_cols].sum(axis=1), self.attr["controllable_kg"], atol=1e-6)

    def test_controllable_plus_contextual_equals_prediction(self):
        np.testing.assert_allclose(
            self.attr["controllable_kg"] + self.attr["contextual_kg"], self.attr["predicted_kg"], atol=1e-6
        )

    def test_flight_already_at_benchmark_has_no_controllable_excess(self):
        row = self.test.head(50).copy()
        for lever, value in config.LEVER_BENCHMARKS.items():
            row[lever] = value
        at_benchmark = attribution.attribute(self.models, row)
        self.assertLess(at_benchmark["controllable_kg"].abs().max(), 1e-6)

    def test_worsening_a_lever_never_reduces_its_own_credit_on_average(self):
        base = self.test.head(300).copy()
        worse = base.copy()
        worse["taxi_out_min"] = worse["taxi_out_min"] + 15.0
        delta = (
            attribution.attribute(self.models, worse)["lever_taxi_out_min_kg"].to_numpy()
            - attribution.attribute(self.models, base)["lever_taxi_out_min_kg"].to_numpy()
        )
        self.assertGreater(delta.mean(), 30.0)


class TestAttributionAgainstGroundTruth(unittest.TestCase):
    """Only possible because the simulator is disclosed: the estimated
    controllable/contextual split is scored against the true one."""

    def setUp(self):
        self.v = pipeline()["validation"]

    def test_controllable_estimate_tracks_truth(self):
        self.assertGreater(self.v["controllable_correlation"], 0.93)

    def test_controllable_share_is_recovered_within_tolerance(self):
        self.assertLess(abs(self.v["share_gap_pp"]), 8.0)

    def test_bias_direction_is_the_documented_one(self):
        # Tree ensembles extrapolate flatly at the benchmark edge, so the
        # counterfactual under-states the controllable component. If this
        # ever flips, the explanation in RESULTS.md / MODEL_CARD.md is wrong.
        self.assertLess(self.v["share_gap_pp"], 0.0)

    def test_dominant_lever_is_usually_right(self):
        self.assertGreater(self.v["dominant_lever_accuracy"], 0.75)

    def test_every_lever_is_individually_recovered(self):
        for lever, r in self.v["per_lever"].items():
            self.assertGreater(r["correlation"], 0.85, lever)


if __name__ == "__main__":
    unittest.main()
