from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

rng = np.random.default_rng(42)
n = 5000

df = pd.DataFrame({
    "distance_km": rng.uniform(300, 6500, n),
    "payload_tons": rng.uniform(20, 70, n),
    "departure_delay_min": rng.gamma(2, 8, n),
    "weather_severity": rng.uniform(0, 1, n),
    "aircraft_age_years": rng.uniform(1, 18, n),
    "taxi_time_min": rng.uniform(5, 45, n),
    "airport_congestion": rng.uniform(0, 1, n),
    "operational_complexity": rng.uniform(0, 1, n),
})

noise = rng.normal(0, 90, n)

df["excess_consumption_units"] = (
    0.018 * df["distance_km"]
    + 1.5 * df["payload_tons"]
    + 3.8 * df["departure_delay_min"]
    + 190 * df["weather_severity"]
    + 6.0 * df["aircraft_age_years"]
    + 5.5 * df["taxi_time_min"]
    + 150 * df["airport_congestion"]
    + 120 * df["operational_complexity"]
    + noise
)

X = df.drop(columns=["excess_consumption_units"])
y = df["excess_consumption_units"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.25, random_state=42
)

model = HistGradientBoostingRegressor(max_depth=6, learning_rate=0.08, random_state=42)
model.fit(X_train, y_train)

pred = model.predict(X_test)

mae = mean_absolute_error(y_test, pred)
rmse = mean_squared_error(y_test, pred) ** 0.5
r2 = r2_score(y_test, pred)

print("MODEL PERFORMANCE")
print(f"MAE:  {mae:.2f}")
print(f"RMSE: {rmse:.2f}")
print(f"R²:   {r2:.3f}")

imp = permutation_importance(
    model, X_test, y_test, n_repeats=5, random_state=42, scoring="neg_mean_absolute_error"
)
importance = pd.DataFrame({
    "feature": X.columns,
    "importance": imp.importances_mean,
}).sort_values("importance", ascending=False)

print("\nPERMUTATION IMPORTANCE")
print(importance.to_string(index=False))

scored = X_test.copy()
scored["actual"] = y_test.values
scored["predicted"] = pred
scored["priority"] = pd.qcut(scored["predicted"], 10, labels=False, duplicates="drop")

top_decile = scored[scored["priority"] == scored["priority"].max()]
share_of_total = top_decile["actual"].sum() / scored["actual"].sum()

print(f"\nShare of total excess consumption in top predicted decile: {share_of_total:.1%}")

out = Path(__file__).parent / "outputs"
out.mkdir(exist_ok=True)
importance.to_csv(out / "feature_importance.csv", index=False)
scored.to_csv(out / "scored_operations.csv", index=False)
