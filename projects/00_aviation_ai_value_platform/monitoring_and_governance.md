# Monitoring & Governance

## Model monitoring

Track:
- input drift
- prediction drift
- residual drift
- error by route / fleet / season
- missingness
- out-of-range features
- intervention acceptance

## Business monitoring

Track:
- identified opportunity
- actionable opportunity
- actions taken
- realized savings
- false-positive workload
- operator overrides
- reasons for rejection

## Retraining triggers

Possible triggers:
- PSI above threshold
- sustained degradation in MAE / RMSE
- fleet change
- route-network change
- operational procedure change
- major data-source change

## Governance

### AI / data team
Owns model development, validation, monitoring, and technical documentation.

### Operations
Owns intervention feasibility and workflow integration.

### Finance
Owns benefits methodology.

### Risk / governance
Owns model-risk standards, documentation requirements, and approval thresholds.

### Executive sponsor
Owns business outcome and scale decision.

## Human-in-the-loop principle

The appropriate design is usually **decision support**, not unconstrained automation.

The platform should:
- surface the prediction
- explain key contributing signals
- distinguish controllable from contextual drivers
- propose feasible interventions
- record the human decision
- learn from feedback
