# AI Investment & Value Model

## Purpose

The model translates AI technical performance into a business-value chain.

The key idea is:

> Model accuracy does not create value by itself.

Value is only realized when an identified opportunity is **eligible, actionable, adopted, and effective**.

---

# Value equation

```text
Fuel saved
=
Annual flights
× Eligible share
× Prioritized share
× Adoption rate
× Realization rate
× Average avoidable fuel per prioritized flight

Gross value
=
Fuel saved × value per kg

Net annual value
=
Gross value - annual run cost
```

**Actual client economics and realized benefits are confidential and are not shown.** The scenario values below are reconstructed to demonstrate the value-driver logic and sensitivity approach.

---

# Scenario analysis

| Scenario | Fuel saved | Gross annual value | Annual run cost | Net annual value |
|---|---:|---:|---:|---:|
| Downside | 554,400 kg | AED 1.11M | AED 2.50M | **AED -1.39M** |
| Base | 2,520,000 kg | AED 6.30M | AED 2.50M | **AED 3.80M** |
| Upside | 5,940,000 kg | AED 17.82M | AED 2.50M | **AED 15.32M** |

---

# Why the downside case matters

The downside case is deliberately negative.

That illustrates a core AI investment principle:

> A technically successful model can still be a bad investment.

The program can fail economically if:

- too few flights are truly addressable
- the decision policy is too conservative
- operators do not adopt recommendations
- modeled opportunity does not translate into realized savings
- run costs are too high

---

# Sensitivities I would test

## Adoption

If recommendation adoption falls, value can collapse even with unchanged model performance.

Questions:
- Are recommendations understandable?
- Are they operationally feasible?
- Do users trust the system?
- Are incentives aligned?

## Realization

A predicted opportunity may not be fully recoverable.

Questions:
- Does the intervention causally affect fuel use?
- Are operational constraints binding?
- Does performance persist?

## Prioritization

The model does not need to act on every flight.

Questions:
- What top-k threshold maximizes net value?
- When does operator burden outweigh additional captured opportunity?

## Cost per kg

Fuel economics change.

A scalable platform should make the business case robust to input-price sensitivity rather than depend on a single price assumption.

---

# Investment decision framework

I would recommend scale only when all four are demonstrated:

### 1. Technical
The model generalizes and has acceptable uncertainty.

### 2. Operational
Recommendations are actionable and adopted.

### 3. Causal / outcome
Interventions create measurable incremental impact.

### 4. Economic
Realized value exceeds full run cost at an acceptable margin.

---

# Why this belongs in an AI portfolio

This value model connects:

**AI metric → decision precision → adoption → intervention effect → financial value**

That is the bridge between a data-science prototype and an enterprise AI investment thesis.

Run:

```bash
python value_model.py
```
