# Lab 5.1: Full-Stack Agent Deployment — Docker Compose

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                docker-compose up                      │
├──────────┬──────────┬──────────┬──────────┬─────────┤
│ LiteLLM  │  Qdrant  │  Redis   │ LangFuse │  App    │
│ :4000    │  :6333   │  :6379   │  :3000   │  :8080  │
│ (proxy)  │  (RAG)   │ (memory) │ (traces) │ (agent) │
└──────────┴──────────┴──────────┴──────────┴─────────┘
```

## Why

Every component you learned separately now runs together.
One `docker-compose up` = complete agent system.

## Setup

```bash
cp .env.example .env    # Add API keys
make up                 # Everything starts
make test               # End-to-end health checks
make logs               # Tail all services
```

## What You'll Do

1. Read `docker-compose.yml` — understand how services connect
2. Read `.env.example` — what config each service needs
3. `make up` — watch all 5 services start
4. `make test` — verify every service is healthy
5. Challenge: Add a Prometheus + Grafana stack to the compose file
