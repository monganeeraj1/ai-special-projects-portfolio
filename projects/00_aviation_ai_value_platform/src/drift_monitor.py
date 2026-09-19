from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = pd.read_csv(ROOT / "data" / "synthetic_flights.csv")

def psi(expected, actual, bins=10):
    breaks = np.quantile(expected, np.linspace(0, 1, bins + 1))
    breaks = np.unique(breaks)

    expected_counts, _ = np.histogram(expected, bins=breaks)
    actual_counts, _ = np.histogram(actual, bins=breaks)

    expected_pct = expected_counts / max(expected_counts.sum(), 1)
    actual_pct = actual_counts / max(actual_counts.sum(), 1)

    expected_pct = np.clip(expected_pct, 1e-6, None)
    actual_pct = np.clip(actual_pct, 1e-6, None)

    return np.sum(
        (actual_pct - expected_pct) * np.log(actual_pct / expected_pct)
    )

split = int(len(DATA) * 0.70)
baseline = DATA.iloc[:split].copy()
current = DATA.iloc[split:].copy()

# Simulate a distribution shift in one controllable feature.
current["taxi_out_min"] = current["taxi_out_min"] * 1.20

features = [
    "distance_km",
    "payload_tons",
    "taxi_out_min",
    "apu_minutes",
    "route_efficiency_score",
]

print("POPULATION STABILITY INDEX")
for feature in features:
    score = psi(baseline[feature], current[feature])
    flag = "REVIEW" if score >= 0.20 else "OK"
    print(f"{feature:25s} PSI={score:.3f}  {flag}")
