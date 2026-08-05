# Lab 1.3: Google A2A Protocol — Agent Discovery + Delegation

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   A2A Registry                           │
│            /.well-known/agent.json                       │
└────────┬──────────────────┬──────────────────┬──────────┘
         │                  │                  │
    ┌────▼─────┐      ┌────▼─────┐      ┌────▼─────┐
    │  Credit  │      │  Fraud   │      │  KYC     │
    │  Agent   │      │  Agent   │      │  Agent   │
    │  :8001   │      │  :8002   │      │  :8003   │
    └────▲─────┘      └────▲─────┘      └────▲─────┘
         │                  │                  │
         └──────────────────┼──────────────────┘
                            │
                   ┌────────▼────────┐
                   │  Orchestrator   │
                   │  (discovers +   │
                   │   delegates)    │
                   └─────────────────┘
```

## Why

Without A2A, every agent integration is custom glue code.
With A2A: agents publish what they can do (Agent Card), others discover and delegate via a standard protocol.

- Your LangChain agent can talk to someone else's CrewAI agent
- No shared codebase needed — just the protocol
- Like HTTP for AI agents

## Key Concepts

| Concept | What It Is | Analogy |
|---------|-----------|---------|
| Agent Card | JSON manifest of capabilities | API docs / OpenAPI spec |
| Task | Unit of work with lifecycle | HTTP request/response |
| Discovery | Find agents by skill | DNS lookup |
| Delegation | Send task to another agent | REST API call |

## Setup

```bash
make up         # Start 3 agent services + registry
make discover   # See which agents are registered
make test       # Orchestrator delegates to specialists
```

## What You'll Do

1. Read `agents.yaml` — agent capabilities declared as config
2. `make up` — agents register their Agent Cards
3. `make discover` — query registry: "who can do credit_score?"
4. `make test` — orchestrator delegates tasks, see lifecycle
5. Challenge: Add a new agent (KYC verifier) — just add to config
6. Challenge: Kill one agent — watch orchestrator failover to another

## Files

```
lab-3-a2a-protocol/
├── agents.yaml           ← Agent definitions (capabilities, endpoints)
├── docker-compose.yml    ← Each agent as a service
├── server.py             ← 45 lines: A2A-compliant FastAPI server
├── orchestrator.py       ← 30 lines: discover + delegate
└── test.sh              ← Verify discovery + task delegation
```
