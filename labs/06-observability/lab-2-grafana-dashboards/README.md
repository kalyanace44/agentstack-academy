# Lab 6.2: Grafana Dashboards — Monitor Agent Health

## Architecture

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Agent   │────▶│  Prometheus  │────▶│  Grafana     │
│  /metrics│     │  (scrape)    │     │  :3001       │
└──────────┘     └──────────────┘     │  (dashboard) │
                                       └──────────────┘
```

## Why

LangFuse shows individual traces. Grafana shows the big picture:
- Request rate (are we getting busier?)
- Error rate (is something breaking?)
- Latency p95 (are users waiting too long?)
- Cost per hour (are we bleeding money?)
- Active agents (is scaling working?)

## Setup

```bash
make up           # Prometheus + Grafana
make open         # Grafana at localhost:3001 (admin/admin)
make import       # Import pre-built agent dashboard
```

## What You'll Do

1. `docker-compose up -d` — Prometheus + Grafana running
2. Import `dashboard.json` — pre-built agent metrics dashboard
3. Send traffic → watch metrics populate in real-time
4. Set up an alert: "Notify me when error rate > 5%"
5. Challenge: Add a cost panel that shows spend per team per hour
