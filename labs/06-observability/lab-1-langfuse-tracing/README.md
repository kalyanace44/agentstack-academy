# Lab 6.1: LangFuse Tracing — See Every Agent Decision

## Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────────┐
│  Agent   │────▶│  LLM     │     │  LangFuse    │
│  (app)   │     │  (proxy) │────▶│  :3000       │
└──────────┘     └──────────┘     │  (dashboard) │
                                   └──────────────┘
```

## Why

When an agent gives a wrong answer, you need to see WHY:
- What prompt was sent?
- What context was retrieved?
- Which model was used?
- How many tokens / how much cost?
- Where in the chain did it go wrong?

LangFuse = X-ray vision for your agent system.

## Setup

```bash
make up           # LangFuse + Postgres running
make open         # Open dashboard in browser
make test         # Send traced requests, see them appear
```

## What You'll Do

1. `docker-compose up -d` — LangFuse is live at localhost:3000
2. Create a project in the dashboard (API key)
3. Send a traced request (10-line script)
4. See: full trace with timing, tokens, cost in the dashboard
5. Challenge: Add custom scores (user rating) to traces
