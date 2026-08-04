# Lab 5.2: Helm + Kubernetes — Production Deployment

## Architecture

```
┌─────────────────────── K8s Cluster ──────────────────────────┐
│                                                               │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │ agent (HPA) │   │ litellm     │   │ qdrant      │       │
│  │ 2→10 pods   │   │ 2 replicas  │   │ StatefulSet │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
│         ▲                                                     │
│  ┌──────┴──────┐                                             │
│  │  Ingress    │ ← TLS termination                           │
│  │  (nginx)    │                                             │
│  └─────────────┘                                             │
└───────────────────────────────────────────────────────────────┘
```

## Setup

```bash
# Deploy to any K8s cluster (local minikube or cloud)
make deploy         # helm upgrade --install
make status         # kubectl get pods
make test           # smoke test endpoints
make rollback       # helm rollback if broken
```

## What You'll Do

1. Read `values.yaml` — all config in one file
2. `make deploy` — Helm installs everything
3. `make test` — verify endpoints
4. Edit `values.yaml` → change replicas, limits, env vars
5. `make deploy` again — see rolling update (zero downtime)
6. Break it: set memory limit too low → watch pod restart → rollback
