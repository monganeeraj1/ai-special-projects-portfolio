import unittest

import pandas as pd

from fuelops import config
from tests.fixtures import pipeline


class TestValidationDesign(unittest.TestCase):
    def setUp(self):
        p = pipeline()
        self.train, self.test, self.report = p["train"], p["test"], p["model_report"]

    def test_split_is_temporal_not_random(self):
        self.assertLess(self.train["flight_date"].max(), self.test["flight_date"].min() + pd.Timedelta(days=1))
        self.assertAlmostEqual(len(self.test) / (len(self.train) + len(self.test)), config.TEMPORAL_TEST_FRACTION, places=2)

    def test_gradient_boosting_beats_both_baselines_by_a_margin(self):
        m = self.report["models"]
        self.assertLess(m["gradient_boosting"]["mae"], 0.85 * m["ridge_baseline"]["mae"])
        self.assertLess(m["gradient_boosting"]["mae"], 0.40 * m["mean_baseline"]["mae"])

    def test_gradient_boosting_is_close_to_the_noise_floor(self):
        m = self.report["models"]
        gap_closed = (m["ridge_baseline"]["mae"] - m["gradient_boosting"]["mae"]) / (
            m["ridge_baseline"]["mae"] - m["noise_floor"]["mae"]
        )
        self.assertGreater(gap_closed, 0.70)
        self.assertLess(m["gradient_boosting"]["r2"], m["noise_floor"]["r2"] + 1e-9, "nothing beats the floor")

    def test_calibrated_interval_reaches_nominal_coverage(self):
        i = self.report["interval"]
        self.assertLess(i["raw_coverage"], i["nominal_coverage"], "raw quantiles are expected to under-cover on a later window")
        self.assertGreater(i["calibrated_coverage"], i["nominal_coverage"] - 0.03)
        self.assertLess(i["calibrated_coverage"], i["nominal_coverage"] + 0.08, "interval should not be uselessly wide")
        self.assertGreater(i["conformal_margin_kg"], 0.0)

    def test_no_segment_collapses(self):
        seg = pd.DataFrame(self.report["segments"])
        self.assertTrue((seg["r2"] > 0.6).all(), seg.to_string())
        self.assertTrue((seg["n"] >= 200).all())

    def test_month_carries_no_direct_signal(self):
        imp = self.report["importance"].set_index("feature")["importance_mae_kg"]
        self.assertLess(abs(imp["month"]), 2.0)
        self.assertEqual(imp.idxmax(), "distance_km")


class TestEncoder(unittest.TestCase):
    def test_unseen_category_becomes_missing_not_an_error(self):
        p = pipeline()
        row = p["test"].head(3).copy()
        row["departure_station"] = "NEW-STATION"
        X = p["models"].encoder.transform(row)
        self.assertTrue(X["departure_station"].isna().all())
        preds = p["models"].predict(row)
        self.assertEqual(len(preds), 3)


if __name__ == "__main__":
    unittest.main()
