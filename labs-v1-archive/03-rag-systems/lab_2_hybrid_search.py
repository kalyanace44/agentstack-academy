"""Lab 3.2: Hybrid Search — BM25 + Vector with Reciprocal Rank Fusion

Combine keyword (BM25) and semantic (vector) search for better retrieval.
RRF merges rankings without needing score normalization.
"""
from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Document:
    id: str
    text: str
    metadata: dict = field(default_factory=dict)


class BM25:
    """BM25 keyword search (Okapi BM25)."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs: list[Document] = []
        self.doc_freqs: dict[str, int] = defaultdict(int)
        self.doc_lens: list[int] = []
        self.avg_dl: float = 0
        self.tokenized: list[list[str]] = []

    def index(self, docs: list[Document]):
        self.docs = docs
        self.tokenized = [self._tokenize(d.text) for d in docs]
        self.doc_lens = [len(t) for t in self.tokenized]
        self.avg_dl = sum(self.doc_lens) / max(len(self.doc_lens), 1)
        # Document frequencies
        for tokens in self.tokenized:
            seen = set(tokens)
            for term in seen:
                self.doc_freqs[term] += 1

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        q_tokens = self._tokenize(query)
        scores = []
        n = len(self.docs)
        for i, doc_tokens in enumerate(self.tokenized):
            score = 0.0
            dl = self.doc_lens[i]
            for term in q_tokens:
                if term not in self.doc_freqs:
                    continue
                tf = doc_tokens.count(term)
                df = self.doc_freqs[term]
                idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
                tf_norm = (tf * (self.k1 + 1)) / (tf + self.k1 * (1 - self.b + self.b * dl / self.avg_dl))
                score += idf * tf_norm
            scores.append((self.docs[i].id, score))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r'\w+', text.lower())


class VectorSearch:
    """Simple vector search with TF embeddings."""

    def __init__(self, dim: int = 64):
        self.dim = dim
        self.docs: list[Document] = []
        self.embeddings: list[list[float]] = []
        self._vocab: dict[str, int] = {}

    def index(self, docs: list[Document]):
        self.docs = docs
        self.embeddings = [self._embed(d.text) for d in docs]

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        q_emb = self._embed(query)
        scores = []
        for i, emb in enumerate(self.embeddings):
            sim = self._cosine(q_emb, emb)
            scores.append((self.docs[i].id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def _embed(self, text: str) -> list[float]:
        words = re.findall(r'\w+', text.lower())
        vec = [0.0] * self.dim
        for w in words:
            if w not in self._vocab:
                self._vocab[w] = len(self._vocab) % self.dim
            vec[self._vocab[w]] += 1.0
        mag = math.sqrt(sum(x*x for x in vec)) or 1.0
        return [x/mag for x in vec]

    @staticmethod
    def _cosine(a, b):
        dot = sum(x*y for x, y in zip(a, b))
        ma = math.sqrt(sum(x*x for x in a)) or 1.0
        mb = math.sqrt(sum(x*x for x in b)) or 1.0
        return dot / (ma * mb)


def reciprocal_rank_fusion(rankings: list[list[tuple[str, float]]], k: int = 60) -> list[tuple[str, float]]:
    """Merge multiple rankings using RRF. No score normalization needed."""
    fused: dict[str, float] = defaultdict(float)
    for ranking in rankings:
        for rank, (doc_id, _score) in enumerate(ranking):
            fused[doc_id] += 1.0 / (k + rank + 1)
    result = sorted(fused.items(), key=lambda x: x[1], reverse=True)
    return result


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 3.2: Hybrid Search (BM25 + Vector + RRF)")
    print("  Better retrieval by combining keyword and semantic search")
    print("=" * 70)
    print()

    docs = [
        Document("d1", "Kubernetes HPA scales pods based on CPU utilization and custom metrics like queue depth"),
        Document("d2", "Auto-scaling in cloud environments uses horizontal pod autoscaler for workload management"),
        Document("d3", "Circuit breakers prevent cascading failures in distributed microservice architectures"),
        Document("d4", "Rate limiting with token buckets prevents API abuse and protects backend services"),
        Document("d5", "Vector databases like Pinecone store embeddings for fast similarity search at scale"),
        Document("d6", "BM25 is a bag-of-words retrieval function used in search engines like Elasticsearch"),
        Document("d7", "AI agents need observability — trace every reasoning step and tool call for debugging"),
        Document("d8", "Cost management for LLM workloads requires per-team budgets and model routing"),
    ]

    bm25 = BM25()
    vector = VectorSearch()
    bm25.index(docs)
    vector.index(docs)

    queries = [
        "How do I auto-scale Kubernetes pods?",
        "prevent failures in microservices",
        "search and retrieval for AI",
    ]

    for query in queries:
        bm25_results = bm25.search(query, top_k=5)
        vector_results = vector.search(query, top_k=5)
        hybrid_results = reciprocal_rank_fusion([bm25_results, vector_results])

        print(f"  Q: \"{query}\"")
        print(f"    BM25 top-3:   {[r[0] for r in bm25_results[:3]]}")
        print(f"    Vector top-3: {[r[0] for r in vector_results[:3]]}")
        print(f"    Hybrid top-3: {[r[0] for r in hybrid_results[:3]]}")
        # Show winner
        winner_id = hybrid_results[0][0]
        winner_doc = next(d for d in docs if d.id == winner_id)
        print(f"    Best match:   \"{winner_doc.text[:70]}...\"")
        print()

    print("  ✅ Hybrid search combines strengths of both approaches")
    print("  💡 BM25 wins on exact keywords, Vector wins on semantic meaning, RRF merges both")
