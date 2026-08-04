# Lab 03: RAG Systems

> Build production RAG pipelines — from naive retrieval to advanced hybrid search with evaluation.

## Labs

| Lab | Topic | What You Build |
|-----|-------|----------------|
| 3.1 | RAG from Scratch | Complete pipeline: chunk → embed → store → retrieve → generate |
| 3.2 | Hybrid Search | BM25 + vector search with Reciprocal Rank Fusion |
| 3.3 | Advanced Chunking | Semantic chunking, parent-child, sliding window comparison |
| 3.4 | RAG Evaluation | Measure faithfulness, relevance, and context precision |

## Prerequisites

```bash
pip install numpy  # Only numpy needed for basic labs
# Optional for production labs:
# pip install openai pinecone-client sentence-transformers
```

## Quick Start

```bash
cd labs/03-rag-systems
python lab_1_rag_pipeline.py    # Zero dependencies, runs immediately
python lab_2_hybrid_search.py   # BM25 + vector fusion
python lab_3_chunking.py        # Compare chunking strategies
python lab_4_eval.py            # Measure RAG quality
```

## Key Insight

RAG quality depends more on retrieval quality than generation quality.
If you retrieve garbage, even GPT-4 produces garbage. Focus on chunking and retrieval first.
