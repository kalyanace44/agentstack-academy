# Lab 7.1: LiteLLM Model Registry — Manage Models Like Infra

## Architecture

```
┌─────────────┐     ┌──────────────────────────────────────┐
│  Team A     │     │           LiteLLM Proxy              │
│  (lending)  │────▶│                                      │
├─────────────┤     │  Model Registry:                     │
│  Team B     │────▶│    gpt-4o → OpenAI (prod)           │
│  (support)  │     │    gpt-4o → Anthropic (canary 5%)   │
├─────────────┤     │    gpt-mini → OpenAI (all traffic)  │
│  Team C     │────▶│                                      │
│  (fraud)    │     │  Budgets: A=$10/day B=$3/day C=$15  │
└─────────────┘     └──────────────────────────────────────┘
```

## Why

Model management is infra, not code:
- Switch GPT-4o → Claude without code deploy
- Canary new models (5% traffic) with auto-rollback
- Per-team budgets prevent cost explosions
- A/B test models by config, not code

## Setup

```bash
make up         # LiteLLM with model registry
make test       # Show registered models + routing
```

## What You'll Do

1. Read `config.yaml` — models, teams, budgets
2. `make up` — proxy is live
3. `make test` — show what model each team gets
4. Change: swap a model for one team → `make restart`
5. Add a canary: 10% traffic to new model → monitor quality
6. Set a budget limit → exceed it → see requests rejected
