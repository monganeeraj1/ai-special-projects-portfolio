# Production RAG Architecture Notes

## Retrieval choices

### Lexical
Strengths:
- exact terminology
- IDs and codes
- deterministic
- cheap

Weaknesses:
- semantic mismatch

### Dense
Strengths:
- semantic similarity
- paraphrase robustness

Weaknesses:
- can retrieve conceptually similar but operationally wrong content

### Hybrid
Often preferred for enterprise use because it combines exact and semantic retrieval.

## Reranking

Use a cross-encoder or LLM reranker when:
- source corpus is large
- retrieval precision matters more than latency
- first-stage retrieval returns many near matches

## Chunking

Chunk size should be treated as an empirical variable, not a fixed best practice.

Evaluate:
- chunk size
- overlap
- structural boundaries
- metadata retention
- parent/child retrieval

## Grounding controls

- force citations
- restrict generation to retrieved evidence
- abstain below retrieval confidence
- validate claims against evidence
- surface source timestamps
