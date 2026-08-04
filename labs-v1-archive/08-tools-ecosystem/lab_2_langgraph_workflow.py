"""Lab 8.2: LangGraph Workflows — State Machine Agents

Build a state machine agent with conditional branching, loops, and human-in-the-loop.
Pattern: each node is a function, edges are conditions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable


class NodeStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class State:
    """Mutable state that flows through the graph."""
    messages: list[dict] = field(default_factory=list)
    intent: str = ""
    confidence: float = 0.0
    context: list[str] = field(default_factory=list)
    response: str = ""
    needs_human: bool = False
    steps_taken: list[str] = field(default_factory=list)
    error: str = ""


class StateGraph:
    """Minimal LangGraph-style state machine."""

    def __init__(self):
        self.nodes: dict[str, Callable] = {}
        self.edges: dict[str, list[tuple[Callable | None, str]]] = {}
        self.entry_point: str = ""

    def add_node(self, name: str, fn: Callable):
        self.nodes[name] = fn
        if not self.entry_point:
            self.entry_point = name

    def add_edge(self, from_node: str, to_node: str):
        """Unconditional edge."""
        self.edges.setdefault(from_node, []).append((None, to_node))

    def add_conditional_edge(self, from_node: str, condition: Callable, routes: dict[str, str]):
        """Conditional edge: condition(state) returns a key, routes maps key→node."""
        def router(state):
            result = condition(state)
            return routes.get(result, "END")
        self.edges.setdefault(from_node, []).append((router, "CONDITIONAL"))

    def run(self, initial_state: State, max_steps: int = 10) -> State:
        """Execute the graph from entry point."""
        current = self.entry_point
        state = initial_state
        steps = 0

        while current != "END" and steps < max_steps:
            if current not in self.nodes:
                break

            # Execute node
            state.steps_taken.append(current)
            state = self.nodes[current](state)
            steps += 1

            # Find next node
            edges = self.edges.get(current, [])
            if not edges:
                break

            next_node = "END"
            for condition, target in edges:
                if condition is None:
                    next_node = target
                    break
                else:
                    result = condition(state)
                    if result != "END":
                        next_node = result
                        break

            current = next_node

        return state


# --- Build a credit application workflow ---

def classify_intent(state: State) -> State:
    """Node: Classify the customer's intent."""
    msg = state.messages[-1]["content"].lower() if state.messages else ""
    if any(w in msg for w in ["apply", "credit", "loan", "limit"]):
        state.intent = "credit_application"
        state.confidence = 0.9
    elif any(w in msg for w in ["status", "check", "where"]):
        state.intent = "status_check"
        state.confidence = 0.85
    elif any(w in msg for w in ["complaint", "issue", "problem", "angry"]):
        state.intent = "complaint"
        state.confidence = 0.8
    else:
        state.intent = "general"
        state.confidence = 0.4
    return state


def retrieve_context(state: State) -> State:
    """Node: Retrieve relevant knowledge for the intent."""
    kb = {
        "credit_application": [
            "Credit limit range: ₹50K - ₹10L based on income and score",
            "Required docs: PAN, Aadhaar, 3 months bank statements",
            "Processing time: 24-48 hours after document submission",
        ],
        "status_check": [
            "Applications are processed in 24-48 hours",
            "Status can be: submitted, under_review, approved, rejected",
        ],
        "complaint": [
            "Escalation policy: complaints must be acknowledged within 2 hours",
            "Compensation: credit of ₹100 for service delays > 72 hours",
        ],
    }
    state.context = kb.get(state.intent, ["Please contact support for more information."])
    return state


def generate_response(state: State) -> State:
    """Node: Generate response using context."""
    context_str = " | ".join(state.context)
    state.response = f"[{state.intent}] Based on our knowledge: {context_str}"
    return state


def escalate_to_human(state: State) -> State:
    """Node: Flag for human handoff."""
    state.needs_human = True
    state.response = "I'm connecting you with a specialist who can help better with this."
    return state


def route_by_intent(state: State) -> str:
    """Conditional: route based on intent and confidence."""
    if state.confidence < 0.5:
        return "escalate"
    if state.intent == "complaint":
        return "escalate"
    return "retrieve"


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 8.2: LangGraph Workflows — State Machine Agents")
    print("  Conditional branching, routing, and human-in-the-loop")
    print("=" * 70)
    print()

    # Build graph
    graph = StateGraph()
    graph.add_node("classify", classify_intent)
    graph.add_node("retrieve", retrieve_context)
    graph.add_node("respond", generate_response)
    graph.add_node("escalate", escalate_to_human)

    # Edges
    graph.add_conditional_edge("classify", route_by_intent, {
        "retrieve": "retrieve",
        "escalate": "escalate",
    })
    graph.add_edge("retrieve", "respond")

    # Test cases
    test_cases = [
        "I want to apply for a credit card with ₹5L limit",
        "Where is my application? I submitted it 3 days ago",
        "I have a serious complaint about your service",
        "What's the weather like today?",
    ]

    for msg in test_cases:
        state = State(messages=[{"role": "user", "content": msg}])
        result = graph.run(state)
        human = "👤 HUMAN" if result.needs_human else "🤖 AI"
        print(f"  Input:  \"{msg[:55]}...\"" if len(msg) > 55 else f"  Input:  \"{msg}\"")
        print(f"  Path:   {' → '.join(result.steps_taken)}")
        print(f"  Handler: {human}")
        print(f"  Output: {result.response[:70]}...")
        print()

    print("  ✅ State machine routes requests through the right pipeline")
    print("  💡 LangGraph adds: checkpointing, streaming, time-travel debugging")
