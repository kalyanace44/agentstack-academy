# Lab 8.2: LangGraph Workflow — Agent Pipelines as Config

## Architecture

```
┌───────┐     ┌──────────┐     ┌────────────────────────┐     ┌────────┐
│ Input │────▶│ Classify  │────▶│ Route (conditional)    │────▶│ Verify │
│       │     │ (gpt-mini)│     │                        │     │        │
└───────┘     └──────────┘     │  billing → billing_agent│     └───┬────┘
                                │  technical → tech_agent │         │
                                │  account → acct_agent   │    ┌────▼────┐
                                └────────────────────────┘    │APPROVED │→ END
                                                              │ESCALATE │→ on-call
                                                              └─────────┘
```

## Why

Agent workflows without a framework = spaghetti `if/else` chains.
LangGraph lets you define the flow as a GRAPH — nodes do work, edges route.

The key insight: your workflow is config. The code just executes the graph.

## Setup

```bash
pip install langgraph langchain-openai
make run        # Process a sample ticket through the graph
make visualize  # See the graph (outputs PNG)
```

## What You'll Do

1. Read `config.yaml` — nodes, edges, conditional routing
2. `make run` — watch a ticket flow through: classify → route → handle → verify
3. Edit: add a node (e.g., "sentiment_check" before classify)
4. Edit: change routing rules (add "urgent" category → skip to escalation)
5. Challenge: Add a retry loop (if verify fails, re-run the handler once)
6. Challenge: Make billing + account run in parallel (both results → verify)

## Key Insight

The Python file is 40 lines: load config, build graph, run.
All logic is in the YAML — nodes, edges, conditions, models.
