# Lab 08: Tools Ecosystem

> Deep dives into production agent frameworks — when to use what, and how to combine them.

## Labs

| Lab | Framework | What You Build |
|-----|-----------|----------------|
| 8.1 | Framework Comparison | Side-by-side eval of LangChain, CrewAI, DSPy, AutoGen |
| 8.2 | LangGraph Workflows | State machine agents with conditional branching |
| 8.3 | DSPy Optimization | Programmatic prompt optimization (no manual prompting) |
| 8.4 | Self-Hosted Inference | Deploy models locally with vLLM/Ollama |

## Prerequisites

```bash
# Labs run without installing frameworks (simulated for comparison)
# To run against real frameworks:
# pip install langchain crewai dspy-ai autogen
```

## Quick Start

```bash
cd labs/08-tools-ecosystem
python lab_1_framework_comparison.py    # Compare 4 frameworks
python lab_2_langgraph_workflow.py       # State machine agents
python lab_3_dspy_optimization.py       # Programmatic prompts
python lab_4_self_hosted.py             # vLLM/Ollama deployment
```
