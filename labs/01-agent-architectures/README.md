# Lab 01: Agent Architectures

> Build 4 different agent patterns from scratch. Understand when to use each.

## Labs

| Lab | Pattern | What You Build |
|-----|---------|----------------|
| 1.1 | ReAct Agent | Tool-calling agent with reasoning traces |
| 1.2 | Multi-Agent | Two agents collaborating on a task |
| 1.3 | Router Agent | Agent that delegates to specialist sub-agents |
| 1.4 | Critique Loop | Agent with self-reflection and retry |

## Prerequisites

```bash
pip install openai httpx
export OPENAI_API_KEY="your-key"  # or use local Ollama
```

## Quick Start

```bash
cd labs/01-agent-architectures
python lab_1_react.py
python lab_2_multi_agent.py
python lab_3_router.py
python lab_4_critique.py
```
