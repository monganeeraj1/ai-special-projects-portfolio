# 01 — RAG Evaluation Lab

## Executive question

**How do you know whether a Retrieval-Augmented Generation system is actually trustworthy?**

A RAG system can fail even when the LLM is strong. Common failure modes include:
- the right source was never retrieved
- the source was retrieved but ranked too low
- chunks lost important context
- the model ignored retrieved evidence
- the answer was plausible but unsupported
- stale or conflicting documents were used

This project separates **retrieval quality** from **generation quality**.

## Reference architecture

```text
User query
   ↓
Query preprocessing
   ↓
Retriever
   ├─ lexical retrieval
   ├─ dense retrieval
   └─ hybrid / reranking
   ↓
Top-k evidence
   ↓
LLM generation
   ↓
Grounding checks
   ↓
Answer + citations
   ↓
Evaluation + monitoring
```

## What is evaluated

### Retrieval
- Recall@K
- Mean Reciprocal Rank (MRR)
- coverage by document type
- sensitivity to chunk size / overlap

### Generation
- groundedness
- citation correctness
- completeness
- refusal quality when evidence is weak
- latency
- token / inference cost

## Why this matters

If Recall@5 is poor, prompting will not fix the system.  
If retrieval is strong but groundedness is poor, the generation layer or prompt policy needs work.  
If both are good but users still fail tasks, the workflow or UX is the problem.

## Files

- `rag_eval.py` — runnable retrieval and evaluation prototype
- `evaluation_framework.md` — enterprise evaluation design
- `architecture.md` — production considerations

## Run

```bash
python rag_eval.py
```

The runnable prototype uses TF-IDF retrieval so it works without external APIs. The architecture notes explain how this extends to dense embeddings, hybrid retrieval, reranking, and LLM-based generation.
