# Lab 2.1: Redis Memory — Persistent Agent Memory in 5 Minutes

## Architecture

```
┌──────────┐     ┌───────────┐     ┌───────────┐
│  Agent   │────▶│  Redis    │     │ Expire    │
│  (app.py)│◀────│  :6379    │────▶│ after 24h │
└──────────┘     └───────────┘     └───────────┘
```

## Why

Agents are stateless by default — every call starts fresh.
Redis gives them memory: conversation history, user preferences, session state.
Config-driven TTL means old memories expire automatically.

## Setup

```bash
make up       # Redis is live
make test     # Store + retrieve + expire
```

## What You'll Do

1. `docker-compose up -d` — Redis is ready
2. Read `config.yaml` — memory namespaces, TTL, max entries
3. `make test` — see memory store/retrieve/expire in action
4. Challenge: Change TTL to 10s, watch memories disappear
5. Challenge: Add a new namespace for "user_preferences"
