"""Lab 8.1: Framework Comparison — LangChain vs CrewAI vs DSPy vs AutoGen

Compare agent frameworks on 5 axes:
1. Complexity (lines of code for same task)
2. Flexibility (how easy to customize)
3. Observability (debugging support)
4. Production-readiness (error handling, scaling)
5. Best use case

This lab doesn't require installing the frameworks — it demonstrates
the patterns and trade-offs through simulated implementations.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FrameworkProfile:
    name: str
    paradigm: str
    loc_for_basic_agent: int
    loc_for_multi_agent: int
    streaming_support: bool
    builtin_memory: bool
    builtin_tools: int
    observability: str  # "excellent", "good", "basic", "minimal"
    production_ready: str
    best_for: str
    weakness: str
    example_code: str


FRAMEWORKS = [
    FrameworkProfile(
        name="LangChain / LangGraph",
        paradigm="Chain/Graph composition",
        loc_for_basic_agent=25,
        loc_for_multi_agent=80,
        streaming_support=True,
        builtin_memory=True,
        builtin_tools=150,
        observability="excellent",
        production_ready="High (LangSmith tracing, error recovery)",
        best_for="Complex workflows with state machines, conditional branching",
        weakness="Abstraction overhead, version churn, large dependency tree",
        example_code="""
# LangGraph: State machine with conditional routing
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)
graph.add_node("classify", classify_intent)
graph.add_node("research", research_topic)
graph.add_node("respond", generate_response)
graph.add_conditional_edges("classify", route_by_intent, {
    "technical": "research",
    "simple": "respond",
})
app = graph.compile()
""",
    ),
    FrameworkProfile(
        name="CrewAI",
        paradigm="Role-based multi-agent",
        loc_for_basic_agent=15,
        loc_for_multi_agent=40,
        streaming_support=True,
        builtin_memory=True,
        builtin_tools=50,
        observability="good",
        production_ready="Medium (needs custom error handling)",
        best_for="Multi-agent collaboration with defined roles and goals",
        weakness="Less control over execution flow, opinionated structure",
        example_code="""
# CrewAI: Role-based agents with goals
from crewai import Agent, Task, Crew

researcher = Agent(role="Research Analyst", goal="Find accurate data",
    backstory="Expert at finding information")
writer = Agent(role="Content Writer", goal="Write clear reports",
    backstory="Skilled technical writer")

research_task = Task(description="Research {topic}", agent=researcher)
write_task = Task(description="Write report from research", agent=writer)

crew = Crew(agents=[researcher, writer], tasks=[research_task, write_task])
result = crew.kickoff(inputs={"topic": "AI deployment"})
""",
    ),
    FrameworkProfile(
        name="DSPy",
        paradigm="Programmatic prompt optimization",
        loc_for_basic_agent=20,
        loc_for_multi_agent=60,
        streaming_support=False,
        builtin_memory=False,
        builtin_tools=10,
        observability="basic",
        production_ready="Medium (research-oriented, growing ecosystem)",
        best_for="Optimizing prompts systematically without manual engineering",
        weakness="Steep learning curve, less intuitive than chat-based frameworks",
        example_code="""
# DSPy: Optimized prompts without manual engineering
import dspy

class CreditScorer(dspy.Module):
    def __init__(self):
        self.scorer = dspy.ChainOfThought("income, credit_history -> risk_score, reasoning")

    def forward(self, income, credit_history):
        return self.scorer(income=income, credit_history=credit_history)

# Auto-optimize prompts on training data
optimizer = dspy.BootstrapFewShot(metric=accuracy_metric)
optimized = optimizer.compile(CreditScorer(), trainset=train_examples)
""",
    ),
    FrameworkProfile(
        name="AutoGen / AG2",
        paradigm="Conversation-driven multi-agent",
        loc_for_basic_agent=20,
        loc_for_multi_agent=50,
        streaming_support=True,
        builtin_memory=True,
        builtin_tools=30,
        observability="good",
        production_ready="Medium-High (Microsoft backed, enterprise features)",
        best_for="Multi-agent conversations, human-in-the-loop workflows",
        weakness="Conversation overhead, harder to constrain agent behavior",
        example_code="""
# AutoGen: Conversation-driven collaboration
from autogen import AssistantAgent, UserProxyAgent

coder = AssistantAgent("coder", llm_config=llm_config,
    system_message="Write Python code to solve problems")
reviewer = AssistantAgent("reviewer", llm_config=llm_config,
    system_message="Review code for bugs and improvements")
executor = UserProxyAgent("executor", code_execution_config={"work_dir": "output"})

# Agents chat until task is done
executor.initiate_chat(coder, message="Build a credit risk calculator")
""",
    ),
]


# --- Decision Matrix ---

def print_comparison():
    print(f"\n  {'Framework':<22} {'LOC(1)':<7} {'LOC(N)':<7} {'Tools':<6} {'Memory':<7} {'Observe':<10} {'Prod-Ready':<12}")
    print(f"  {'─'*22} {'─'*7} {'─'*7} {'─'*6} {'─'*7} {'─'*10} {'─'*12}")
    for f in FRAMEWORKS:
        print(f"  {f.name:<22} {f.loc_for_basic_agent:<7} {f.loc_for_multi_agent:<7} {f.builtin_tools:<6} {'✓' if f.builtin_memory else '✗':<7} {f.observability:<10} {f.production_ready[:10]:<12}")


def print_decision_tree():
    print("""
  DECISION TREE: Which framework to use?

  ┌─ Need state machines / conditional routing?
  │   └─ YES → LangGraph
  │
  ├─ Need multiple agents with defined roles?
  │   ├─ Simple collaboration → CrewAI
  │   └─ Complex conversation flows → AutoGen
  │
  ├─ Need to optimize prompts without manual engineering?
  │   └─ YES → DSPy
  │
  ├─ Building a prototype quickly?
  │   └─ CrewAI (least code) or LangChain (most tutorials)
  │
  └─ Need maximum control + production hardening?
      └─ LangGraph + custom middleware (or build from scratch)
""")


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 8.1: Framework Comparison")
    print("  LangChain vs CrewAI vs DSPy vs AutoGen")
    print("=" * 70)

    print_comparison()

    print(f"\n  {'─' * 66}")
    print("  BEST FOR:")
    for f in FRAMEWORKS:
        print(f"    {f.name:<22}: {f.best_for}")

    print(f"\n  WEAKNESSES:")
    for f in FRAMEWORKS:
        print(f"    {f.name:<22}: {f.weakness}")

    print_decision_tree()

    print("  💡 RECOMMENDATION FOR PRODUCTION:")
    print("    • Start with LangGraph if you need complex workflows")
    print("    • Use CrewAI for quick multi-agent prototypes")
    print("    • Add DSPy when you want to eliminate manual prompt engineering")
    print("    • Consider building from scratch (like our earlier labs!) for maximum control")
    print("    • Whatever you choose: add observability from day 1")
