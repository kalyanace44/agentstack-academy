# Lab 02: Memory & State Management

> Build memory systems that give agents persistent knowledge across conversations.

## Labs

| Lab | Pattern | What You Build |
|-----|---------|----------------|
| 2.1 | Conversation Memory | Sliding window, summary, and hybrid buffer |
| 2.2 | Vector Long-Term Memory | Store + retrieve past experiences by similarity |
| 2.3 | Entity Memory | Track and update knowledge about entities over time |
| 2.4 | Multi-Tenant Memory | Isolated memory per user/team with TTL and eviction |

## Prerequisites

```bash
pip install numpy  # For vector similarity in lab 2.2
# No API keys required — all labs run locally
```

## Quick Start

```bash
cd labs/02-memory-state
python lab_1_conversation_memory.py   # Three memory strategies compared
python lab_2_vector_memory.py         # Long-term recall by similarity
python lab_3_entity_memory.py         # Track entities across conversations
python lab_4_multi_tenant.py          # Production memory with isolation
```

## Key Insight

Memory is the difference between a chatbot and an agent. Without memory:
- Users repeat context every session
- Agents can't learn from past mistakes
- Multi-step tasks break across conversations

But memory in production is hard: you need isolation, eviction, cost control, and consistency.
