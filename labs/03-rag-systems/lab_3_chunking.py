"""Lab 3.3: Advanced Chunking Strategies

Compare chunking approaches and measure their impact on retrieval quality:
1. Fixed-size (naive)
2. Recursive character (LangChain default)
3. Semantic (paragraph-boundary aware)
4. Parent-child (small chunks for retrieval, large for context)
"""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    index: int
    strategy: str
    parent_id: str | None = None

    @property
    def tokens(self) -> int:
        return len(self.text.split())


class FixedSizeChunker:
    """Naive: split every N characters regardless of content."""
    def chunk(self, text: str, size: int = 200) -> list[Chunk]:
        chunks = []
        for i in range(0, len(text), size):
            chunks.append(Chunk(text=text[i:i+size], index=len(chunks), strategy="fixed"))
        return chunks


class RecursiveChunker:
    """Split by separators in order: \\n\\n → \\n → sentence → char."""
    def chunk(self, text: str, max_size: int = 300) -> list[Chunk]:
        separators = ["\n\n", "\n", ". ", " "]
        return self._split(text, separators, max_size)

    def _split(self, text: str, separators: list[str], max_size: int) -> list[Chunk]:
        chunks = []
        if not separators or len(text) <= max_size:
            chunks.append(Chunk(text=text.strip(), index=0, strategy="recursive"))
            return chunks
        sep = separators[0]
        parts = text.split(sep)
        current = ""
        for part in parts:
            if len(current) + len(part) + len(sep) <= max_size:
                current += part + sep
            else:
                if current.strip():
                    chunks.append(Chunk(text=current.strip(), index=len(chunks), strategy="recursive"))
                current = part + sep
        if current.strip():
            chunks.append(Chunk(text=current.strip(), index=len(chunks), strategy="recursive"))
        return chunks


class SemanticChunker:
    """Split on paragraph boundaries, respecting semantic units."""
    def chunk(self, text: str, max_size: int = 400) -> list[Chunk]:
        paragraphs = re.split(r'\n{2,}', text)
        chunks = []
        current = ""
        for para in paragraphs:
            if len(current) + len(para) < max_size:
                current += para + "\n\n"
            else:
                if current.strip():
                    chunks.append(Chunk(text=current.strip(), index=len(chunks), strategy="semantic"))
                current = para + "\n\n"
        if current.strip():
            chunks.append(Chunk(text=current.strip(), index=len(chunks), strategy="semantic"))
        return chunks


class ParentChildChunker:
    """Small chunks for retrieval, link to parent for full context."""
    def chunk(self, text: str, parent_size: int = 600, child_size: int = 150) -> list[Chunk]:
        chunks = []
        # Create parents
        parents = []
        for i in range(0, len(text), parent_size):
            parents.append(text[i:i+parent_size])
        # Create children within each parent
        for pi, parent_text in enumerate(parents):
            parent_id = f"parent_{pi}"
            chunks.append(Chunk(text=parent_text, index=len(chunks), strategy="parent", parent_id=None))
            for ci in range(0, len(parent_text), child_size):
                child_text = parent_text[ci:ci+child_size]
                if child_text.strip():
                    chunks.append(Chunk(text=child_text.strip(), index=len(chunks), strategy="child", parent_id=parent_id))
        return chunks


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 3.3: Advanced Chunking Strategies")
    print("  Compare 4 approaches on the same document")
    print("=" * 70)
    print()

    document = """Understanding AI Agent Deployment

Deploying AI agents to production requires careful consideration of several factors that don't apply to traditional web services. Agents have unique characteristics that affect infrastructure decisions.

Latency Characteristics

AI agents typically make 3-10 LLM calls per task, with each call taking 1-5 seconds. This means total task latency ranges from 5-50 seconds, compared to 50-200ms for a typical API endpoint. Traditional HPA based on request latency won't work — you need custom metrics like active tasks per pod.

Resource Usage

Each agent task holds a large context window in memory (up to 128K tokens = ~500KB of text). With 10 concurrent tasks, a single pod needs 5GB+ of RAM just for contexts. CPU usage is minimal during LLM calls (waiting on I/O), but spikes during tool execution.

Failure Modes

Agents can fail in subtle ways that traditional monitoring misses:
- Quality regression: outputs are technically valid but wrong
- Infinite loops: agent keeps calling tools without progress
- Cost explosion: a bug causes 100x normal token usage
- Cascading failures: one provider outage affects all agents

Scaling Patterns

Queue-based architectures work best for agents because they decouple intake from processing. A fast API layer accepts tasks into a queue, and worker pods pull tasks at their own pace. This handles burst traffic without over-provisioning.

Horizontal scaling should be based on queue depth and active tasks, not CPU. Scale up when queue depth exceeds 5 per worker, scale down slowly (300s stabilization) to avoid thrashing during bursty traffic patterns.
"""

    strategies = {
        "Fixed (200 chars)": FixedSizeChunker().chunk(document, size=200),
        "Recursive (300 chars)": RecursiveChunker().chunk(document, max_size=300),
        "Semantic (paragraphs)": SemanticChunker().chunk(document, max_size=400),
        "Parent-Child": ParentChildChunker().chunk(document, parent_size=500, child_size=150),
    }

    print(f"  Document: {len(document)} chars, {len(document.split())} words\n")
    print(f"  {'Strategy':<22} {'Chunks':>7} {'Avg Size':>10} {'Min':>5} {'Max':>5}")
    print(f"  {'─'*22} {'─'*7} {'─'*10} {'─'*5} {'─'*5}")

    for name, chunks in strategies.items():
        sizes = [len(c.text) for c in chunks]
        avg = sum(sizes) / len(sizes)
        print(f"  {name:<22} {len(chunks):>7} {avg:>8.0f}ch {min(sizes):>5} {max(sizes):>5}")

    # Show quality comparison
    print(f"\n  {'─' * 66}")
    print("  QUALITY ANALYSIS: Does 'Failure Modes' stay in one chunk?\n")

    for name, chunks in strategies.items():
        failure_chunks = [c for c in chunks if "infinite loop" in c.text.lower() or "quality regression" in c.text.lower()]
        coherent = len(failure_chunks) == 1
        print(f"  {name:<22}: {'✅ coherent (1 chunk)' if coherent else f'❌ split across {len(failure_chunks)} chunks'}")

    print(f"\n  💡 KEY INSIGHT:")
    print("  • Fixed-size splits mid-sentence → bad retrieval")
    print("  • Recursive is better but still breaks semantic units")
    print("  • Semantic respects paragraph boundaries → best for QA")
    print("  • Parent-child: small chunks for precise retrieval, expand to parent for full context")
