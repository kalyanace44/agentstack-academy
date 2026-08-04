# Lab 1.1: LiteLLM Proxy — One API, All Providers

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Your App   │────▶│ LiteLLM Proxy│────▶│ OpenAI       │
│  (curl/SDK) │     │  :4000       │────▶│ Anthropic    │
└─────────────┘     └──────────────┘────▶│ Ollama/local │
                                          └──────────────┘
```

## Why This Matters

Without a proxy, every team hardcodes provider SDKs. One provider outage = everything breaks.
With LiteLLM: one endpoint, automatic fallbacks, cost tracking, rate limits — all in config.

## Setup

```bash
cd labs-v2/01-agent-architectures/lab-1-litellm-proxy
docker-compose up -d
```

## What You'll Do

1. Edit `config.yaml` to add your models
2. `docker-compose up -d` — proxy is live
3. `./test.sh` — hit it with curl
4. Break it: remove a model, watch fallback kick in
5. Check spend: `curl localhost:4000/spend/logs`

## Key Learning

- Model aliasing (your code says `gpt-4o`, proxy routes to whatever you want)
- Fallback chains (if OpenAI is down → Anthropic → local)
- Spend tracking per API key
- Rate limiting without code changes
