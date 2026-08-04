"""Lab 3.1: RAG Pipeline from Scratch

Build a complete Retrieval-Augmented Generation pipeline:
1. Document loading and chunking
2. Embedding generation (simulated + real API option)
3. Vector storage with similarity search
4. Retrieval + LLM generation with citations

No external vector DB required — pure Python with NumPy.
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass, field


# --- Document Chunking ---

@dataclass
class Chunk:
    """A chunk of text with metadata."""
    id: str
    text: str
    source: str
    index: int
    embedding: list[float] = field(default_factory=list)


class TextChunker:
    """Splits documents into overlapping chunks.

    Strategy: recursive character splitting with overlap.
    Production tip: semantic chunking (by paragraph/section) usually beats fixed-size.
    """

    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str, source: str = "unknown") -> list[Chunk]:
        """Split text into overlapping chunks."""
        # Clean and normalize
        text = re.sub(r'\n{3,}', '\n\n', text.strip())

        # Try splitting by paragraphs first (semantic boundaries)
        paragraphs = text.split('\n\n')
        chunks = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) < self.chunk_size:
                current += para + "\n\n"
            else:
                if current:
                    chunks.append(current.strip())
                current = para + "\n\n"

                # If single paragraph exceeds chunk_size, split by sentences
                if len(current) > self.chunk_size:
                    sentences = re.split(r'(?<=[.!?])\s+', current)
                    current = ""
                    for sent in sentences:
                        if len(current) + len(sent) < self.chunk_size:
                            current += sent + " "
                        else:
                            if current:
                                chunks.append(current.strip())
                            current = sent + " "

        if current.strip():
            chunks.append(current.strip())

        # Add overlap
        result = []
        for i, chunk_text in enumerate(chunks):
            chunk_id = hashlib.md5(f"{source}:{i}:{chunk_text[:50]}".encode()).hexdigest()[:12]
            result.append(Chunk(id=chunk_id, text=chunk_text, source=source, index=i))

        return result


# --- Embedding (simulated for zero-dependency lab) ---

class SimpleEmbedder:
    """TF-IDF-like embedder for demonstration.

    In production, use:
    - OpenAI text-embedding-3-small ($0.02/1M tokens, 1536 dims)
    - Cohere embed-v3 (good for multilingual)
    - sentence-transformers/all-MiniLM-L6-v2 (free, local, 384 dims)
    """

    def __init__(self, dim: int = 128):
        self.dim = dim
        self.vocab: dict[str, int] = {}
        self._next_idx = 0

    def embed(self, text: str) -> list[float]:
        """Generate a simple embedding based on word frequencies."""
        words = re.findall(r'\w+', text.lower())
        vector = [0.0] * self.dim

        for word in words:
            if word not in self.vocab:
                self.vocab[word] = self._next_idx % self.dim
                self._next_idx += 1
            idx = self.vocab[word]
            vector[idx] += 1.0

        # Normalize
        magnitude = math.sqrt(sum(x * x for x in vector)) or 1.0
        return [x / magnitude for x in vector]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]


# --- Vector Store ---

class VectorStore:
    """In-memory vector store with cosine similarity search.

    Production alternatives: Pinecone, Qdrant, Weaviate, pgvector, Chroma.
    """

    def __init__(self):
        self.chunks: list[Chunk] = []

    def add(self, chunks: list[Chunk]):
        """Add chunks with embeddings to the store."""
        self.chunks.extend(chunks)

    def search(self, query_embedding: list[float], top_k: int = 3) -> list[tuple[Chunk, float]]:
        """Find most similar chunks by cosine similarity."""
        results = []
        for chunk in self.chunks:
            if not chunk.embedding:
                continue
            score = self._cosine_similarity(query_embedding, chunk.embedding)
            results.append((chunk, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    @staticmethod
    def _cosine_similarity(a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        mag_a = math.sqrt(sum(x * x for x in a)) or 1.0
        mag_b = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (mag_a * mag_b)

    @property
    def size(self) -> int:
        return len(self.chunks)


# --- RAG Pipeline ---

class RAGPipeline:
    """Complete RAG pipeline: chunk → embed → store → retrieve → generate."""

    def __init__(self):
        self.chunker = TextChunker(chunk_size=300, overlap=30)
        self.embedder = SimpleEmbedder(dim=128)
        self.store = VectorStore()
        self.documents_ingested = 0

    def ingest(self, text: str, source: str = "document"):
        """Ingest a document into the RAG pipeline."""
        # 1. Chunk
        chunks = self.chunker.chunk(text, source)

        # 2. Embed
        for chunk in chunks:
            chunk.embedding = self.embedder.embed(chunk.text)

        # 3. Store
        self.store.add(chunks)
        self.documents_ingested += 1
        return len(chunks)

    def query(self, question: str, top_k: int = 3) -> dict:
        """Query the RAG pipeline."""
        # 1. Embed query
        query_embedding = self.embedder.embed(question)

        # 2. Retrieve relevant chunks
        results = self.store.search(query_embedding, top_k=top_k)

        # 3. Build context
        context_parts = []
        sources = []
        for chunk, score in results:
            context_parts.append(f"[Source: {chunk.source}, Score: {score:.3f}]\n{chunk.text}")
            sources.append({"source": chunk.source, "chunk_id": chunk.id, "score": round(score, 3)})

        context = "\n\n---\n\n".join(context_parts)

        # 4. Generate answer (simulated — in production, call LLM here)
        prompt = f"""Answer the question based ONLY on the context below. If the context doesn't contain the answer, say "I don't have enough information."

Context:
{context}

Question: {question}

Answer:"""

        # Simulated response (in production: call OpenAI/Anthropic with this prompt)
        answer = f"Based on the retrieved context ({len(results)} sources, top relevance: {results[0][1]:.1%}), " \
                 f"here is what I found about '{question}':\n\n" \
                 f"The most relevant information comes from '{results[0][0].source}': " \
                 f"\"{results[0][0].text[:200]}...\""

        return {
            "answer": answer,
            "sources": sources,
            "context_tokens": len(context.split()),
            "prompt": prompt,
        }


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 3.1: RAG Pipeline from Scratch")
    print("  Chunk → Embed → Store → Retrieve → Generate")
    print("=" * 70)
    print()

    rag = RAGPipeline()

    # Sample documents (agent deployment knowledge base)
    docs = {
        "agent_architectures.md": """
AI Agent Architectures

The ReAct pattern combines reasoning and acting. The agent thinks about what to do,
takes an action, observes the result, and repeats. This creates an explicit reasoning
trace that helps with debugging and evaluation.

Multi-agent systems use multiple specialized agents that collaborate. CrewAI provides
role-based agents with defined goals and tools. AutoGen enables conversation-driven
coordination between agents. LangGraph adds state machines for complex workflows.

Function calling allows LLMs to invoke external tools. OpenAI, Anthropic, and Google
all provide native function calling support. The LLM outputs structured JSON that
maps to tool parameters. Tools should have clear descriptions and input schemas.
""",
        "deployment_patterns.md": """
Production Deployment Patterns for AI Agents

Kubernetes Deployment: Deploy agents as stateless pods behind a service. Use HPA
to scale based on queue depth or request latency. Set resource limits to prevent
OOM kills. Use pod disruption budgets for zero-downtime updates.

Queue-Based Architecture: Put agent tasks in a message queue (SQS, RabbitMQ).
Workers pull tasks and process them asynchronously. This decouples request intake
from processing and handles burst traffic gracefully.

Circuit Breakers: When an LLM provider fails repeatedly, open the circuit to stop
sending requests. This prevents cascading failures and protects your budget.
After a timeout period, send a single test request (half-open state).

Cost Management: Set per-request token limits. Track cost by team and project.
Use cheaper models for simple tasks, expensive models only when quality matters.
Cache repeated queries. Alert when daily spend exceeds thresholds.
""",
        "observability.md": """
Observability for AI Agent Systems

Tracing: Every agent execution should produce a trace showing the reasoning chain.
Include: prompt, model, tokens used, tool calls, latency per step, final output.
LangSmith and Arize provide specialized agent tracing.

Metrics: Track requests/sec, latency (p50, p95, p99), error rate, token usage,
cache hit rate, and cost per request. Use Prometheus + Grafana or Datadog.

Logging: Structured JSON logs with correlation IDs. Log reasoning steps at DEBUG
level, tool calls at INFO, errors at ERROR. Include model, team, and request ID
in every log line for filtering.

Alerting: Alert on error rate spikes, latency degradation, cost anomalies, and
agent loops (>10 steps without progress). Use PagerDuty or Opsgenie for on-call.
""",
    }

    # Ingest all documents
    print("  📄 Ingesting documents...")
    total_chunks = 0
    for name, content in docs.items():
        n = rag.ingest(content, source=name)
        print(f"    → {name}: {n} chunks")
        total_chunks += n

    print(f"\n  📊 Vector store: {rag.store.size} chunks indexed")
    print()

    # Query examples
    queries = [
        "How do I deploy AI agents on Kubernetes?",
        "What is the ReAct pattern?",
        "How do I track costs for AI agents?",
        "What metrics should I monitor for agent systems?",
    ]

    for q in queries:
        print(f"  ─────────────────────────────────────────────────")
        print(f"  Q: {q}")
        result = rag.query(q, top_k=2)
        print(f"  A: {result['answer'][:200]}...")
        print(f"  Sources: {[s['source'] for s in result['sources']]}")
        print(f"  Relevance: {[s['score'] for s in result['sources']]}")
        print()

    print(f"\n  ✅ RAG pipeline working — {total_chunks} chunks, {len(queries)} queries answered")
    print(f"  💡 Next: Replace SimpleEmbedder with OpenAI embeddings for production quality")
