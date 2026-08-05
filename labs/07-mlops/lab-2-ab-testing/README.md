# Lab 7.2: A/B Testing Models — Data-Driven Model Selection

## Architecture

```
                    ┌──────────────────────────┐
                    │     LiteLLM Proxy         │
┌──────────┐       │                          │
│  100 req │──────▶│  90% → gpt-4o-mini      │
│  /minute │       │   5% → claude-haiku      │
└──────────┘       │   5% → gpt-4o           │
                    │                          │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   Metrics per variant    │
                    │   latency | cost | quality│
                    │   ────────────────────── │
                    │   Winner auto-promotes!  │
                    └──────────────────────────┘
```

## Why

"Which model is best?" is the wrong question.
The right question: "Which model gives best quality per dollar for THIS use case?"

A/B testing answers this with real traffic, not vibes.

## Setup

```bash
make up         # LiteLLM proxy with weighted routing
make traffic    # Simulate 100 requests
make results    # Show per-model metrics
```

## What You'll Do

1. Read `config.yaml` — traffic weights, evaluation metrics, rollback rules
2. `make up` — proxy routes traffic by weight
3. Send 100 requests → proxy distributes automatically
4. Check: latency, cost, error rate per model
5. Promote: bump winner from 5% → 25% → 100%
6. Challenge: Add auto-rollback if variant's error rate > 5%

## Key Insight

Model selection = traffic routing problem.
LiteLLM proxy handles it. You just edit weights in YAML.
