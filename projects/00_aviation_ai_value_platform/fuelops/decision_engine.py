"""Decision layer: from per-flight attribution to a reviewable intervention queue.

The model predicts. This module decides what an operator sees, in this order:

1. **Abstain** when the model should not be trusted for a flight: a feature
   outside the training range (out-of-distribution) or a prediction interval
   much wider than typical. Abstained flights go to a separate review bucket
   rather than being silently ranked.
2. **Filter** to flights whose *controllable* excess clears a minimum size
   and a minimum share of the total. A flight with large excess that is
   entirely contextual (headwind, payload) is not an intervention.
3. **Rank** by controllable kg, not by total predicted kg. Ranking on the
   total is the naive policy this design exists to replace, and the report
   measures the difference.
4. **Explain** each queued flight with its dominant lever and the kg the
   model attributes to it.

Evaluation uses the simulator's ground truth to score the queue against an
oracle that ranks on the *true* controllable excess, and against the naive
and random policies. "Capture" is the share of all true controllable fuel
in the window that sits inside the top-k queue.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .attribution import LEVERS


# --------------------------------------------------------------------------- #
# Abstention
# --------------------------------------------------------------------------- #
def out_of_distribution(encoder, df: pd.DataFrame, margin: float = config.OOD_RANGE_MARGIN) -> pd.Series:
    """True when any numeric feature lies outside the training range (+margin)."""
    flags = pd.Series(False, index=df.index)
    for col, (lo, hi) in encoder.train_ranges.items():
        span = max(hi - lo, 1e-9)
        outside = (df[col] < lo - margin * span) | (df[col] > hi + margin * span)
        flags |= outside
    for col in config.CATEGORICAL_FEATURES:
        flags |= ~df[col].astype(str).isin(encoder.categories[col])
    return flags


def abstention_reasons(encoder, df: pd.DataFrame, attr: pd.DataFrame) -> pd.Series:
    ood = out_of_distribution(encoder, df)
    median_width = attr["interval_width_kg"].median()
    wide = attr["interval_width_kg"] > config.MAX_INTERVAL_WIDTH_RATIO * median_width
    reason = pd.Series("", index=df.index, dtype=object)
    reason[wide] = "low confidence: wide prediction interval"
    reason[ood] = "out of distribution: feature outside training range"
    return reason


# --------------------------------------------------------------------------- #
# Queue construction
# --------------------------------------------------------------------------- #
def _recommendation(row: pd.Series) -> str:
    parts = []
    for lever in LEVERS:
        kg = row[f"lever_{lever}_kg"]
        if kg >= 0.25 * row["controllable_kg"] and kg >= 25.0:
            parts.append(f"{config.LEVER_LABELS[lever]} (~{kg:.0f} kg)")
    return "Review: " + "; ".join(parts) if parts else "Review: diffuse controllable excess across levers"


def build_queue(encoder, df: pd.DataFrame, attr: pd.DataFrame) -> pd.DataFrame:
    """Attach policy decisions to every flight; rank the actionable ones."""
    q = pd.concat([df, attr], axis=1)
    q["abstain_reason"] = abstention_reasons(encoder, df, attr)
    q["abstained"] = q["abstain_reason"] != ""

    meets_size = q["controllable_kg"] >= config.MIN_CONTROLLABLE_KG
    meets_share = q["controllable_share"] >= config.MIN_CONTROLLABLE_SHARE
    q["actionable"] = ~q["abstained"] & meets_size & meets_share

    q["status"] = np.select(
        [q["abstained"], q["actionable"], ~meets_size],
        ["review_low_confidence", "queued", "no_action"],
        default="no_action_contextual",
    )
    q["priority_kg"] = np.where(q["actionable"], q["controllable_kg"], 0.0)
    q["recommendation"] = ""
    q.loc[q["actionable"], "recommendation"] = q[q["actionable"]].apply(_recommendation, axis=1)
    return q.sort_values("priority_kg", ascending=False)


# --------------------------------------------------------------------------- #
# Policy evaluation against ground truth
# --------------------------------------------------------------------------- #
def _policy_scorecard(top: pd.DataFrame, truth_total: float) -> dict:
    """What an operator reviewing this top-k list would actually find."""
    ctrl = top["true_controllable_kg"]
    ctx = top["true_contextual_kg"]
    share = ctrl / (ctrl + ctx)
    return {
        "capture_of_controllable_fuel": float(ctrl.sum() / max(truth_total, 1e-9)),
        "precision_actionable": float((share >= config.MIN_CONTROLLABLE_SHARE).mean()),
        "mean_true_controllable_kg": float(ctrl.mean()),
        "mean_true_contextual_kg": float(ctx.mean()),
        "contextual_share_of_reviewed_excess": float(ctx.sum() / max((ctrl + ctx).sum(), 1e-9)),
    }


def evaluate_policies(queue: pd.DataFrame, k_fraction: float = config.TOP_K_FRACTION, seed: int = config.SEED) -> dict:
    """Score competing ranking policies on the same review capacity (top-k).

    * capture: share of all true controllable fuel inside the top-k list
    * precision: share of the list where the excess is mostly controllable
    * contextual share of reviewed excess: operator effort spent on fuel
      nobody can recover (the cost of ranking on the total prediction)
    """
    q = queue.reset_index(drop=True)
    truth = q["true_controllable_kg"].to_numpy()
    k = max(1, int(len(q) * k_fraction))
    rng = np.random.default_rng(seed)

    policies = {
        "oracle_true_controllable": np.argsort(-truth),
        "controllable_attribution": np.argsort(-q["priority_kg"].to_numpy(), kind="stable"),
        "naive_total_predicted": np.argsort(-q["predicted_kg"].to_numpy()),
        "random": rng.permutation(len(q)),
    }
    scorecards = {name: _policy_scorecard(q.iloc[order[:k]], truth.sum()) for name, order in policies.items()}

    top = q.iloc[policies["controllable_attribution"][:k]]
    return {
        "k": int(k),
        "k_fraction": float(k_fraction),
        "policies": scorecards,
        "mean_true_controllable_overall_kg": float(truth.mean()),
        "status_counts": q["status"].value_counts().to_dict(),
        "abstention_rate": float(q["abstained"].mean()),
        "dominant_lever_mix_in_queue": top["dominant_lever"].value_counts(normalize=True).round(3).to_dict(),
    }
