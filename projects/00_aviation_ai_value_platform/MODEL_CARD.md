# Model Card — Aviation Fuel Opportunity Model

## Model summary

**Model name:** Aviation Fuel Opportunity Model  
**Model type:** Gradient-boosted regression  
**Portfolio status:** Synthetic technical reconstruction  
**Primary output:** Predicted avoidable fuel opportunity per flight (kg)  
**Intended use:** Decision support for prioritizing operational fuel-efficiency review  
**Not intended for:** Automated flight-control decisions, safety-critical automation, crew performance scoring, or unreviewed financial attribution

> This model is a portfolio reconstruction using synthetic data. It is not a production airline model and does not represent proprietary client logic.

---

## 1. Problem definition

The model estimates where flight-level operations exhibit patterns associated with elevated avoidable fuel consumption.

The downstream decision is not:

> "Is this flight inefficient?"

It is:

> "Is there sufficient evidence of a material, actionable fuel-efficiency opportunity to justify operational review?"

That distinction drives the architecture: prediction is separated from recommendation and intervention.

---

## 2. Inputs

### Contextual / largely uncontrollable

- distance
- payload
- headwind
- outside temperature
- aircraft age

These features help establish expected operating context but are not necessarily intervention levers.

### Potentially controllable

- taxi-out time
- departure delay
- cruise-speed deviation
- APU usage
- route-efficiency score

These may support intervention hypotheses, subject to operational and causal validation.

---

## 3. Target

**Synthetic target:** `avoidable_fuel_kg`

The target is designed to approximate excess fuel consumption above a contextual baseline.

### Production challenge

Target construction would require alignment across:

- flight operations
- engineering
- fuel-efficiency specialists
- analytics
- finance

Poor target design can create a technically accurate model that optimizes the wrong quantity.

---

## 4. Training approach

Portfolio prototype:

- synthetic tabular dataset
- gradient-boosted regression
- train/test holdout
- MAE, RMSE, R²
- permutation importance

### Production recommendation

Prefer:

- temporal validation
- route / fleet segmentation
- backtesting across seasons
- out-of-distribution testing
- calibration of uncertainty
- prospective pilot validation

Random train/test splits are useful for a prototype but can overstate real-world performance in a changing operating environment.

---

## 5. Current synthetic benchmark

| Metric | Result |
|---|---:|
| MAE | 66.06 kg |
| RMSE | 82.90 kg |
| R² | 0.609 |

These results are synthetic and illustrative.

The model is intentionally not presented as "high accuracy = success." The relevant question is whether the model improves the precision and economics of real operational interventions.

---

## 6. Explainability

The prototype uses permutation importance for global analysis.

For production, I would add:

- SHAP for local and global explanation
- confidence / uncertainty bands
- contextual baseline comparison
- controllable vs non-controllable contribution
- reason codes suitable for operators

Example operator-facing explanation:

> "This flight is prioritized because taxi-out time, APU usage, and route-efficiency signals are materially above comparable operating context. Weather and payload explain part of the remaining predicted excess."

---

## 7. Decision policy

Model output does not trigger an automatic operational action.

The decision layer considers:

1. predicted fuel opportunity
2. whether controllable levers are present
3. confidence / out-of-distribution status
4. operational constraints
5. expected intervention value
6. human review

---

## 8. Known limitations

- synthetic target construction
- simplified feature space
- no temporal sequence modeling
- no aircraft-tail-specific effects
- no route-level hierarchical model
- no causal intervention model
- no explicit uncertainty calibration in current prototype
- no production data-quality pipeline
- no live operator feedback loop

---

## 9. Risk considerations

### Automation bias
Operators may over-trust a high model score.

**Control:** explanations, confidence, review requirements, and override capture.

### Data leakage
Features unavailable at decision time can falsely inflate offline performance.

**Control:** explicit point-in-time feature contract.

### Distribution shift
Fleet, route, season, procedures, and airport operations change.

**Control:** drift monitoring, segmented performance, retraining triggers.

### Proxy / fairness risk
Operational variables can unintentionally proxy for teams, stations, or personnel.

**Control:** prohibit people-performance use without a separate governance and validation process.

### Value misattribution
Fuel savings can be claimed where weather, network, or unrelated operational changes drove the outcome.

**Control:** independent benefits methodology and controlled pilot design.

---

## 10. Go-live criteria

A production deployment should require all of the following:

- technical metrics above agreed threshold
- stable performance across material segments
- acceptable uncertainty / abstention behavior
- no critical leakage findings
- operator usability validated
- intervention precision demonstrated
- finance-approved value methodology
- monitoring and rollback live
- accountable business owner named
