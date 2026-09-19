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

## Why the portfolio prototype uses gradient boosting

The purpose is not to maximize benchmark accuracy.

The purpose is to demonstrate:
- correct problem framing
- leakage discipline
- operational feature design
- evaluation
- explainability
- decision integration

## Train / test design

A production version should prefer **time-based validation** over random train/test splits when deployment predicts future operations.

Random splitting can overstate performance if temporal patterns leak across the split.

## Explainability

Useful methods include:
- permutation importance
- SHAP values
- partial dependence
- local explanations

But explanation should answer an operational question.

"Feature X mattered" is weaker than:

> "For this prediction, taxi time and APU usage were materially above the model's learned baseline, while weather and payload explain the remaining non-controllable component."

## Uncertainty

For high-impact decision support, the platform should distinguish:
- high-confidence opportunity
- low-confidence / out-of-distribution cases
- cases where no intervention should be recommended

Options include:
- quantile models
- conformal prediction
- ensemble variance
- distance / OOD heuristics
