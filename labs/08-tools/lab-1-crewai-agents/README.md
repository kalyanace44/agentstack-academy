# Lab 8.1: CrewAI — Multi-Agent Teams in Config

## Architecture

```
                     config.yaml
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐
         │Research│→│ Writer │→│Reviewer│
         │ Agent  │ │ Agent  │ │ Agent  │
         └────────┘ └────────┘ └────────┘
              │                      │
              ▼                      ▼
         ┌────────┐           ┌────────┐
         │ Tools  │           │ Output │
         │(search)│           │(report)│
         └────────┘           └────────┘
```

## Why

You don't build agent orchestration from scratch.
CrewAI = define agents + tasks in config, Python is just glue.
Swap agents, reorder tasks, add tools — all without touching code.

## Setup

```bash
pip install crewai crewai-tools
make run topic="Kubernetes autoscaling for AI agents"
```

## What You'll Do

1. Read `config.yaml` — agents, tasks, process order
2. `make run` — watch 3 agents collaborate
3. Edit config: change an agent's model, add a task, swap order
4. Challenge: Add a 4th agent (FactChecker) between writer and reviewer
5. Challenge: Switch process to "hierarchical" (one agent manages others)

## Key Insight

The Python file (`crew.py`) is 25 lines. All intelligence is in config.
