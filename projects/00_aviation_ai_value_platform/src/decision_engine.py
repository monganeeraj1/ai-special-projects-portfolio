from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PRED = ROOT / "outputs" / "test_predictions.csv"
OUT = ROOT / "outputs"

df = pd.read_csv(PRED)

def recommendation(row):
    levers = []

    if row["taxi_out_min"] > 22:
        levers.append("Review taxi-out / ground congestion opportunity")

    if row["apu_minutes"] > 18:
        levers.append("Review APU usage / ground-power opportunity")

    if abs(row["cruise_speed_delta_pct"]) > 2.0:
        levers.append("Review cruise-speed profile")

    if row["route_efficiency_score"] < 0.88:
        levers.append("Review route-efficiency opportunity")

    if row["departure_delay_min"] > 25:
        levers.append("Review delay-related operating impact")

    if row["predicted_avoidable_fuel_kg"] < 250:
        return "No priority action"

    if not levers:
        return "High predicted excess; primarily contextual — review before action"

    return " | ".join(levers)

df["recommendation"] = df.apply(recommendation, axis=1)
df["actionable"] = ~df["recommendation"].isin([
    "No priority action",
    "High predicted excess; primarily contextual — review before action",
])

df["priority_score"] = (
    df["predicted_avoidable_fuel_kg"]
    * (1 + 0.35 * df["actionable"].astype(int))
)

prioritized = df.sort_values("priority_score", ascending=False)

top_10pct_n = max(1, int(len(prioritized) * 0.10))
top = prioritized.head(top_10pct_n)

capture = (
    top["actual_avoidable_fuel_kg"].sum()
    / prioritized["actual_avoidable_fuel_kg"].sum()
)

actionable_share = top["actionable"].mean()

print(f"Opportunity captured in top 10% of prioritized cases: {capture:.1%}")
print(f"Actionable share within top 10%: {actionable_share:.1%}")

prioritized.to_csv(OUT / "prioritized_interventions.csv", index=False)
print("\nTop recommendations:")
print(
    prioritized[
        ["predicted_avoidable_fuel_kg", "priority_score", "recommendation"]
    ].head(12).to_string(index=False)
)
