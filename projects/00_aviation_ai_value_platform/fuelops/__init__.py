"""fuelops — a validated prototype of an AI fuel-efficiency decision system.

Modules, in pipeline order:

    synthetic_data   disclosed simulator with ground truth for validation
    train            temporal split, baselines, gradient boosting, calibrated intervals
    attribution      counterfactual controllable/contextual split, exact Shapley by lever
    decision_engine  abstention, filtering, ranking; scored against oracle/naive/random
    drift_monitor    feature, prediction and concept drift with season-matched reference
    value_model      illustrative annual value range, one row informed by the pipeline
    report           renders RESULTS.md from the numbers above

Run everything with `python -m fuelops`; run the tests with `python -m pytest`.
"""
