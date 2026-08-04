# Lab 06: Observability & Debugging

> Trace, measure, and debug AI agent systems in production.

## Labs

| Lab | Topic | What You Build |
|-----|-------|----------------|
| 6.1 | Agent Tracing | Full execution traces with timing, tokens, and tool calls |
| 6.2 | Metrics Dashboard | Prometheus metrics for latency, cost, errors, cache hits |
| 6.3 | Loop Detection | Detect and kill infinite agent loops before they burn budget |
| 6.4 | Cost Attribution | Per-team, per-model, per-task cost tracking and alerting |

## Prerequisites

```bash
pip install fastapi uvicorn  # For metrics endpoint
# No external services needed — all metrics are in-process
```

## Quick Start

```bash
cd labs/06-observability
python lab_1_agent_tracing.py      # See a full agent trace
python lab_2_metrics.py            # Prometheus metrics for agents
python lab_3_loop_detection.py     # Kill runaway agents
python lab_4_cost_attribution.py   # Track spend by team
```

## Key Principle

You can't debug what you can't see. Agent failures are subtle:
- The agent "works" but gives wrong answers (quality regression)
- The agent works but takes 45 seconds (latency creep)
- The agent works but costs $0.50/request (cost explosion)

Observability for agents means tracking quality, latency, AND cost — not just errors.
