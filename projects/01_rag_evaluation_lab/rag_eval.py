from dataclasses import dataclass
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

@dataclass
class Document:
    doc_id: str
    text: str

docs = [
    Document("d1", "The museum opens at 10 AM and closes at 8 PM on weekdays."),
    Document("d2", "Wheelchair access is available through the east entrance."),
    Document("d3", "Children under 12 can join the family heritage workshop."),
    Document("d4", "The evening cultural performance starts at 7 PM."),
    Document("d5", "Parking is available in the north visitor car park."),
]

eval_set = [
    {"query": "What time does the museum open?", "relevant": "d1"},
    {"query": "Is there wheelchair access?", "relevant": "d2"},
    {"query": "Can children join a heritage activity?", "relevant": "d3"},
    {"query": "When is the evening performance?", "relevant": "d4"},
    {"query": "Where can I park?", "relevant": "d5"},
]

corpus = [d.text for d in docs]
vectorizer = TfidfVectorizer(ngram_range=(1,2), stop_words="english")
doc_matrix = vectorizer.fit_transform(corpus)

def retrieve(query: str, k: int = 3) -> List[Dict]:
    q = vectorizer.transform([query])
    scores = cosine_similarity(q, doc_matrix)[0]
    ranked = np.argsort(scores)[::-1][:k]
    return [
        {"doc_id": docs[i].doc_id, "text": docs[i].text, "score": float(scores[i])}
        for i in ranked
    ]

def recall_at_k(k: int) -> float:
    hits = 0
    for item in eval_set:
        ids = [x["doc_id"] for x in retrieve(item["query"], k=k)]
        hits += item["relevant"] in ids
    return hits / len(eval_set)

def mrr() -> float:
    rr = []
    for item in eval_set:
        ranked = retrieve(item["query"], k=len(docs))
        ids = [x["doc_id"] for x in ranked]
        rank = ids.index(item["relevant"]) + 1
        rr.append(1 / rank)
    return sum(rr) / len(rr)

print("RAG RETRIEVAL EVALUATION")
for k in [1, 3, 5]:
    print(f"Recall@{k}: {recall_at_k(k):.2f}")
print(f"MRR: {mrr():.2f}")

sample = "I use a wheelchair. How do I enter?"
print("\nSample query:", sample)
for r in retrieve(sample, k=3):
    print(r)
