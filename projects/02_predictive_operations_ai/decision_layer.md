# From Model to Decision

## Why ranking matters

In many operational AI use cases, the business cannot act on every prediction.

The practical question is:
> Which small number of cases should receive attention first?

This makes top-decile or top-k capture more important than global average error in some workflows.

## Decision design

For each predicted case:
1. estimate likely avoidable value
2. identify feasible interventions
3. assess intervention cost
4. prioritize only when expected benefit exceeds action cost
5. capture operator feedback
6. retrain / recalibrate as operating conditions change

## Causal caution

Feature importance is not intervention importance.

Example:
- bad weather may be highly predictive
- but weather itself is not controllable

The system should distinguish:
- predictive features
- controllable levers
- contextual constraints
- causal drivers
