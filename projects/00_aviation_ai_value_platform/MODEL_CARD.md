# Model card — fuel opportunity model

A model card is a governance artefact, not a technical one. Its job is to make
it hard for an organisation to deploy something without having answered the
questions below — which is why writing one early, before anybody is invested
in a launch date, is worth more than writing a good one late.

This card is a portfolio reconstruction for the fuel-opportunity use case.
It is written at the level of decisions and evidence rather than of a
particular fitted model, because that is the level at which it is useful:
the questions below have to be answered whichever model the team ends up
building.

> Client data, production results and the airline's proprietary methods are
> confidential and are not shown. Thresholds stated here are design targets
> for an advisory pilot, not achieved results.

---

## 1. What it is for

**Intended use:** helping an operations team decide which flights are worth
reviewing for recoverable fuel, and telling them which lever to look at.

**Explicitly not intended for:** automated flight-control decisions, anything
safety-critical, crew or individual performance scoring, or financial
attribution that has not been through Finance.

The last two matter more than they look. A model that ranks flights can be
turned into a model that ranks crews by anyone with a pivot table, and the
protection against that is a governance decision taken in advance, not a
technical property of the model.

## 2. The question it answers

Not "is this flight inefficient?" but:

> "Is there enough evidence of a **recoverable** opportunity here to be worth
> an operator's time?"

That distinction drives the whole design. Prediction, the separation of
recoverable from contextual, and the decision to put a flight in front of a
human are three separate steps, and each can be wrong independently.

## 3. What it sees

**Context it cannot change:** sector distance, payload, headwind, temperature,
aircraft age.

**Levers an operator can change**, each measured against an operating
benchmark: taxi-out time (12 min), departure delay (0), APU minutes (8),
route efficiency (1.0).

**The benchmarks are the hard part, and they are not a modelling decision.**
They are negotiated with flight operations, and everything downstream inherits
whatever is agreed. A benchmark three minutes too generous does not make the
ranking wrong, but it does change how much recoverable fuel the programme
claims exists — which is the number that ends up in the business case.

**Deliberately excluded:** anything recorded after the decision point. A
feature that is only available once the flight has landed will improve an
offline metric and be useless in service. This is the most common way a
promising model dies in implementation, and it is a data-availability
question, not a modelling one.

## 4. How it was validated

| Choice | What was done | Why it matters |
|---|---|---|
| Split | By date — trained on the first 75%, tested on the last 25% | A random split lets the model see next summer while predicting last summer. It flatters the model and tells the programme nothing. |
| Baseline | A linear model on the same features | A model's error means nothing alone, only its distance from the simplest thing that works |
| Segments | Error reported by route, fleet, airport and operating regime | An acceptable average can hide a segment where the model is unusable |
| Uncertainty | Observed coverage of the stated interval, overall and on material segments | An interval labelled 80% that covers 70% is worse than no interval, because it will be trusted |
| The decision | Compared against ranking on total excess, and against the existing process | The only comparison that reflects what an operations team actually experiences |

The acceptance thresholds these imply are set out in
[delivery standards](https://monganeeraj1.github.io/ai-strategy-transformation/cases/delivery-standards.html#release).

## 5. The error to expect, and in which direction

A counterfactual estimate of the recoverable amount tends to run **low**. At
benchmark operations some flights sit at the edge of the training data, where
tree models flatten out, so the estimate under-states what could have been
saved.

Low is the safer direction — it sends fewer flights to review rather than
promising savings that are not there — but "conservative" is not the same as
"right", and in production the size of that error is invisible. The only way
to find out is a controlled pilot: act on a sample, measure what was actually
recovered, compare it with what was predicted.

## 6. Known limits

- Benchmarks set as constants rather than as segment-specific operating
  targets agreed per station and fleet
- Association, not causation. A model can learn that flights with long taxi
  times burn more fuel. It has not established that reducing taxi time at a
  given station is possible, who owns that change, or what it would cost.
- Attribution is model-based rather than intervention-validated until a pilot
  says otherwise
- No live operator feedback loop, so rejection reasons — the most useful
  signal a review process produces — are not yet reaching the model owners

## 7. Risks worth naming in advance

**Automation bias.** Operators come to trust a ranked list more than it
deserves. *Control:* every recommendation names its lever and its kg, so it
can be argued with; overrides are captured and read.

**Leakage.** A feature unavailable at the decision point inflates offline
performance. *Control:* an explicit point-in-time feature contract, agreed
with the data owners rather than inferred by the modelling team.

**Distribution shift.** Fleet, network, season and airport operations change.
*Control:* monitoring on inputs *and* on errors — they fail differently, and a
programme that watches only one misses half the failure modes.

**Proxy discrimination.** Operational variables can stand in for teams,
stations or individuals. *Control:* prohibit performance-management use
without a separate governance process. This is a policy, not a model setting.

**Value misattribution.** Savings get claimed that weather or network changes
actually produced. *Control:* a benefits methodology agreed with Finance
before launch, and a control group.

## 8. What has to be true before this goes live

- performance above an agreed threshold **relative to a baseline**, on a
  time-based validation, and stable across route families and fleet types
- no leakage findings outstanding
- the recoverable/contextual separation confirmed on a designed pilot, not on
  offline plausibility
- operators able to use the output in their actual workflow, demonstrated
  rather than assumed
- a benefits methodology Finance has signed
- monitoring and a rollback path live on day one
- a named business owner who is accountable for the outcome, not just for the
  model
