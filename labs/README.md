# AgentStack Academy — Labs

> Configure, deploy, and operate. Not implement from scratch.

## How Labs Work

Every lab follows the same pattern:

```
lab-name/
├── README.md           ← Architecture diagram + why this matters
├── config.yaml         ← The knobs you turn (THIS is the learning)
├── docker-compose.yml  ← Infrastructure (one command to start)
├── test.sh             ← Verify it works (curl + assertions)
├── Makefile            ← make up / make test / make logs
└── app.py             ← Thin glue (20-50 lines max, if needed)
```

## Modules

| # | Module | What You Deploy | Tools |
|---|--------|-----------------|-------|
| 01 | Agent Architectures | LLM proxy + routing | LiteLLM |
| 02 | Memory | Persistent agent memory | Redis |
| 03 | RAG | Vector search pipeline | Qdrant |
| 04 | Guardrails | PII scanner + prompt firewall | Rules YAML |
| 05 | Deployment | Full stack + K8s | Docker Compose, Helm |
| 06 | Observability | Tracing + dashboards | LangFuse, Grafana |
| 07 | MLOps | Model registry + canary | LiteLLM registry |
| 08 | Tools | Multi-agent teams | CrewAI, LangGraph |
| 09 | Production | Complete system + cost optimization | Everything |

## Prerequisites

- Docker + Docker Compose
- kubectl + helm (for Module 5.2)
- Python 3.11+ (for thin glue scripts)
- An LLM API key (OpenAI or Anthropic — or use free local Ollama)

## Getting Started

```bash
# Start with Module 01 — everything builds on this
cd 01-agent-architectures/lab-1-litellm-proxy
cp .env.example .env      # Add your API key
make up                   # Proxy is live
make test                 # Verify it works
```

## Philosophy

| Old way (academic) | Our way (DevOps) |
|--------------------|------------------|
| Implement BM25 from scratch (300 lines) | `docker-compose up qdrant` + config |
| Build a vector DB in Python | Edit `config.yaml`, change chunk_size |
| Write a tracing system | `helm install langfuse` + import dashboard |
| Code a rate limiter | Add 2 lines to `config.yaml` |

The real skill is: **which tool, how to configure it, how to debug it when it breaks.**
