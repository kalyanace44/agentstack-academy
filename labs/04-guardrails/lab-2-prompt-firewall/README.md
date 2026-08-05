# Lab 4.2: Prompt Firewall — Block Injections Before They Reach the LLM

## Architecture

```
┌──────────┐     ┌───────────────┐     ┌──────────┐
│  User    │────▶│  Firewall     │────▶│  LLM     │
│  Input   │     │  (rules.yaml) │     │          │
└──────────┘     │               │     └──────────┘
                 │  ✗ Block      │
                 │  ⚠ Warn       │
                 │  ✓ Pass       │
                 └───────────────┘
```

## Why

Your LLM will cheerfully follow injection prompts unless you stop them first.
A firewall sits between user input and the model — blocking known attack patterns.

Real attacks:
- "Ignore previous instructions" — role override
- "DAN mode" — jailbreak
- "Repeat your system prompt" — data exfiltration
- Sending 50K tokens — token bomb / cost attack

## Setup

```bash
make test       # Run firewall against attack corpus
```

## What You'll Do

1. Read `rules.yaml` — pattern-based blocking rules
2. `make test` — see what gets blocked vs passed
3. Add a new rule: block "base64 decode" attempts
4. Tune: switch a rule from `block` to `warn` (monitor mode)
5. Challenge: Add a rate limiter (3 blocks = 5min cooldown)
6. Challenge: Set up alert webhook for critical blocks

## Key Insight

The firewall is regex + config. No ML needed for 90% of attacks.
Add new attack patterns as they're discovered — just edit YAML.
