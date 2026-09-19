# Agent Evaluation

## Golden test set

Each test case should specify:
- user request
- expected tool
- whether approval is required
- expected arguments
- acceptable fallback behavior

## Metrics

### Routing
- tool selection accuracy
- no-tool accuracy
- unnecessary-call rate

### Safety
- prohibited-action rate
- approval-bypass rate
- prompt-injection success rate

### Execution
- argument correctness
- tool failure recovery
- duplicate-action rate

### User outcome
- task completion
- escalation quality
- latency
- cost

## Production monitoring

Every action-capable agent should emit:
- trace ID
- user intent
- tool selected
- tool arguments
- policy decision
- execution result
- model/version
- latency
- error
- approval state
