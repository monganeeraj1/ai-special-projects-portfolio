import unittest

from fuelops import config, decision_engine
from tests.fixtures import pipeline


class TestRankingPolicies(unittest.TestCase):
    def setUp(self):
        self.policies = pipeline()["policy"]["policies"]

    def test_policy_ordering_is_oracle_ours_naive_random(self):
        c = {k: v["capture_of_controllable_fuel"] for k, v in self.policies.items()}
        self.assertGreaterEqual(c["oracle_true_controllable"], c["controllable_attribution"])
        self.assertGreater(c["controllable_attribution"], c["naive_total_predicted"])
        self.assertGreater(c["naive_total_predicted"], c["random"])

    def test_ours_is_close_to_oracle(self):
        c = self.policies
        ratio = c["controllable_attribution"]["capture_of_controllable_fuel"] / c["oracle_true_controllable"]["capture_of_controllable_fuel"]
        self.assertGreater(ratio, 0.90)

    def test_random_captures_roughly_its_share(self):
        self.assertAlmostEqual(self.policies["random"]["capture_of_controllable_fuel"], config.TOP_K_FRACTION, delta=0.03)

    def test_ranking_on_controllable_sends_operators_to_actionable_flights(self):
        ours, naive = self.policies["controllable_attribution"], self.policies["naive_total_predicted"]
        self.assertGreater(ours["precision_actionable"], naive["precision_actionable"])
        self.assertLess(ours["contextual_share_of_reviewed_excess"], naive["contextual_share_of_reviewed_excess"])


class TestQueueMechanics(unittest.TestCase):
    def setUp(self):
        p = pipeline()
        self.queue, self.models, self.test, self.attr = p["queue"], p["models"], p["test"], p["attr"]

    def test_statuses_are_exhaustive_and_exclusive(self):
        self.assertEqual(set(self.queue["status"].unique()) - {"queued", "no_action", "no_action_contextual", "review_low_confidence"}, set())
        self.assertTrue((self.queue["actionable"] == (self.queue["status"] == "queued")).all())

    def test_queue_is_sorted_by_priority(self):
        pr = self.queue["priority_kg"].to_numpy()
        self.assertTrue((pr[:-1] >= pr[1:]).all())

    def test_every_queued_flight_has_a_recommendation_and_meets_policy(self):
        q = self.queue[self.queue["actionable"]]
        self.assertTrue(q["recommendation"].str.startswith("Review").all())
        self.assertTrue((q["controllable_kg"] >= config.MIN_CONTROLLABLE_KG).all())
        self.assertTrue((q["controllable_share"] >= config.MIN_CONTROLLABLE_SHARE).all())

    def test_abstention_is_rare_in_distribution(self):
        self.assertLess(self.queue["abstained"].mean(), 0.05)

    def test_out_of_distribution_flight_is_abstained_not_ranked(self):
        row = self.test.head(2).copy()
        row["distance_km"] = 25_000.0  # no such sector exists in training
        attr = pipeline()["attr"].loc[row.index]
        q = decision_engine.build_queue(self.models.encoder, row, attr)
        self.assertTrue((q["status"] == "review_low_confidence").all())
        self.assertTrue((q["priority_kg"] == 0).all())

    def test_unseen_station_is_abstained(self):
        row = self.test.head(2).copy()
        row["departure_station"] = "NEW-STATION"
        attr = pipeline()["attr"].loc[row.index]
        q = decision_engine.build_queue(self.models.encoder, row, attr)
        self.assertTrue(q["abstained"].all())


if __name__ == "__main__":
    unittest.main()
