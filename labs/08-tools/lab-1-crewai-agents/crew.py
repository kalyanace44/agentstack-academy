"""
crew.py — 25 lines. Config does the thinking.
"""
import yaml
from crewai import Agent, Task, Crew, Process

# Load config
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Create agents from config
agents = {}
for name, cfg in config["agents"].items():
    agents[name] = Agent(
        role=cfg["role"],
        goal=cfg["goal"],
        backstory=cfg["backstory"],
        llm=cfg["llm"],
        verbose=cfg.get("verbose", False),
    )

# Create tasks from config
tasks = []
for name, cfg in config["tasks"].items():
    tasks.append(Task(
        description=cfg["description"],
        agent=agents[cfg["agent"]],
        expected_output=cfg["expected_output"],
    ))

# Run crew
crew = Crew(
    agents=list(agents.values()),
    tasks=tasks,
    process=Process.sequential if config["crew"]["process"] == "sequential" else Process.hierarchical,
    verbose=config["crew"].get("verbose", True),
)

if __name__ == "__main__":
    import sys
    topic = sys.argv[1] if len(sys.argv) > 1 else "AI agent deployment best practices"
    result = crew.kickoff(inputs={"topic": topic})
    print(f"\n{'='*60}\nFINAL OUTPUT:\n{'='*60}\n{result}")
