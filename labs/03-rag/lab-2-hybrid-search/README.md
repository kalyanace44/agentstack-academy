# Lab 3.2: Hybrid Search — BM25 + Vector for Better Recall

## Architecture

```
                       ┌──────────────┐
              ┌───────▶│ BM25 (Qdrant)│──── keyword matches
┌──────────┐  │        └──────────────┘
│  Query   │──┤                              ──▶ RRF Fusion ──▶ Top K
└──────────┘  │        ┌──────────────┐
              └───────▶│ Vector Search│──── semantic matches
                       └──────────────┘
```

## Why

Vector search alone misses exact keyword matches (e.g., error codes, product names).
BM25 alone misses semantic similarity ("deployment" doesn't match "shipping to prod").
Hybrid = best of both. Most production RAG uses this.

## Setup

```bash
make up         # Qdrant with hybrid mode
make index      # Index sample documents
make test       # Compare: vector-only vs hybrid
```

## What You'll Do

1. Read `config.yaml` — adjust BM25 vs vector weight
2. Index documents with both sparse (BM25) + dense (vector) representations
3. Query: "how to fix OOMKilled" — see hybrid finds exact match + related
4. Tune: set `bm25_weight: 0.7` for code/error searches
5. Tune: set `vector_weight: 0.8` for conceptual questions
6. Challenge: Add a reranker (Cohere/cross-encoder) on top

## Key Insight

The `fusion_weight` in config is the only knob that matters.
No algorithm to implement — Qdrant does both searches natively.
