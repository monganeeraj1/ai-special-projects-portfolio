# Enterprise RAG Evaluation Framework

## Offline evaluation

### Retrieval test set
Create a gold-standard set of:
- user query
- expected source document
- expected source passage
- answerable / unanswerable label

Track:
- Recall@K
- MRR
- nDCG where graded relevance exists

### Generation test set
Human-review dimensions:
- factual correctness
- groundedness
- completeness
- citation validity
- tone / policy compliance
- correct abstention

### Stress tests
- ambiguous query
- stale document
- conflicting sources
- adversarial instruction inside a document
- multilingual query
- long-tail terminology
- no-answer case

## Online evaluation

Track:
- task completion
- escalation rate
- correction rate
- citation clicks
- repeat query rate
- latency
- cost per successful task
- user feedback

## Production decision

A launch threshold should require both:
1. technical performance above minimum levels
2. business task completion above baseline

A high model score without task improvement is not success.
