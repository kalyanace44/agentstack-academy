# Lab 9.1: Full Production Stack — Complete Agent System

## Architecture

```
┌─────────────────────────── Production Stack ──────────────────────────────┐
│                                                                            │
│  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌───────────┐           │
│  │ Ingress │───▶│ Agent    │───▶│ LiteLLM  │───▶│ OpenAI/   │           │
│  │ (nginx) │    │ (FastAPI)│    │ (proxy)  │    │ Anthropic │           │
│  └─────────┘    └──────────┘    └──────────┘    └───────────┘           │
│                       │                                                    │
│              ┌────────┼────────┐                                          │
│              ▼        ▼        ▼                                          │
│         ┌────────┐ ┌──────┐ ┌────────┐                                  │
│         │ Qdrant │ │Redis │ │LangFuse│                                   │
│         │ (RAG)  │ │(mem) │ │(traces)│                                   │
│         └────────┘ └──────┘ └────────┘                                   │
│                                                                            │
│  ┌────────────────────────────────────────────────────┐                   │
│  │ Prometheus + Grafana (metrics + alerts + dashboard)│                   │
│  └────────────────────────────────────────────────────┘                   │
└────────────────────────────────────────────────────────────────────────────┘
```

## This Lab Combines Everything

| Module | Component | Config File |
|--------|-----------|-------------|
| 01 | LiteLLM Proxy | `config/litellm.yaml` |
| 02 | Redis Memory | `config/memory.yaml` |
| 03 | Qdrant RAG | `config/rag.yaml` |
| 04 | PII Scanner | `config/guardrails.yaml` |
| 05 | Docker Compose | `docker-compose.yml` |
| 06 | LangFuse + Grafana | `config/observability.yaml` |
| 07 | Model Registry | `config/models.yaml` |

## Setup

```bash
cp .env.example .env    # Add your API keys
make up                 # Full stack (7 services)
make test               # End-to-end validation
make dashboard          # Open Grafana
make traces             # Open LangFuse
```

## What You'll Do

1. Read `docker-compose.yml` — see how all services connect
2. `make up` — full system comes alive
3. `make test` — validates every service
4. Send a query → trace it through: guardrails → memory → RAG → LLM → response
5. Break something: kill Qdrant → see fallback behavior
6. Monitor: watch Grafana dashboard during load test
