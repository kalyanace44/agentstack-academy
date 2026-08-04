# Lab 9.2: Cost Optimization — Spend 70% Less Without Losing Quality

## The Problem

Most teams waste 60-80% of their AI budget by sending everything to GPT-4o.
Fix: route by complexity. Simple questions → cheap model. Hard questions → expensive model.

## Architecture

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│  Request │────▶│  Complexity  │     │ gpt-mini │ ← 80% of traffic ($)
│          │     │  Classifier  │────▶│          │
└──────────┘     │  (5 rules)   │     ├──────────┤
                 └──────────────┘     │ gpt-4o   │ ← 15% of traffic ($$)
                                      ├──────────┤
                                      │ claude   │ ← 5% of traffic ($$$)
                                      └──────────┘
```

## Setup

```bash
make test     # Compare cost of naive vs optimized routing
```

## Config

```yaml
# cost-rules.yaml — route by complexity
routing:
  simple:
    keywords: [hello, thanks, yes, no, ok, help]
    model: gpt-4o-mini
    max_tokens: 200
    
  medium:
    patterns: [how, what, explain, compare]
    model: gpt-4o-mini
    max_tokens: 500
    
  complex:
    patterns: [analyze, design, review, debug, architect]
    model: gpt-4o
    max_tokens: 2000
    
  critical:
    patterns: [fraud, compliance, legal, security]
    model: claude-sonnet
    max_tokens: 2000
```

## What You'll Do

1. Read `cost-rules.yaml` — understand routing logic
2. `make test` — see cost comparison (naive vs smart routing)
3. Edit rules: tune the keywords for your use case
4. Challenge: Add caching — identical questions use cached response ($0)
5. Calculate: your monthly savings at 100K requests/day
