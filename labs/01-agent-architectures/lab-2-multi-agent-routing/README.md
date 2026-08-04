# Lab 1.2: Multi-Agent Routing — Right Model for the Right Job

## Architecture

```
                         ┌──────────┐
            ┌──credit───▶│ gpt-4o   │ accurate, expensive
┌────────┐  │            └──────────┘
│ Router  │──┤            ┌──────────┐
│ (config)│  ├──faq──────▶│ gpt-mini │ fast, cheap
└────────┘  │            └──────────┘
            │            ┌──────────┐
            └──fraud────▶│ claude   │ best reasoning
                         └──────────┘
```

## Why

One model doesn't fit all. FAQ answers don't need GPT-4o ($$$).
Credit decisions shouldn't use GPT-4o-mini (too stupid).
Route by intent → save 70% cost while keeping quality where it matters.

## Setup

```bash
cp .env.example .env   # Add your API keys
make up
make test
```

## What You'll Do

1. Read `config.yaml` — understand routing rules
2. `make up` — deploy the router
3. `make test` — send different request types, see routing decisions
4. Edit `config.yaml` — add a new route, change fallbacks
5. Challenge: Add cost caps per team in config
