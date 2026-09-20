# Model Card — Fuel Opportunity Model

## Model summary

**Model name:** Fuel Opportunity Model
**Model type:** Gradient-boosted regression (point) + two gradient-boosted quantile models (p10, p90) with split-conformal calibration
**Portfolio status:** Independent technical reconstruction, trained on a disclosed simulator
**Primary output:** Predicted avoidable fuel per flight (kg), an 80% prediction interval, and a counterfactual split into controllable and contextual components by lever
**Intended use:** Decision support for prioritising operational fuel-efficiency review
**Not intended for:** Automated flight-control decisions, safety-critical automation, crew performance scoring, or unreviewed financial attribution

> Client data, production results and proprietary model logic from the engagement are confidential and are not shown. Every number in this card comes from the simulator in `fuelops/synthetic_data.py` and describes the method, not an airline.

---

## 1. Problem definition

The model estimates where flight-level operations exhibit patterns associated with elevated avoidable fuel consumption.

The downstream decision is not:

> "Is this flight inefficient?"

It is:

> "Is there sufficient evidence of a material, **controllable** fuel-efficiency opportunity to justify operational review?"

That distinction drives the architecture: prediction, attribution and intervention are separate steps with separate tests.

---

## 2. Inputs

The feature contract is a single list in `fuelops/config.py`. A test fails if any ground-truth column ever enters it.

### Contextual / largely uncontrollable
distance, payload, headwind, outside temperature, aircraft age, calendar month, departure station, aircraft type

These establish expected operating context. They are not intervention levers.

### Controllable levers (measured as excess over an operating benchmark)
taxi-out time (benchmark 12 min), departure delay (0), cruise-speed deviation (0%), APU minutes (8), route-efficiency score (1.0)

Benchmarks are constants here so the attribution can be validated. In production they would be segment-specific operating targets agreed with flight operations.

### Deliberately excluded
`route_family` (derived from distance; used only to slice evaluation) and every `true_*` simulator column.

---

## 3. Target and data-generating process

**Target:** `avoidable_fuel_kg` — fuel above a contextual baseline.

The simulator is disclosed in full because a hidden one would make every result below unfalsifiable:

```text
avoidable_fuel_kg = contextual(x) + controllable(x) + noise

contextual   = f(distance, payload, headwind, heat, age, station, season)
               with a distance × payload interaction
controllable = Σ lever_excess × rate × interaction
               taxi excess costs more on heavy aircraft
               APU excess costs more in heat
               cruise and routing deviations scale with sector length
noise        ~ N(0, 40 + 0.012 × distance)   (heteroscedastic)
```

Lever distributions are right-skewed on purpose: most flights operate near benchmark and a minority carry most of the excess. On the pipeline run (24,000 flights, 24 months): mean target 746 kg, controllable share 35%, R² ceiling 0.91.

**Why this matters for the numbers below:** the benchmark cannot be "good" or "bad" in isolation. It is judged against the noise floor the simulator imposes and against baselines fitted on the same data.

### Production challenge
Target construction on real data would require alignment across flight operations, engineering, fuel-efficiency specialists, analytics and finance. Poor target design creates a technically accurate model that optimises the wrong quantity.

---

## 4. Validation design

| Choice | Prototype | Why |
|---|---|---|
| Split | **Temporal**: train Jan 2023 – Jun 2024, test Jul – Dec 2024 | Random splits leak seasonal structure and overstate performance for a system that predicts the future |
| Calibration | Last 20% of the training period, unseen by the quantile models | Split-conformal guarantees need genuinely held-out data |
| Baselines | Mean predictor; ridge regression on one-hot features | The model is reported as lift, never alone |
| Ceiling | Noise floor: a model that knows the simulator's signal exactly | Nothing can beat it; the gap to it is what the model has not learned |
| Slices | Route family, aircraft type, departure station | Aggregate error hides where a model fails |
| Structure check | Permutation importance | With a disclosed DGP it confirms recovery; it discovers nothing |

---

## 5. Benchmark (held-out window, 6,000 flights)

| Model | MAE (kg) | RMSE (kg) | R² |
|---|---:|---:|---:|
| Mean baseline | 238.7 | 294.3 | 0.000 |
| Ridge baseline | 97.9 | 135.9 | 0.787 |
| **Gradient boosting** | **72.8** | **95.5** | **0.895** |
| Noise floor (ceiling) | 67.9 | 88.8 | 0.909 |

Gradient boosting closes 84% of the gap between the linear baseline and the ceiling. Per-segment R² ranges 0.77 (long haul, where the noise is largest) to 0.90.

### Prediction intervals

| | Coverage of nominal 80% |
|---|---:|
| Raw quantile models | 71.2% |
| After split-conformal calibration | 79.9% |

Quantile models under-cover on a later window. The interval is calibrated on held-out data before the decision layer is allowed to use its width for abstention.

Live figures: [RESULTS.md](RESULTS.md), regenerated by `python -m fuelops`.

---

## 6. Attribution and explainability

The operator's question is not "which features matter to the model" but "how much of *this* flight's excess could we have avoided?". That is a counterfactual query against the fitted model:

```text
controllable_kg = f(x) − f(x with all five levers at benchmark)
contextual_kg   = f(x with all five levers at benchmark)
```

The controllable amount is split across levers with **exact Shapley values** (2⁵ = 32 model evaluations per flight, cheap enough to do exactly). Efficiency guarantees the lever credits sum to `controllable_kg`; a test enforces it to 1e-6.

Because the simulator's true split is known, the attribution is scored rather than trusted:

| Check | Value |
|---|---:|
| Correlation with true controllable kg | 0.973 |
| MAE of the controllable estimate | 32 kg |
| Controllable share: true / estimated | 35.3% / 31.9% (−3.3 pp) |
| Dominant lever identified correctly | 85.4% |

The estimate is **systematically conservative**. Tree ensembles extrapolate flatly at the benchmark edge of the training distribution, so the counterfactual under-states the controllable component. Here the bias is measured; in production it would be invisible, which is the argument for validating attribution with a designed pilot rather than assuming it.

Operator-facing explanation, as generated by the decision layer:

> Review: Taxi-out / ground congestion (~329 kg); Cruise-speed profile (~532 kg)

---

## 7. Decision policy

Model output never triggers an operational action. The decision layer, in order:

1. **Abstains** when any feature is outside the training range (+5% margin), a category is unseen, or the calibrated interval is more than 2× the median width → `review_low_confidence`
2. **Filters** to flights with controllable excess ≥ 300 kg and controllable share ≥ 30% → everything else is `no_action` or `no_action_contextual`
3. **Ranks** the remainder by controllable kg, not by total prediction
4. **Explains** with the dominant levers and the kg attributed to each

Measured on the held-out window against the same review capacity (top 10%):

| Ranking policy | Capture of controllable fuel | Actionable precision | Contextual share of reviewed excess |
|---|---:|---:|---:|
| Oracle (true controllable) | 22.8% | 100% | 49% |
| **Controllable attribution (this design)** | **22.4%** | **100%** | **49%** |
| Naive: total predicted | 20.2% | 84% | 58% |
| Random | 9.8% | 63% | 65% |

Ranking on the total prediction — the obvious policy — spends 58% of operator review on excess nobody can recover.

---

## 8. Monitoring

Three monitors with three different signatures, all exercised in the pipeline:

| Monitor | Statistic | Catches |
|---|---|---|
| Feature drift | PSI per feature vs a **season-matched** training reference | The operating population moved |
| Prediction drift | PSI on model output | Interactions shifted even if features look stable |
| Concept drift | z-test on mean residual once outcomes are known | The relationship changed, or the data feed did |

Injected scenarios: a +20% measurement change in recorded taxi-out registers only WATCH on feature PSI but z = −17 on residuals; a genuine route-efficiency degradation registers REVIEW on feature PSI with residuals near zero. Monitoring that watches only inputs misses the first; monitoring that watches only errors is late on the second.

---

## 9. Known limitations

- Constant benchmarks rather than segment-specific operating targets
- Counterfactuals near the edge of training support; conservative bias of ~3 pp measured on the simulator
- No temporal sequence modelling, tail-specific effects or route-level hierarchy
- No causal or uplift model: attribution is model-based, not intervention-validated
- Simulator features are independent of one another except through the disclosed interactions; real operational data has richer dependence
- No live operator feedback loop; rejection reasons and realised impact are designed for (`ARCHITECTURE_DEEP_DIVE.md`) but not simulated

---

## 10. Risk considerations

### Automation bias
Operators may over-trust a high model score.
**Control:** explanations by lever, calibrated intervals, review requirements, override capture.

### Data leakage
Features unavailable at decision time can falsely inflate offline performance.
**Control:** explicit point-in-time feature contract; a test that fails on ground-truth leakage.

### Distribution shift
Fleet, route, season, procedures and airport operations change.
**Control:** season-matched drift monitoring on features, predictions and residuals; retraining triggers; abstention.

### Proxy / fairness risk
Operational variables can unintentionally proxy for teams, stations or personnel.
**Control:** prohibit people-performance use without a separate governance and validation process.

### Value misattribution
Fuel savings can be claimed where weather, network or unrelated changes drove the outcome.
**Control:** independent benefits methodology and controlled pilot design; the value model shows adoption and realisation as explicit, dominant factors.

---

## 11. Go-live criteria

A production deployment should require all of the following:

- technical metrics above agreed thresholds **relative to baselines**, on temporal validation
- stable performance across material segments
- calibrated uncertainty with an agreed abstention policy
- no critical leakage findings
- attribution validated on a designed pilot, not on offline plausibility
- operator usability validated; intervention precision demonstrated
- finance-approved value methodology
- monitoring (feature, prediction, concept) and rollback live
- accountable business owner named
