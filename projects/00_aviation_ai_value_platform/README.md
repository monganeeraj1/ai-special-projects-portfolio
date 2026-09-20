# Airline fuel-efficiency AI programme — supporting documents

These are the working documents behind the case study. They are the artefacts I
would expect to exist on an AI programme before anyone is asked to approve a
release — written to be argued with rather than admired.

**Start with the case study itself:**
[The case](https://monganeeraj1.github.io/ai-strategy-transformation/cases/aviation-ai.html) ·
[Engagement walkthrough](https://monganeeraj1.github.io/ai-strategy-transformation/cases/inside-the-airline-engagement.html) ·
[Delivery standards](https://monganeeraj1.github.io/ai-strategy-transformation/cases/delivery-standards.html)

---

| Document | The question it forces someone to answer |
|---|---|
| [MODEL_CARD.md](MODEL_CARD.md) | What is this model for, what must it never be used for, how was it validated, where is it wrong, and what has to be true before it goes live? |
| [FAILURE_ANALYSIS.md](FAILURE_ANALYSIS.md) | How does this class of system fail — leakage, distribution shift, false positives, causal misreading — and what does each failure mode require of the design? |
| [VALUE_MODEL.md](VALUE_MODEL.md) | How does prediction quality convert, or fail to convert, into value Finance will recognise? |
| [IMPLEMENTATION_PLAYBOOK.md](IMPLEMENTATION_PLAYBOOK.md) | What is the delivery sequence, the governance cadence, and the evidence required at each stage gate? |
| [ARCHITECTURE_DEEP_DIVE.md](ARCHITECTURE_DEEP_DIVE.md) | Which component is responsible for what, and how does a recommendation get from data to an operator with its evidence intact? |

## Why a model card and a failure analysis belong to the consultant

The technical team will build a better model than I could. What tends to be
missing is not modelling skill — it is a written answer to *what would make us
stop*, agreed before anybody is invested in a launch date.

A model card written early is cheap and awkward. Written late it is a
formality. The same is true of a failure analysis: naming how the system will
fail while the design can still change is worth more than discovering it in
shadow operation.

## What is experience and what is reconstruction

The engagement and consulting scope are experience based. These documents are
portfolio reconstructions: they demonstrate the analytical approach without
reproducing client data, internal architecture, implementation status or
production results, all of which remain confidential.

Numbers that appear as targets — coverage thresholds, precision levels,
latency budgets — are design targets for an advisory pilot. They are not
achieved airline results and not industry benchmarks.
