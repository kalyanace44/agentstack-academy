# Lab 05: Deployment Patterns

> Deploy AI agents to production — K8s, serverless, queue-based, and edge patterns.

## Labs

| Lab | Pattern | What You Build |
|-----|---------|----------------|
| 5.1 | Kubernetes | Production K8s manifests with HPA, PDB, topology spread |
| 5.2 | Queue-Based | SQS/Redis queue workers with backpressure and DLQ |
| 5.3 | Serverless | Lambda/Cloud Run agent with cold-start optimization |
| 5.4 | Multi-Region | Active-active deployment with failover routing |

## Prerequisites

```bash
pip install pyyaml   # For K8s manifest generation
# Optional: kubectl, docker, aws-cli for live deployment
```

## Quick Start

```bash
cd labs/05-deployment-patterns
python lab_1_k8s_deploy.py       # Generate + explain K8s manifests
python lab_2_queue_workers.py    # Build a queue-based agent pipeline
python lab_3_serverless.py       # Serverless agent with cold-start tricks
python lab_4_multi_region.py     # Active-active with health-based routing
```

## Key Principle

AI agents are NOT regular web services. They have:
- 10-60s latency per request (LLM calls)
- Bursty, unpredictable load
- High memory usage (large contexts)
- External API dependencies that fail

Your deployment architecture must account for all of these.
