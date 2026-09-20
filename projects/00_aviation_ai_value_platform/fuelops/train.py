"""Model training and validation.

Design choices a reviewer should see immediately:

* **Temporal split.** The last 25% of flights by date are held out. A random
  split would let seasonal structure leak across the boundary and overstate
  performance for a system that predicts *future* operations.
* **Baselines first.** A mean predictor and a regularised linear model are
  fitted on the same features. The gradient-boosted model is reported as a
  lift over those, never as a standalone number.
* **Uncertainty, calibrated.** Two quantile models (p10, p90) give an 80%
  prediction interval per flight. Quantile models under-cover when the test
  window drifts from training, so the interval is widened by a split-conformal
  margin computed on a held-out calibration slice (the last 20% of the
  training period). The report shows coverage before and after calibration;
  the decision layer uses interval width to abstain.
* **Segment metrics.** Aggregate error hides where a model fails. Metrics are
  sliced by route family, aircraft type and departure station.
* **Permutation importance is a structure check, not a discovery.** The DGP
  is disclosed; importance is reported to confirm the model recovers it.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from . import config

GBM_PARAMS = dict(max_depth=6, learning_rate=0.06, max_iter=400, min_samples_leaf=40, random_state=config.SEED)


# --------------------------------------------------------------------------- #
# Feature encoding
# --------------------------------------------------------------------------- #
@dataclass
class Encoder:
    """Maps a raw frame to the model matrix, with a frozen categorical vocab."""

    categories: dict[str, list[str]] = field(default_factory=dict)
    train_ranges: dict[str, tuple[float, float]] = field(default_factory=dict)

    def fit(self, df: pd.DataFrame) -> "Encoder":
        self.categories = {c: sorted(df[c].astype(str).unique().tolist()) for c in config.CATEGORICAL_FEATURES}
        self.train_ranges = {c: (float(df[c].min()), float(df[c].max())) for c in config.NUMERIC_FEATURES}
        return self

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        X = df[config.NUMERIC_FEATURES].astype(float).copy()
        for c in config.CATEGORICAL_FEATURES:
            codes = {level: float(i) for i, level in enumerate(self.categories[c])}
            # A category never seen in training becomes missing; the boosted
            # trees route missing values down a learned default branch rather
            # than failing, and the decision layer abstains on it anyway.
            X[c] = df[c].astype(str).map(codes).astype(float)
        return X

    @property
    def categorical_mask(self) -> list[bool]:
        return [c in config.CATEGORICAL_FEATURES for c in config.FEATURES]

    def one_hot(self, df: pd.DataFrame) -> pd.DataFrame:
        """Design matrix for the linear baseline."""
        X = df[config.NUMERIC_FEATURES].astype(float).copy()
        for c in config.CATEGORICAL_FEATURES:
            for level in self.categories[c]:
                X[f"{c}={level}"] = (df[c].astype(str) == level).astype(float)
        return X


# --------------------------------------------------------------------------- #
# Split
# --------------------------------------------------------------------------- #
def temporal_split(df: pd.DataFrame, test_fraction: float = config.TEMPORAL_TEST_FRACTION):
    df = df.sort_values("flight_date").reset_index(drop=True)
    cut = int(len(df) * (1.0 - test_fraction))
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()


# --------------------------------------------------------------------------- #
# Fitting
# --------------------------------------------------------------------------- #
@dataclass
class TrainedModels:
    encoder: Encoder
    point: HistGradientBoostingRegressor
    lower: HistGradientBoostingRegressor
    upper: HistGradientBoostingRegressor
    linear: object
    train_mean: float
    conformal_margin_kg: float = 0.0

    def predict(self, df: pd.DataFrame, calibrated: bool = True) -> pd.DataFrame:
        X = self.encoder.transform(df)
        margin = self.conformal_margin_kg if calibrated else 0.0
        out = pd.DataFrame(index=df.index)
        out["predicted_kg"] = self.point.predict(X)
        out["p10_kg"] = self.lower.predict(X) - margin
        out["p90_kg"] = self.upper.predict(X) + margin
        out["interval_width_kg"] = out["p90_kg"] - out["p10_kg"]
        return out


def _conformal_margin(models: "TrainedModels", calib: pd.DataFrame) -> float:
    """Split-conformal margin so the (p10, p90) interval reaches nominal coverage.

    Nonconformity score = how far outside the raw interval the truth fell
    (zero when inside). The margin is the finite-sample-corrected
    (1 - alpha) quantile of those scores on unseen calibration data.
    """
    raw = models.predict(calib, calibrated=False)
    y = calib[config.TARGET].to_numpy()
    score = np.maximum(raw["p10_kg"].to_numpy() - y, y - raw["p90_kg"].to_numpy())
    score = np.maximum(score, 0.0)
    lo_q, hi_q = config.INTERVAL_QUANTILES
    alpha = 1.0 - (hi_q - lo_q)
    n = len(score)
    level = min(1.0, np.ceil((n + 1) * (1.0 - alpha)) / n)
    return float(np.quantile(score, level))


def fit_models(train: pd.DataFrame, calibration_fraction: float = 0.20) -> TrainedModels:
    """Fit baselines, point model and quantile models; calibrate the interval.

    The training period is itself split by time: models are fitted on the
    earlier part and the interval margin is calibrated on the later part, so
    the calibration data is never seen by the quantile models.
    """
    fit, calib = temporal_split(train, test_fraction=calibration_fraction)

    enc = Encoder().fit(fit)
    X, y = enc.transform(fit), fit[config.TARGET].to_numpy()
    mask = enc.categorical_mask

    point = HistGradientBoostingRegressor(categorical_features=mask, **GBM_PARAMS).fit(X, y)
    lo_q, hi_q = config.INTERVAL_QUANTILES
    lower = HistGradientBoostingRegressor(loss="quantile", quantile=lo_q, categorical_features=mask, **GBM_PARAMS).fit(X, y)
    upper = HistGradientBoostingRegressor(loss="quantile", quantile=hi_q, categorical_features=mask, **GBM_PARAMS).fit(X, y)
    linear = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(enc.one_hot(fit), y)

    models = TrainedModels(enc, point, lower, upper, linear, float(y.mean()))
    models.conformal_margin_kg = _conformal_margin(models, calib)
    return models


# --------------------------------------------------------------------------- #
# Evaluation
# --------------------------------------------------------------------------- #
def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(mean_squared_error(y_true, y_pred) ** 0.5),
        "r2": float(r2_score(y_true, y_pred)),
    }


def evaluate(models: TrainedModels, test: pd.DataFrame) -> dict:
    """Headline metrics vs baselines, interval coverage and segment slices."""
    y = test[config.TARGET].to_numpy()
    preds = models.predict(test)
    yhat = preds["predicted_kg"].to_numpy()

    noise_floor = None
    if "true_noise_kg" in test:
        # The best any model can do on this simulator: predict signal exactly.
        signal = (test["true_contextual_kg"] + test["true_controllable_kg"]).to_numpy()
        noise_floor = _metrics(y, np.clip(signal, 0, None))

    lo_q, hi_q = config.INTERVAL_QUANTILES
    raw = models.predict(test, calibrated=False)
    covered_raw = (y >= raw["p10_kg"]) & (y <= raw["p90_kg"])
    covered = (y >= preds["p10_kg"]) & (y <= preds["p90_kg"])

    segment_rows = []
    for key in config.SEGMENT_KEYS:
        for level, idx in test.groupby(key).groups.items():
            m = _metrics(y[test.index.get_indexer(idx)], yhat[test.index.get_indexer(idx)])
            segment_rows.append({"segment_key": key, "segment": str(level), "n": len(idx), **m})

    imp = permutation_importance(
        models.point, models.encoder.transform(test), y,
        scoring="neg_mean_absolute_error", n_repeats=5, random_state=config.SEED,
    )
    importance = (
        pd.DataFrame({"feature": config.FEATURES, "importance_mae_kg": imp.importances_mean})
        .sort_values("importance_mae_kg", ascending=False)
        .reset_index(drop=True)
    )

    return {
        "n_test": int(len(test)),
        "test_window": [str(test["flight_date"].min())[:10], str(test["flight_date"].max())[:10]],
        "models": {
            "mean_baseline": _metrics(y, np.full_like(y, models.train_mean)),
            "ridge_baseline": _metrics(y, models.linear.predict(models.encoder.one_hot(test))),
            "gradient_boosting": _metrics(y, yhat),
            "noise_floor": noise_floor,
        },
        "interval": {
            "nominal_coverage": float(hi_q - lo_q),
            "raw_coverage": float(covered_raw.mean()),
            "calibrated_coverage": float(covered.mean()),
            "conformal_margin_kg": float(models.conformal_margin_kg),
            "mean_width_kg": float(preds["interval_width_kg"].mean()),
        },
        "segments": segment_rows,
        "importance": importance,
    }


def train_and_evaluate(df: pd.DataFrame):
    """Convenience wrapper: temporal split -> fit -> evaluate."""
    train, test = temporal_split(df)
    models = fit_models(train)
    report = evaluate(models, test)
    report["n_train"] = int(len(train))
    report["train_window"] = [str(train["flight_date"].min())[:10], str(train["flight_date"].max())[:10]]
    return models, train, test, report
