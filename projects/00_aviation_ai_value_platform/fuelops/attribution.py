"""Counterfactual attribution: how much of each flight's predicted excess is
controllable, and which lever is responsible.

The question the decision layer needs answered is not "which features matter
to the model" (permutation importance answers that, globally) but "for *this*
flight, how much fuel would the model expect us to save if operations had
been at benchmark?". That is a counterfactual query against the fitted model:

    controllable_kg = f(x) - f(x with all levers set to benchmark)
    contextual_kg   = f(x with all levers set to benchmark)

Splitting `controllable_kg` across the five levers is a credit-assignment
problem with interactions (the model has learned, for example, that taxi-out
excess costs more on heavy aircraft). The split uses **exact Shapley values**
over the lever set with the benchmark as the reference point: with five
levers that is 2^5 = 32 model evaluations per flight, cheap enough to do
exactly rather than approximate. Shapley efficiency guarantees the lever
contributions sum to `controllable_kg`.

Known limitation, stated up front: the counterfactual asks the model to
predict at benchmark operations, which sits at the edge of the training
distribution for some segments. Tree ensembles extrapolate flatly there. The
attribution test checks the recovered controllable share against the
simulator's truth so this error is measured rather than assumed away.
"""
from __future__ import annotations

from itertools import combinations
from math import factorial

import numpy as np
import pandas as pd

from . import config

LEVERS = list(config.CONTROLLABLE_FEATURES)


def _with_levers_at_benchmark(df: pd.DataFrame, levers_to_reset) -> pd.DataFrame:
    out = df.copy()
    for lever in levers_to_reset:
        out[lever] = config.LEVER_BENCHMARKS[lever]
    return out


def _predict(models, df: pd.DataFrame) -> np.ndarray:
    return models.point.predict(models.encoder.transform(df))


def shapley_lever_attribution(models, df: pd.DataFrame) -> pd.DataFrame:
    """Exact Shapley decomposition of controllable excess across levers.

    The characteristic function v(S) is the model's predicted excess when the
    levers in S are at their *actual* values and all other levers are at
    benchmark, minus the all-benchmark prediction. v(all levers) equals the
    total controllable excess by construction.
    """
    n = len(LEVERS)
    # Predictions for every coalition S ⊆ levers (levers in S kept at actual).
    coalition_pred: dict[frozenset, np.ndarray] = {}
    for size in range(n + 1):
        for S in combinations(LEVERS, size):
            reset = [l for l in LEVERS if l not in S]
            coalition_pred[frozenset(S)] = _predict(models, _with_levers_at_benchmark(df, reset))

    baseline = coalition_pred[frozenset()]
    phi = {lever: np.zeros(len(df)) for lever in LEVERS}
    for lever in LEVERS:
        others = [l for l in LEVERS if l != lever]
        for size in range(n):
            weight = factorial(size) * factorial(n - size - 1) / factorial(n)
            for S in combinations(others, size):
                S = frozenset(S)
                phi[lever] += weight * (coalition_pred[S | {lever}] - coalition_pred[S])

    out = pd.DataFrame(index=df.index)
    for lever in LEVERS:
        out[f"lever_{lever}_kg"] = phi[lever]
    out["contextual_kg"] = baseline
    out["controllable_kg"] = coalition_pred[frozenset(LEVERS)] - baseline
    return out


def attribute(models, df: pd.DataFrame) -> pd.DataFrame:
    """Per-flight prediction, interval, controllable/contextual split and levers."""
    preds = models.predict(df)
    levers = shapley_lever_attribution(models, df)
    out = pd.concat([preds, levers], axis=1)

    lever_cols = [f"lever_{l}_kg" for l in LEVERS]
    # Negative Shapley credit means "this lever is better than benchmark";
    # it is kept in the columns (it is informative) but not treated as an
    # intervention opportunity.
    positive = out[lever_cols].clip(lower=0.0)
    out["dominant_lever"] = positive.idxmax(axis=1).str.replace("lever_", "").str.replace("_kg", "")
    out["dominant_lever_kg"] = positive.max(axis=1)
    out["controllable_share"] = (out["controllable_kg"] / out["predicted_kg"].clip(lower=1.0)).clip(0.0, 1.0)
    return out


def validate_against_truth(attr: pd.DataFrame, df: pd.DataFrame) -> dict:
    """Compare model-based attribution with the simulator's ground truth.

    Only possible because the DGP is known. This is the test that turns the
    synthetic data from a liability into an instrument.
    """
    truth = df["true_controllable_kg"].to_numpy()
    est = attr["controllable_kg"].to_numpy()

    per_lever = {}
    for lever in LEVERS:
        t = df[f"true_lever_{lever}_kg"].to_numpy()
        e = attr[f"lever_{lever}_kg"].to_numpy()
        per_lever[lever] = {
            "true_mean_kg": float(t.mean()),
            "estimated_mean_kg": float(e.mean()),
            "correlation": float(np.corrcoef(t, e)[0, 1]) if t.std() > 0 else float("nan"),
        }

    true_share = truth.sum() / (truth.sum() + df["true_contextual_kg"].sum())
    est_share = est.sum() / (est.sum() + attr["contextual_kg"].sum())
    return {
        "controllable_mae_kg": float(np.mean(np.abs(est - truth))),
        "controllable_correlation": float(np.corrcoef(truth, est)[0, 1]),
        "true_controllable_share": float(true_share),
        "estimated_controllable_share": float(est_share),
        "share_gap_pp": float((est_share - true_share) * 100.0),
        "dominant_lever_accuracy": float(
            (attr["dominant_lever"].to_numpy()
             == df[[f"true_lever_{l}_kg" for l in LEVERS]].idxmax(axis=1)
             .str.replace("true_lever_", "").str.replace("_kg", "").to_numpy()).mean()
        ),
        "per_lever": per_lever,
    }
