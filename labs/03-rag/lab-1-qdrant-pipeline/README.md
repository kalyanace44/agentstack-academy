# Lab 3.1: RAG Pipeline — Qdrant + OpenAI Embeddings

## Architecture

```
┌──────────┐     ┌──────────────┐     ┌──────────┐     ┌──────────┐
│  Docs    │────▶│  Embed       │────▶│  Qdrant  │     │  LLM     │
│  (PDF/MD)│     │  (OpenAI)    │     │  :6333   │────▶│  Answer  │
└──────────┘     └──────────────┘     └──────────┘     └──────────┘
```

## Why

LLMs don't know your docs. RAG = "search your knowledge base, stuff results into prompt."
No fine-tuning needed. Works with any model. Update docs instantly.

## Setup

```bash
make up          # Qdrant is live at localhost:6333
make index       # Index sample docs (3 commands)
make query       # Ask questions against your docs
make dashboard   # Open Qdrant dashboard in browser
```

## What You'll Do

1. `docker-compose up -d` — Qdrant running
2. Read `config.yaml` — embedding model, chunk size, collection settings
3. `make index` — chunk + embed + store your docs
4. `make query` — search with curl, see ranked results
5. Challenge: Change chunk_size in config, re-index, compare results

## Key Config

All you change is `config.yaml`. The pipeline script is 30 lines.
