# Lab 2.2: Vector Memory — Semantic Search with Qdrant

## Architecture

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│  Agent   │────▶│  Embed       │────▶│  Qdrant  │
│  (store) │     │  (OpenAI)    │     │  :6333   │
│          │◀────│              │◀────│  (recall) │
└──────────┘     └──────────────┘     └──────────┘
```

## Why

Redis = exact key lookups (fast but dumb).
Vector memory = "find me things SIMILAR to this" (semantic search).

When your agent says "we discussed deployment options earlier" — that's a vector memory lookup, not a key-value fetch.

## Setup

```bash
make up         # Qdrant running
make test       # Store memories → semantic recall
make search     # Query: "deployment" → finds related memories
```

## What You'll Do

1. Read `config.yaml` — embedding model, similarity threshold, TTL
2. `make up` — Qdrant + embedding service running
3. Store agent memories (conversations, decisions, context)
4. Query by meaning: "infrastructure" finds "we chose Kubernetes"
5. Challenge: Set up memory namespaces (per-user, per-session)
6. Challenge: Add TTL — memories expire after 7 days

## Key Insight

Config controls: which embedding model, similarity threshold, max results.
Code is just `qdrant.search(query_vector, limit=config["top_k"])`.
