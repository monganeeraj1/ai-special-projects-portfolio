# Model Design Notes

## Target

Illustrative target:

**avoidable_fuel_kg**

The target represents fuel consumption above an expected baseline after accounting for flight context.

In a real program, target construction is one of the hardest parts of the problem and requires close alignment between operations, engineering, analytics, and finance.

## Candidate model families

### Gradient-boosted trees
Strong baseline for tabular operational data:
- nonlinear relationships
- interactions
- limited preprocessing
- fast iteration
- interpretable with post-hoc methods

### Neural networks
Potentially useful when:
- very large datasets exist
- temporal / sequence behavior matters
- multimodal signals are included

### Causal / uplift models
Relevant when the objective moves from:
> "Where is excess fuel likely?"

to:
> "Which intervention is likely to reduce fuel for this specific context?"

## Why the prototype uses gradient boosting

The purpose is not to maximize benchmark accuracy.

The purpose is to demonstrate:
- correct problem framing
- leakage discipline (enforced by test)
- operational feature design
- evaluation against baselines and a known ceiling
- counterfactual attribution, validated
- decision integration

## Train / test design

The prototype uses **time-based validation**: the last six months are held out, and the last 20% of the training period is reserved to calibrate the prediction interval. Random splitting would let seasonal structure leak across the split and overstate performance for a system that predicts future operations.

## Explainability

Two different questions need two different tools:

| Question | Tool in the prototype |
|---|---|
| Did the model learn the structure it should have? | Permutation importance (a check, since the DGP is disclosed) |
| How much of *this* flight's excess is controllable, and by which lever? | Counterfactual against benchmark operations, split by exact Shapley values |

The second is what the operator needs. "Feature X mattered" is weaker than:

> "Review: Taxi-out / ground congestion (~329 kg); Cruise-speed profile (~532 kg)"

SHAP on the full feature set is the natural next step for a richer local explanation; it was not needed to answer the operational question here.

## Uncertainty

The prototype distinguishes:
- high-confidence opportunity → ranked
- low-confidence or out-of-distribution cases → abstained to review
- cases where no intervention should be recommended → filtered out

Implemented with p10/p90 quantile models plus a split-conformal margin. Raw quantile models covered 71% of a nominal 80% interval on the later window; calibration restored 80%. Alternatives not used here: ensemble variance, conformalised quantile regression with segment-conditional margins, distance-based OOD scores.
