import unittest

import numpy as np

from fuelops import config, drift_monitor
from tests.fixtures import pipeline


def _row(report, monitor, name):
    return report[(report["monitor"] == monitor) & (report["name"] == name)].iloc[0]


class TestPsi(unittest.TestCase):
    def test_identical_distributions_score_zero(self):
        x = np.random.default_rng(0).normal(size=5000)
        self.assertLess(drift_monitor.psi(x, x), 1e-9)

    def test_shifted_distribution_scores_high(self):
        rng = np.random.default_rng(0)
        self.assertGreater(drift_monitor.psi(rng.normal(size=5000), rng.normal(loc=1.0, size=5000)), config.PSI_REVIEW_THRESHOLD)

    def test_bins_cover_values_outside_reference_range(self):
        rng = np.random.default_rng(0)
        ref = rng.uniform(0, 1, 2000)
        cur = rng.uniform(5, 6, 2000)  # entirely outside the reference range
        self.assertGreater(drift_monitor.psi(ref, cur), 1.0)


class TestDriftSignatures(unittest.TestCase):
    """The three windows in RESULTS.md must keep their distinct signatures."""

    @classmethod
    def setUpClass(cls):
        p = pipeline()
        models, ref, test = p["models"], p["reference"], p["test"]
        cls.clean = drift_monitor.drift_report(models, ref, test)
        cls.measurement = drift_monitor.drift_report(models, ref, drift_monitor.inject_measurement_drift(test))
        cls.operational = drift_monitor.drift_report(models, ref, drift_monitor.inject_operational_drift(test))

    def test_season_matched_reference_keeps_the_clean_window_quiet(self):
        self.assertFalse((self.clean["flag"] == "REVIEW").any(), self.clean.to_string())
        self.assertNotIn("month", self.clean["name"].tolist())

    def test_measurement_drift_is_caught_by_residuals_not_by_feature_psi(self):
        taxi = _row(self.measurement, "feature", "taxi_out_min")
        concept = _row(self.measurement, "concept", "mean_residual_kg")
        self.assertIn(taxi["flag"], {"WATCH", "REVIEW"})
        self.assertEqual(concept["flag"], "REVIEW")
        self.assertLess(concept["value"], 0.0, "model now over-predicts, so residuals go negative")
        # Only the injected feature moves.
        others = self.measurement[(self.measurement["monitor"] == "feature") & (self.measurement["name"] != "taxi_out_min")]
        self.assertTrue((others["flag"] == "OK").all())

    def test_operational_drift_is_loud_on_features_and_quiet_on_residuals(self):
        route = _row(self.operational, "feature", "route_efficiency_score")
        self.assertEqual(route["flag"], "REVIEW")
        z_operational = abs(_row(self.operational, "concept", "mean_residual_kg")["value"])
        z_measurement = abs(_row(self.measurement, "concept", "mean_residual_kg")["value"])
        self.assertLess(z_operational, 0.5 * z_measurement)
        pred_clean = _row(self.clean, "prediction", "predicted_kg")["value"]
        pred_operational = _row(self.operational, "prediction", "predicted_kg")["value"]
        self.assertGreater(pred_operational, 5 * pred_clean)


if __name__ == "__main__":
    unittest.main()
