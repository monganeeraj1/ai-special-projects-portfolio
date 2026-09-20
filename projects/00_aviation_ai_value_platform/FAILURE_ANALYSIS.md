# Failure Analysis

## Why this matters

A model can look strong in aggregate while failing in precisely the cases that matter operationally.

For an AI-enabled fuel-efficiency platform, I would treat failure analysis as a formal workstream rather than a post-launch debugging exercise.

---

## Failure taxonomy

| Failure mode | Example | Why it matters | Control / test |
|---|---|---|---|
| Data leakage | Post-flight variable used in pre-flight recommendation | Inflated offline accuracy | Point-in-time feature audit |
| Missing context | Diversion / abnormal operation not encoded | False opportunity signal | Exception taxonomy |
| OOD operation | New route / aircraft type | Unreliable prediction | OOD detection + abstention |
| Seasonal drift | Summer operating profile changes | Performance degradation | Segment monitoring |
| Spurious correlation | Station effect mistaken for controllable driver | Wrong intervention | Causal / domain review |
| Recommendation overload | Too many flagged flights | Low adoption | Top-k policy |
| Weak actionability | High prediction, no feasible lever | Wasted operator effort | Controllability layer |
| Automation bias | Operator follows weak recommendation | Operational risk | Human review + confidence |
| Benefit overclaim | Savings attributed without counterfactual | Bad investment decisions | Finance-owned methodology |
| Feedback bias | Only accepted recommendations generate outcomes | Biased retraining data | Capture rejects + reasons |

---

# Residual analysis

Model error should be segmented rather than viewed only as one RMSE.

Important cuts:

- route family
- aircraft / fleet
- airport
- season
- weather regime
- delay band
- payload band
- high vs low predicted opportunity
- actionable vs contextual cases

Questions:

1. Where does the model systematically under-predict?
2. Where does it systematically over-predict?
3. Are errors concentrated in rare but high-value contexts?
4. Is performance worse precisely where interventions are most expensive?
5. Does model confidence correlate with actual error?

---

# False-positive analysis

A false positive has a real cost because an operator must investigate it.

For each high-priority false positive:

- Was the input data wrong?
- Was relevant context absent?
- Was the model wrong?
- Was the model technically right but the intervention impossible?
- Was the target / baseline definition wrong?
- Did the operator have information unavailable to the model?

This analysis often identifies product and data improvements faster than generic model tuning.

---

# False-negative analysis

False negatives represent missed fuel opportunity.

Prioritise analysis of:

- highest realised excess missed by the model
- recurring missed route patterns
- recurring airport / taxi patterns
- changes in operational procedures
- missing features suggested by subject-matter experts

---

# Counterfactual challenge

The most dangerous failure is:

> The model predicts excess correctly, but the proposed intervention does not actually change the outcome.

That is not a prediction failure. It is a **causal reasoning failure**.

Mitigation:

- separate predictive variables from intervention levers
- validate intervention hypotheses with domain experts
- use controlled pilots where practical
- measure incremental impact
- introduce uplift / causal modelling only when the data and intervention design support it

---

# Red-team scenarios

Before scaling, I would explicitly test:

### Scenario 1 — Extreme weather
Does the model incorrectly recommend operational actions when the excess is mostly weather-driven?

### Scenario 2 — New route
Does the system abstain when the route is outside its training distribution?

### Scenario 3 — Data feed degradation
What happens when APU or taxi data is delayed, missing, or stale?

### Scenario 4 — Mass recommendation event
Can an airport disruption generate thousands of alerts and overwhelm operators?

### Scenario 5 — Model / business conflict
What happens when the model recommends an action that contradicts an operational constraint?

### Scenario 6 — Apparent savings with poor counterfactual
Can the platform distinguish true intervention impact from natural regression to the mean?

---

# Failure-review cadence

## Daily / operational
- data incidents
- abnormal prediction volume
- recommendation failures

## Weekly
- top false positives
- top missed opportunities
- operator rejection reasons

## Monthly
- segment performance
- drift
- realised vs modeled value
- model / rule changes

## Quarterly / major change
- full model-risk review
- retraining decision
- operating-model review
