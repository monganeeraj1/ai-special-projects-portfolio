# Synthetic Benchmark Results

These results come from the portfolio's **synthetic** flight dataset and illustrative model. They are not production airline results.

## Model performance

| Metric | Result |
|---|---:|
| MAE | 66.06 kg |
| RMSE | 82.90 kg |
| R² | 0.609 |

The intent is deliberately not to create an unrealistically perfect model. Operational AI should be evaluated on whether imperfect predictions can still support better decisions and measurable value.

## Most influential features

Permutation importance in the synthetic benchmark:

| Rank | Feature | Relative importance |
|---:|---|---:|
| 1 | Route efficiency score | 36.68 |
| 2 | Cruise speed deviation | 17.92 |
| 3 | APU minutes | 15.63 |
| 4 | Taxi-out time | 15.21 |
| 5 | Departure delay | 6.74 |

Contextual variables such as headwind, route distance, aircraft age, payload, and temperature contribute to the prediction but are intentionally less actionable in the intervention layer.

## Decision-layer result

After adding controllability to the prioritization logic:

- the top 10% of prioritized cases captured **14.9% of total synthetic avoidable-fuel opportunity**
- **100%** of those top-priority cases contained at least one flagged controllable operational lever

This is an example of why the portfolio separates:

**prediction quality → actionability → operational value**

A production system would require temporal validation, route/fleet segmentation, causal validation of interventions, financial benefit verification, and live operational testing.
