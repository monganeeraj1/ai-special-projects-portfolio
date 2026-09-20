"""One in-memory pipeline run shared by every test module.

The tests deliberately run the real pipeline on a smaller sample rather than
mocking it: the claims under test are statistical (lift over baselines,
attribution accuracy, drift signatures) and only hold for the real code.
"""
from __future__ import annotations

from functools import lru_cache

from fuelops import attribution, decision_engine, drift_monitor, synthetic_data, train

N_TEST_FLIGHTS = 12_000
SEED = 7  # different from the pipeline seed: the assertions must not be seed-specific


@lru_cache(maxsize=1)
def pipeline():
    df = synthetic_data.generate(N_TEST_FLIGHTS, SEED)
    models, train_df, test_df, model_report = train.train_and_evaluate(df)
    attr = attribution.attribute(models, test_df)
    validation = attribution.validate_against_truth(attr, test_df)
    queue = decision_engine.build_queue(models.encoder, test_df, attr)
    policy = decision_engine.evaluate_policies(queue)
    reference = drift_monitor.season_matched_reference(train_df, test_df)
    return {
        "df": df,
        "models": models,
        "train": train_df,
        "test": test_df,
        "model_report": model_report,
        "attr": attr,
        "validation": validation,
        "queue": queue,
        "policy": policy,
        "reference": reference,
    }
