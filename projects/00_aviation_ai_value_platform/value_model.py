import pandas as pd

SCENARIOS = [
    {
        "scenario": "Downside",
        "annual_flights": 160_000,
        "eligible_share": 0.40,
        "prioritized_share": 0.15,
        "adoption_rate": 0.55,
        "realization_rate": 0.35,
        "avg_avoidable_fuel_kg": 300,
        "value_per_kg_aed": 2.0,
        "annual_run_cost_aed": 2_500_000,
    },
    {
        "scenario": "Base",
        "annual_flights": 180_000,
        "eligible_share": 0.50,
        "prioritized_share": 0.20,
        "adoption_rate": 0.70,
        "realization_rate": 0.50,
        "avg_avoidable_fuel_kg": 400,
        "value_per_kg_aed": 2.5,
        "annual_run_cost_aed": 2_500_000,
    },
    {
        "scenario": "Upside",
        "annual_flights": 200_000,
        "eligible_share": 0.55,
        "prioritized_share": 0.25,
        "adoption_rate": 0.80,
        "realization_rate": 0.60,
        "avg_avoidable_fuel_kg": 450,
        "value_per_kg_aed": 3.0,
        "annual_run_cost_aed": 2_500_000,
    },
]

df = pd.DataFrame(SCENARIOS)

df["fuel_saved_kg"] = (
    df["annual_flights"]
    * df["eligible_share"]
    * df["prioritized_share"]
    * df["adoption_rate"]
    * df["realization_rate"]
    * df["avg_avoidable_fuel_kg"]
)

df["gross_value_aed"] = df["fuel_saved_kg"] * df["value_per_kg_aed"]
df["net_value_aed"] = df["gross_value_aed"] - df["annual_run_cost_aed"]

print(
    df[
        [
            "scenario",
            "fuel_saved_kg",
            "gross_value_aed",
            "annual_run_cost_aed",
            "net_value_aed",
        ]
    ].to_string(index=False)
)

print("\nImportant: all assumptions are illustrative portfolio assumptions, not client figures.")
