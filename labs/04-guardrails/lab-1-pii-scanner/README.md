# Lab 4.1: PII Scanner — Block Sensitive Data with Config Rules

## Architecture

```
┌──────────┐     ┌──────────────┐     ┌──────────┐
│  Request │────▶│  PII Scanner │────▶│  LLM     │
│  (user)  │     │  (middleware)│     │  (clean) │
└──────────┘     └──────────────┘     └──────────┘
                        │
                        ▼ blocked/redacted
                 ┌──────────────┐
                 │  HTTP 451    │
                 │  (rejected)  │
                 └──────────────┘
```

## Why

One PAN number in a prompt sent to US servers = RBI compliance violation.
Configure what to scan, what to block, what to redact — in YAML. No code changes.

## Setup

```bash
make up       # Scanner is live
make test     # Send clean + dirty requests, see blocking in action
```

## What You'll Do

1. Read `rules.yaml` — what PII patterns to detect
2. `make test` — send test payloads through the scanner
3. See: clean requests pass, PII gets redacted, injections get blocked
4. Challenge: Add a new pattern (UPI VPA) to `rules.yaml`
5. Challenge: Change action from "block" to "redact" for email addresses
