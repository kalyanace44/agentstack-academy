# Lab 04: Guardrails & Safety

> Build production guardrails that protect AI agents from prompt injection, PII leakage, cost explosions, and runaway loops.

## Labs

| Lab | Topic | What You Build |
|-----|-------|----------------|
| 4.1 | PII Scanner | Detect & redact PAN, Aadhaar, CC, emails before they reach LLM providers |
| 4.2 | Prompt Injection | Classify and block adversarial inputs |
| 4.3 | Cost Guardrails | Token budgets, rate limiting, circuit breakers |
| 4.4 | Output Validation | Detect hallucinations, enforce JSON schema, content filters |

## Prerequisites

```bash
pip install fastapi uvicorn httpx
# No API keys needed — all labs run locally
```

## Quick Start

```bash
cd labs/04-guardrails-safety
python lab_1_pii_scanner.py          # See PII detection in action
python lab_2_prompt_injection.py      # Block adversarial inputs
python lab_3_cost_guardrails.py       # Token budgets + circuit breakers
python lab_4_output_validation.py     # Schema enforcement + hallucination check
```

## Key Takeaway

Guardrails aren't optional in production — they're the difference between a demo and a product.
One leaked PAN number = RBI compliance violation. One runaway agent loop = $10K bill overnight.
