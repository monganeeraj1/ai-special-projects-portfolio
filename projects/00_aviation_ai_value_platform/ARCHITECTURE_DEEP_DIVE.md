# Architecture Deep Dive

## Design objective

Build an AI decision-support capability that can identify fuel-efficiency opportunity, explain why it is being flagged, propose only feasible interventions, measure realised value, and remain governable as conditions change.

## The platform this document describes

The programme is building an end-to-end fuel-efficiency platform, not a single
model. At the level of its architecture it has four kinds of component, and
keeping their responsibilities apart is what makes each one separately
evaluable:

| Layer | Responsibility | Why it is separate |
|---|---|---|
| **Predictive** | Fuel prediction; anomaly detection on flight-level consumption | Returns an estimate *and* its uncertainty. Downstream logic needs both; a point estimate alone cannot support an abstention rule. |
| **Optimisation** | Flight optimisation combining classical ML with reinforcement-learning methods | Returns feasible candidate actions with objective values and constraint results. Improving the objective while breaching a hard limit is a failed recommendation, and only a separate constraint check can catch it. |
| **Agentic** | Agentic reasoning combined with the ML and RL components in the production system — composing evidence, routing recommendations to the people who act | An agent may select tools and summarise evidence. Fuel calculations and operational constraints stay in validated numerical services, outside the language model. |
| **Platform machinery** | Training, experimentation, evaluation, observability and deployment, on a model-agnostic design | Stable interfaces and versioned inputs and outputs are what allow a predictor, optimiser or language model to be replaced without changing what downstream users experience. |

This document describes responsibilities and the evidence each component owes,
not client infrastructure or a confirmed deployment. The release criteria,
guardrails and monitoring thresholds that follow from it are in
[delivery standards](https://monganeeraj1.github.io/ai-strategy-transformation/cases/delivery-standards.html).

## Logical architecture

```mermaid
flowchart TD
    A[Operational Source Systems] --> B[Ingestion & Data Quality]
    B --> C[Curated Operational Data]
    C --> D[Feature Pipeline / Feature Store]

    D --> E[Training Pipeline]
    E --> F[Experiment Tracking]
    F --> G[Model Registry]
    G --> H[Validation Gate]

    D --> I[Online / Batch Feature Build]
    H --> J[Model Serving]
    I --> J

    J --> K[Prediction + Uncertainty]
    K --> L[Explainability Layer]
    L --> M[Controllability / Policy Engine]

    M --> N{Actionable?}
    N -- No --> O[Observe / No Action]
    N -- Yes --> P[Prioritised Recommendation]

    P --> Q[Human Operational Review]
    Q --> R{Accept?}
    R -- No --> S[Capture Reject Reason]
    R -- Yes --> T[Operational Intervention]

    T --> U[Outcome Capture]
    S --> U
    O --> U

    U --> V[Benefits Measurement]
    U --> W[Model Monitoring]
    W --> X[Drift / Performance Alerts]
    X --> E

    V --> Y[Executive Value Dashboard]
```

---

# Layer-by-layer design

## 1. Data layer

Sources may include:

- flight operations
- planning / dispatch
- aircraft / fleet
- airport operations
- weather
- ground operations
- fuel / engineering records

### Key controls

- point-in-time correctness
- data lineage
- schema validation
- missingness monitoring
- late-arriving data policy
- source ownership

---

## 2. Feature layer

The feature contract should explicitly state:

- feature definition
- source
- refresh frequency
- availability time
- owner
- training / serving transformation
- acceptable missingness

This prevents training-serving skew and data leakage.

---

## 3. Model lifecycle

```text
Experiment
→ validation
→ model registry
→ approval
→ deployment
→ monitoring
→ retraining / rollback
```

Production artifacts should include:

- model version
- training window
- feature version
- metrics
- segment performance
- model card
- approval record

---

## 4. Decision layer

This is deliberately separate from the model.

The model predicts **opportunity**.

The decision layer incorporates:

- controllability
- policy
- operational constraints
- value threshold
- confidence
- intervention capacity

This separation allows operations policy to change without unnecessary model retraining.

---

## 5. Human-in-the-loop

The user interface should show:

- predicted opportunity
- confidence
- top contributing factors
- controllable levers
- proposed action
- estimated value
- relevant context

The operator can:

- accept
- modify
- reject
- record reason

That feedback becomes part of the product-learning loop.

---

## 6. Monitoring

### Data
- missingness
- distribution shift
- schema change

### Model
- MAE / RMSE
- residual drift
- segment degradation
- confidence distribution

### Decision
- actionable rate
- acceptance rate
- override rate
- false-positive workload

### Value
- modeled opportunity
- acted opportunity
- realised savings
- benefit persistence

---

## 7. Deployment pattern

For many operational use cases, **batch or near-real-time scoring** may be more appropriate than low-latency online inference.

Architecture should be driven by decision timing, not by a desire to make the system "real time."

---

# Key trade-offs

## Accuracy vs interpretability
A modest model with clear operational logic may create more value than a marginally stronger black-box model.

## Model complexity vs maintainability
A complex ensemble may not justify itself if operations change frequently.

## Alert volume vs capture
Lower thresholds capture more opportunity but increase operator burden.

## Automation vs control
More autonomy can reduce friction but increases operational and governance risk.

## Central platform vs use-case-specific stack
Reusable capabilities create scale, but over-standardisation can constrain use cases with different latency, risk, or data requirements.
