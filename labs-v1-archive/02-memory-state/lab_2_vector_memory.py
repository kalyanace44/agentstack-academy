"""Lab 2.2: Vector Long-Term Memory

Store agent experiences as embeddings and retrieve by similarity.
Enables agents to recall relevant past interactions across sessions.
"""
from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field


@dataclass
class MemoryEntry:
    id: str
    content: str
    embedding: list[float]
    timestamp: float = field(default_factory=time.time)
    importance: float = 1.0
    access_count: int = 0
    metadata: dict = field(default_factory=dict)


class VectorMemory:
    """Long-term memory backed by vector similarity search."""

    def __init__(self, dim: int = 64, max_entries: int = 1000):
        self.dim = dim
        self.max_entries = max_entries
        self.entries: list[MemoryEntry] = []
        self._vocab: dict[str, int] = {}

    def _embed(self, text: str) -> list[float]:
        """Simple TF embedding (replace with OpenAI/Cohere in production)."""
        import re
        words = re.findall(r'\w+', text.lower())
        vec = [0.0] * self.dim
        for w in words:
            if w not in self._vocab:
                self._vocab[w] = len(self._vocab) % self.dim
            vec[self._vocab[w]] += 1.0
        mag = math.sqrt(sum(x*x for x in vec)) or 1.0
        return [x / mag for x in vec]

    def store(self, content: str, importance: float = 1.0, **metadata) -> str:
        """Store a memory entry."""
        entry_id = hashlib.md5(f"{content}:{time.time()}".encode()).hexdigest()[:12]
        entry = MemoryEntry(
            id=entry_id, content=content,
            embedding=self._embed(content),
            importance=importance, metadata=metadata,
        )
        self.entries.append(entry)
        if len(self.entries) > self.max_entries:
            self._evict()
        return entry_id

    def recall(self, query: str, top_k: int = 3) -> list[tuple[MemoryEntry, float]]:
        """Retrieve memories most relevant to the query."""
        q_emb = self._embed(query)
        scored = []
        for entry in self.entries:
            sim = self._cosine(q_emb, entry.embedding)
            # Boost by importance and recency
            recency = 1.0 / (1.0 + (time.time() - entry.timestamp) / 3600)
            score = sim * 0.6 + entry.importance * 0.2 + recency * 0.2
            scored.append((entry, score))
            entry.access_count += 1
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    def _evict(self):
        """Evict least important/accessed memories."""
        self.entries.sort(key=lambda e: e.importance * (e.access_count + 1), reverse=True)
        self.entries = self.entries[:self.max_entries]

    @staticmethod
    def _cosine(a: list[float], b: list[float]) -> float:
        dot = sum(x*y for x, y in zip(a, b))
        ma = math.sqrt(sum(x*x for x in a)) or 1.0
        mb = math.sqrt(sum(x*x for x in b)) or 1.0
        return dot / (ma * mb)


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 2.2: Vector Long-Term Memory")
    print("  Store experiences → retrieve by similarity across sessions")
    print("=" * 70)
    print()

    memory = VectorMemory()

    # Simulate past interactions
    experiences = [
        ("User prefers concise responses under 200 words", 0.9),
        ("User's credit limit was increased to ₹5L on June 15", 0.8),
        ("User had a payment failure on May 3 — resolved by retry", 0.7),
        ("User is interested in UPI credit line features", 0.8),
        ("User's KYC was completed on April 20 with PAN verification", 0.6),
        ("Agent previously recommended GPT-4o-mini for cost savings", 0.5),
        ("User escalated a ticket about slow API response times", 0.7),
        ("User works in fintech — understands technical terms", 0.9),
    ]

    for content, importance in experiences:
        memory.store(content, importance=importance)
    print(f"  📦 Stored {len(experiences)} memories\n")

    # Query
    queries = [
        "What do I know about this user's preferences?",
        "Any payment issues in the past?",
        "What's the user's credit limit?",
        "Technical background?",
    ]

    for q in queries:
        results = memory.recall(q, top_k=2)
        print(f"  Q: \"{q}\"")
        for entry, score in results:
            print(f"    → [{score:.2f}] {entry.content}")
        print()

    print(f"  ✅ {len(memory.entries)} memories stored, recall working")
