# 00 — Airline AI Value & Operations Platform

**A validated prototype of an AI fuel-efficiency decision system, built from my experience advising a major airline's leadership on an AI initiative and structuring its implementation.**

[![CI](https://github.com/monganeeraj1/ai-strategy-transformation/actions/workflows/aviation-ai-ci.yml/badge.svg)](https://github.com/monganeeraj1/ai-strategy-transformation/actions/workflows/aviation-ai-ci.yml)

```bash
cd projects/00_aviation_ai_value_platform
pip install -r ../../requirements.txt -r ../../requirements-dev.txt
python -m pytest        # 42 tests, ~10 s
python -m fuelops       # full pipeline, ~10 s, regenerates RESULTS.md
```

---

## What is real and what is reconstructed

**Real:** I advised the airline's leadership on where AI could improve operational and fuel-efficiency decisions, structured the initiative from use-case identification through value case, requirements, decision-support design, governance and implementation roadmap, and supported the implementation. Client data, production results, proprietary model logic and internal materials are confidential and appear nowhere in this repository.

**Reconstructed:** everything that runs. The simulator, models, attribution, decision engine, drift monitor and tests were built independently to show the *method* at a level a technical reviewer can execute and challenge.

## Why a simulator — and why it is disclosed in full

Without client data, the honest options were a toy dataset or a simulator. A simulator with a disclosed data-generating process is the stronger choice for one reason: **it makes the method testable.**

Because the true controllable/contextual split of every flight is known, the pipeline can be *scored* on the questions that matter in production but are normally unanswerable offline:

| Question | How this project answers it |
|---|---|
| Is the model good, or just better than nothing? | Lift over mean and linear baselines, measured against the simulator's noise floor |
| Do prediction intervals mean what they say? | Empirical coverage on a later time window, before and after conformal calibration |
| Is the controllable/contextual attribution right? | Compared with ground truth: correlation, bias, dominant-lever accuracy |
| Does ranking on controllable excess beat ranking on the total? | Same review capacity, four policies, capture and precision |
| Will monitoring catch the failure modes in `FAILURE_ANALYSIS.md`? | Two injected drift scenarios with different signatures |

The corollary is stated plainly in every output: **no number here says anything about a real airline.** They say whether the method holds up under noise, interactions, segment effects and time.

## The pipeline

```text
fuelops/
  synthetic_data.py   simulator: contextual + controllable(levers, interactions) + heteroscedastic noise
                      ground truth written as true_* columns; excluded from the model by contract
  train.py            temporal split · mean/ridge baselines · gradient boosting
                      p10/p90 quantile models · split-conformal calibration · segment metrics
  attribution.py      counterfactual controllable excess  f(x) − f(x at benchmark ops)
                      exact Shapley values over the 5 levers (2^5 evaluations, sums exactly)
  decision_engine.py  abstain (OOD / wide interval) → filter (size, share) → rank → explain
                      scored against oracle, naive-total and random policies
  drift_monitor.py    PSI on features and predictions; residual z-test for concept drift
                      season-matched reference window; two injected scenarios
  value_model.py      annual value range; one row informed by the actual queue
  report.py           RESULTS.md is rendered from the numbers, never hand-edited
tests/                42 tests; run on a different seed and sample size than the pipeline
```

### Design decisions a reviewer should challenge

- **Temporal validation, not a random split.** The last six months are held out. Random splits leak seasonal structure and overstate performance for a system that predicts the future.
- **Baselines are reported, always.** The gradient-boosted model closes ~84% of the gap between a linear model and the noise floor. The remaining ~16% is what it has not learned, and that is stated.
- **Uncertainty is calibrated before it gates decisions.** Raw quantile models cover ~71% of a nominal 80% interval on the later window; a split-conformal margin from held-out calibration data restores ~80%.
- **Attribution is a counterfactual query, not feature importance.** "How much would the model expect us to save at benchmark operations?" is a different question from "which features matter?", and it is the one the decision layer needs.
- **The attribution's bias is measured and explained.** Tree ensembles extrapolate flatly at the benchmark edge of the data, so the controllable component is under-stated by ~3 pp. In production that bias would be invisible, which is the argument for validating attribution on a designed pilot.
- **Ranking on the total prediction is the trap.** It sends operators to long, heavy, headwind-bound flights whose excess is mostly contextual. Ranking on attributed controllable excess reaches ~98% of the oracle's capture with 100% actionable precision on the same review capacity.
- **Two drift scenarios, two signatures.** A measurement-definition change barely moves feature PSI and is caught by residuals; a genuine operational change is loud on features and silent on residuals. Monitoring that watches only one of those misses half the failure modes.
- **Abstention is a first-class outcome.** Out-of-range features or an unusually wide interval route a flight to review rather than into the ranking.
- **Leakage discipline is a test, not a convention.** `tests/test_synthetic_data.py` fails if any ground-truth column ever enters the feature contract.

### Known limitations of the prototype

- Benchmarks for "controllable" are constants; production would use segment-specific operating targets agreed with flight operations.
- Counterfactuals at benchmark sit near the edge of the training support; the resulting conservative bias is measured here and would need a pilot design in production.
- No tail-specific, route-hierarchical or sequence effects; no causal/uplift model. Those are the next steps described in `model_design.md`, not claims.
- The value model's adoption and realisation rates are operating assumptions, and they dominate the answer. That is the point of showing them.

## Review path

1. **[RESULTS.md](RESULTS.md)** — every number the pipeline produces, with what it does and does not mean.
2. **[MODEL_CARD.md](MODEL_CARD.md)** — intended use, target, validation design, benchmark, limitations, risks, go-live criteria.
3. **[FAILURE_ANALYSIS.md](FAILURE_ANALYSIS.md)** — leakage, OOD, false positives/negatives, causal failure, red-team scenarios.
4. **[ARCHITECTURE_DEEP_DIVE.md](ARCHITECTURE_DEEP_DIVE.md)** — feature pipeline, registry, decision layer, human review, monitoring, value loop.
5. **[VALUE_MODEL.md](VALUE_MODEL.md)** — how prediction quality converts, or fails to convert, into realised value.
6. **[IMPLEMENTATION_PLAYBOOK.md](IMPLEMENTATION_PLAYBOOK.md)** — the delivery sequence, governance cadence and stage gates from the engagement.

Additional notes: [reference architecture](architecture.md) · [model design choices](model_design.md) · [value realisation logic](value_case.md) · [monitoring & governance](monitoring_and_governance.md).

## Executive framing

The question the engagement answered was not "can we predict excess fuel?" It was:

> **Can the airline identify where excess fuel is controllable, act on it inside real operating workflows, and measure the value it actually recovers?**

The value chain — and the places it breaks — is what this prototype is built to expose:

```text
operational data → features → model → calibrated uncertainty
   → controllable-lever attribution → prioritised, explained queue
   → human decision → measured fuel impact → feedback into model and process
```

A model that is right about the total and wrong about what is controllable produces a queue nobody can act on. A queue nobody acts on produces no value. Adoption and realisation, not accuracy, are where AI programs are usually lost.
