# 02 — Predictive Operations AI + Decision Optimization

## Executive question

**How do you move from an ML prediction to an operational intervention that creates measurable value?**

This project uses synthetic operations data to predict excess resource consumption and prioritize interventions.

The specific dataset is synthetic and does not contain client or airline data.

## Why this case matters

Many AI projects stop at:
> “The model achieved an RMSE of X.”

That is not enough.

The real chain is:

```text
Prediction
   ↓
Decision threshold
   ↓
Recommended intervention
   ↓
Operational workflow
   ↓
Behavior / process change
   ↓
Measured economic value
```

## Model

The prototype uses gradient-boosted regression to estimate excess consumption.

Features include:
- route distance
- payload
- delay
- weather proxy
- aircraft age
- taxi time
- congestion
- operational complexity

## Evaluation

Technical:
- MAE
- RMSE
- R²
- feature importance

Operational:
- precision of top-risk cases
- value captured in top-decile interventions
- false-positive operational burden

## Important AI principle

Prediction is not causality.

A feature associated with excess consumption is not automatically a valid intervention lever.

Operational recommendations require:
- domain validation
- causal reasoning
- controlled pilots
- before/after measurement
