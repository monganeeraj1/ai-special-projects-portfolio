# Reference Architecture

## End-to-end design

```text
Operational source systems
  ├─ flight operations
  ├─ aircraft / fleet data
  ├─ weather
  ├─ airport / taxi data
  └─ planning / schedule data
          ↓
Data quality + lineage layer
          ↓
Feature pipeline / feature store
          ↓
Training environment
  ├─ experiment tracking
  ├─ model registry
  └─ validation
          ↓
Model serving
          ↓
Decision-support service
  ├─ prediction
  ├─ confidence / thresholds
  ├─ controllable-lever analysis
  └─ explanation
          ↓
Operational workflow
  ├─ planner
  ├─ dispatcher
  ├─ fuel / efficiency team
  └─ management dashboard
          ↓
Outcome capture
  ├─ action taken?
  ├─ realized fuel impact
  ├─ operator feedback
  └─ exception reason
          ↓
Monitoring + retraining
```

## Architecture principles

### Separate prediction from intervention
The model estimates opportunity. A separate decision layer determines whether action is appropriate.

### Make time-of-decision explicit
Training data must mirror the features that are available when the real decision is made.

### Preserve lineage
Every recommendation should be traceable to:
- data version
- feature version
- model version
- prediction timestamp
- recommendation logic
- user action

### Design for feedback
Capture whether operators accepted, rejected, or modified the recommendation and why.

### Keep business rules outside the model where possible
Operational constraints and policy thresholds change faster than model logic and should be configurable.
