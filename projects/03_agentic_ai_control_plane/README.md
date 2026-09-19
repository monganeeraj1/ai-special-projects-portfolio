# 03 — Agentic AI Control Plane

## Executive question

**How should an enterprise govern an AI system that can decide which tools to use and take actions?**

Agentic AI changes the risk profile because the model is no longer only generating text. It may:
- query enterprise systems
- call APIs
- trigger workflows
- draft actions
- execute actions

The key design problem becomes **control of autonomy**.

## Architecture

```text
User request
    ↓
Intent / risk classifier
    ↓
Planner
    ↓
Tool policy layer
    ├─ read-only tools
    ├─ low-risk write tools
    └─ high-impact tools → human approval
    ↓
Tool execution
    ↓
Observation
    ↓
Final response
    ↓
Audit log + evaluation
```

## Core controls

- explicit tool allowlist
- least-privilege credentials
- high-impact approval gates
- structured tool schemas
- idempotency where possible
- action logging
- timeout / retry policy
- rollback strategy
- prompt-injection defense
- rate and spend limits

## What to evaluate

- correct tool selection
- unnecessary tool calls
- prohibited-action rate
- argument correctness
- task completion
- recovery from tool failure
- escalation quality
- latency and cost
