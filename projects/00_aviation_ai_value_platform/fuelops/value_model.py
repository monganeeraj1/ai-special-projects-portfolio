"""Value model: from a ranked queue to an annual net-value range.

    value = flights x eligible x prioritised x adoption x realisation
            x avg controllable kg x value per kg  -  run cost

Every factor is illustrative. The point of the model is the *shape*: the
model's job ends at "prioritised"; adoption and realisation are operating
outcomes that the program has to earn, and they are where most AI value is
lost. See VALUE_MODEL.md for the argument.

When pipeline results are supplied, the "pipeline-informed" scenario replaces
the guessed `avg_controllable_kg` and `prioritised_share` with what the
decision engine actually produced on the held-out window.
"""
from __future__ import annotations

import pandas as pd

SCENARIOS = [
    {"scenario": "Downside", "annual_flights": 160_000, "eligible_share": 0.40, "prioritised_share": 0.10,
     "adoption_rate": 0.55, "realisation_rate": 0.35, "avg_controllable_kg": 400, "value_per_kg_aed": 2.0,
     "annual_run_cost_aed": 2_500_000},
    {"scenario": "Base", "annual_flights": 180_000, "eligible_share": 0.50, "prioritised_share": 0.10,
     "adoption_rate": 0.70, "realisation_rate": 0.50, "avg_controllable_kg": 500, "value_per_kg_aed": 2.5,
     "annual_run_cost_aed": 2_500_000},
    {"scenario": "Upside", "annual_flights": 200_000, "eligible_share": 0.55, "prioritised_share": 0.10,
     "adoption_rate": 0.80, "realisation_rate": 0.60, "avg_controllable_kg": 600, "value_per_kg_aed": 3.0,
     "annual_run_cost_aed": 2_500_000},
]


def value_table(pipeline_policy: dict | None = None) -> pd.DataFrame:
    rows = list(SCENARIOS)
    if pipeline_policy is not None:
        base = dict(SCENARIOS[1])
        base.update({
            "scenario": "Base (pipeline-informed)",
            "prioritised_share": pipeline_policy["k_fraction"],
            "avg_controllable_kg": round(pipeline_policy["policies"]["controllable_attribution"]["mean_true_controllable_kg"]),
        })
        rows.append(base)

    df = pd.DataFrame(rows)
    df["fuel_saved_kg"] = (
        df["annual_flights"] * df["eligible_share"] * df["prioritised_share"]
        * df["adoption_rate"] * df["realisation_rate"] * df["avg_controllable_kg"]
    )
    df["gross_value_aed"] = df["fuel_saved_kg"] * df["value_per_kg_aed"]
    df["net_value_aed"] = df["gross_value_aed"] - df["annual_run_cost_aed"]
    return df


if __name__ == "__main__":
    print(value_table().to_string(index=False))
    print("\nAll assumptions are illustrative; none are client figures.")
