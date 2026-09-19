# From Model Accuracy to Value Realization

## Value equation

A simple starting point:

```text
Annual value
=
Eligible operations
× Intervention rate
× Average avoidable fuel
× Realization rate
× Fuel value per unit
- Run cost
```

Each term should be independently challenged.

## Example value tree

### Opportunity pool
How much avoidable fuel exists?

### Detectability
What share can the model identify with acceptable precision?

### Actionability
What share of identified opportunity has a feasible operational intervention?

### Adoption
How often do operators use the recommendation?

### Realization
When acted upon, how much modeled opportunity is actually captured?

### Persistence
Does the improvement continue after the pilot period?

## Critical distinction

A 5% improvement in model RMSE may be economically irrelevant.

A smaller model improvement that increases **actionable top-k precision** can be much more valuable.

## Pilot design

A credible pilot should define:

### Baseline
Current fuel-performance distribution and intervention process.

### Test population
Routes / fleet / operating contexts where the signal is reliable and intervention is feasible.

### Outcome
Fuel impact adjusted for relevant context.

### Adoption metric
Percentage of eligible recommendations acted on.

### Decision gate
Scale only if technical quality, operator adoption, and realized economics all clear minimum thresholds.

## Benefits governance

Finance should validate the value methodology before scale.

This prevents the AI team from becoming the sole owner of both the model and the claimed savings.
