from pathlib import Path
import numpy as np
import pandas as pd

rng = np.random.default_rng(42)
N = 12000

df = pd.DataFrame({
    "distance_km": rng.uniform(250, 7200, N),
    "payload_tons": rng.uniform(18, 72, N),
    "headwind_kts": rng.normal(5, 18, N),
    "temperature_c": rng.uniform(-5, 45, N),
    "aircraft_age_years": rng.uniform(1, 18, N),
    "taxi_out_min": rng.gamma(shape=4.0, scale=4.0, size=N) + 4,
    "departure_delay_min": rng.gamma(shape=2.0, scale=7.0, size=N),
    "cruise_speed_delta_pct": rng.normal(0, 1.8, N),
    "apu_minutes": rng.gamma(shape=2.2, scale=6.0, size=N),
    "route_efficiency_score": rng.uniform(0.78, 1.0, N),
})

noise = rng.normal(0, 80, N)

context_component = (
    0.014 * df["distance_km"]
    + 1.0 * df["payload_tons"]
    + 2.7 * np.maximum(df["headwind_kts"], 0)
    + 0.9 * np.maximum(df["temperature_c"] - 30, 0)
    + 4.0 * df["aircraft_age_years"]
)

controllable_component = (
    6.0 * np.maximum(df["taxi_out_min"] - 15, 0)
    + 2.8 * df["departure_delay_min"]
    + 45 * np.abs(df["cruise_speed_delta_pct"])
    + 5.0 * df["apu_minutes"]
    + 1100 * (1 - df["route_efficiency_score"])
)

df["avoidable_fuel_kg"] = np.maximum(
    0,
    0.30 * context_component + controllable_component + noise
)

out = Path(__file__).resolve().parents[1] / "data"
out.mkdir(exist_ok=True)
path = out / "synthetic_flights.csv"
df.to_csv(path, index=False)

print(f"Generated {len(df):,} synthetic flights")
print(f"Saved to {path}")
