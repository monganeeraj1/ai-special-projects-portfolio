from pathlib import Path
import json
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
import joblib

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "synthetic_flights.csv"
OUT = ROOT / "outputs"
MODEL_DIR = ROOT / "models"
OUT.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

df = pd.read_csv(DATA)

X = df.drop(columns=["avoidable_fuel_kg"])
y = df["avoidable_fuel_kg"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

model = HistGradientBoostingRegressor(
    max_depth=7,
    learning_rate=0.07,
    max_iter=250,
    random_state=42,
)
model.fit(X_train, y_train)

pred = model.predict(X_test)

metrics = {
    "mae": float(mean_absolute_error(y_test, pred)),
    "rmse": float(mean_squared_error(y_test, pred) ** 0.5),
    "r2": float(r2_score(y_test, pred)),
}

importance = permutation_importance(
    model,
    X_test,
    y_test,
    scoring="neg_mean_absolute_error",
    n_repeats=5,
    random_state=42,
)

importance_df = pd.DataFrame({
    "feature": X.columns,
    "importance": importance.importances_mean,
}).sort_values("importance", ascending=False)

scored = X_test.copy()
scored["actual_avoidable_fuel_kg"] = y_test.values
scored["predicted_avoidable_fuel_kg"] = pred

importance_df.to_csv(OUT / "feature_importance.csv", index=False)
scored.to_csv(OUT / "test_predictions.csv", index=False)
(OUT / "metrics.json").write_text(json.dumps(metrics, indent=2))
joblib.dump(model, MODEL_DIR / "fuel_opportunity_model.joblib")

print("MODEL METRICS")
for k, v in metrics.items():
    print(f"{k.upper()}: {v:.3f}")

print("\nTOP FEATURES")
print(importance_df.head(10).to_string(index=False))
