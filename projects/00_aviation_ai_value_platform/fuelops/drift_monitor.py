"""Drift monitoring: inputs, outputs and (when labels arrive) errors.

Three different things can drift, and they need three different checks:

* **Feature drift** — the operating population moved (new routes, a station
  became congested, a fleet change). Measured with the Population Stability
  Index (PSI) per feature against the training reference.
* **Prediction drift** — the model's output distribution moved, which can
  happen even when individual features look stable (interactions). Same PSI,
  applied to predictions.
* **Concept drift** — the relationship between inputs and outcome changed.
  Only detectable once actual fuel is known for the new window; measured as
  a shift in mean residual with a z-test against the reference residuals.

Reference window
----------------
Comparing a six-month window against a two-year reference flags every
seasonal feature (month, temperature, wind) as drifted by construction. The
pipeline therefore builds a **season-matched reference**: training flights
from the same calendar months as the window under review.

Scenarios
---------
The pipeline runs the monitor on the genuine test window (which should pass,
or the test set is not representative) and on two injected scenarios with
different signatures:

* **Measurement drift** — recorded taxi-out time rises 20% because an
  upstream definition changed (e.g. pushback wait now included) while real
  fuel burn is unchanged. Features barely move under a PSI threshold;
  residuals move a lot. This is Failure Analysis scenario 3.
* **Operational drift** — an airspace constraint degrades route efficiency
  and fuel genuinely rises. Features and predictions move; residuals do not,
  because the model is still right about the world.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .synthetic_data import contextual_component, lever_contributions


def psi(expected: np.ndarray, actual: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index with quantile bins fitted on `expected`."""
    breaks = np.unique(np.quantile(expected, np.linspace(0.0, 1.0, bins + 1)))
    breaks[0], breaks[-1] = -np.inf, np.inf
    e_counts, _ = np.histogram(expected, bins=breaks)
    a_counts, _ = np.histogram(actual, bins=breaks)
    e_pct = np.clip(e_counts / max(e_counts.sum(), 1), 1e-6, None)
    a_pct = np.clip(a_counts / max(a_counts.sum(), 1), 1e-6, None)
    return float(np.sum((a_pct - e_pct) * np.log(a_pct / e_pct)))


def _flag(score: float) -> str:
    if score >= config.PSI_REVIEW_THRESHOLD:
        return "REVIEW"
    if score >= config.PSI_WATCH_THRESHOLD:
        return "WATCH"
    return "OK"


def season_matched_reference(reference: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    """Reference rows from the same calendar months as the current window."""
    months = current["month"].unique()
    matched = reference[reference["month"].isin(months)]
    return matched if len(matched) >= 500 else reference


def drift_report(models, reference: pd.DataFrame, current: pd.DataFrame) -> pd.DataFrame:
    """One row per monitored quantity with PSI (or z-score) and a flag."""
    rows = []
    for col in config.NUMERIC_FEATURES:
        if col in config.DRIFT_EXCLUDED_FEATURES:
            continue
        s = psi(reference[col].to_numpy(), current[col].to_numpy())
        rows.append({"monitor": "feature", "name": col, "statistic": "psi", "value": s, "flag": _flag(s)})

    ref_pred = models.predict(reference)["predicted_kg"].to_numpy()
    cur_pred = models.predict(current)["predicted_kg"].to_numpy()
    s = psi(ref_pred, cur_pred)
    rows.append({"monitor": "prediction", "name": "predicted_kg", "statistic": "psi", "value": s, "flag": _flag(s)})

    if config.TARGET in current and config.TARGET in reference:
        ref_res = reference[config.TARGET].to_numpy() - ref_pred
        cur_res = current[config.TARGET].to_numpy() - cur_pred
        se = np.sqrt(ref_res.var(ddof=1) / len(ref_res) + cur_res.var(ddof=1) / len(cur_res))
        z = float((cur_res.mean() - ref_res.mean()) / max(se, 1e-9))
        rows.append({
            "monitor": "concept",
            "name": "mean_residual_kg",
            "statistic": "z",
            "value": z,
            "flag": "REVIEW" if abs(z) >= config.RESIDUAL_SHIFT_Z_THRESHOLD else "OK",
        })
    return pd.DataFrame(rows)


def inject_measurement_drift(df: pd.DataFrame, factor: float = 1.20) -> pd.DataFrame:
    """Scenario A: recorded taxi-out time rises 20%; real fuel burn does not.

    An upstream definition change (pushback wait now counted as taxi) is a
    data-feed problem, not an operational one. Only the feature changes, so
    the model's residuals shift: it now predicts more excess than occurs.
    """
    out = df.copy()
    out["taxi_out_min"] = out["taxi_out_min"] * factor
    return out


def inject_operational_drift(df: pd.DataFrame, efficiency_loss: float = 0.08) -> pd.DataFrame:
    """Scenario B: an airspace constraint degrades route efficiency for real.

    Both the feature and the outcome move, recomputed through the disclosed
    DGP with the original noise draw. The model should still be right, so
    residuals stay flat while feature and prediction PSI rise.
    """
    out = df.copy()
    out["route_efficiency_score"] = (out["route_efficiency_score"] - efficiency_loss).clip(lower=0.60)
    levers = lever_contributions(out)
    for c in levers.columns:
        out[c] = levers[c]
    out["true_controllable_kg"] = levers.sum(axis=1)
    out["true_contextual_kg"] = contextual_component(out)
    out[config.TARGET] = np.clip(
        out["true_contextual_kg"] + out["true_controllable_kg"] + out["true_noise_kg"], 0.0, None
    )
    return out
