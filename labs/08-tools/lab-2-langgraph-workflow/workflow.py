"""
workflow.py — Execute a LangGraph-style workflow from config.yaml
40 lines of glue. Config defines the entire pipeline.
"""
import yaml
import sys

with open("config.yaml") as f:
    config = yaml.safe_load(f)

workflow = config["workflow"]
nodes = config["nodes"]
edges = config["edges"]
settings = config["settings"]


class State:
    """Simple state container passed between nodes."""
    def __init__(self, input_text: str):
        self.input = input_text
        self.category: str | None = None
        self.resolution: str | None = None
        self.verification: str | None = None
        self.history: list[str] = []


def execute_node(node_name: str, state: State) -> State:
    """Execute a single node (simulated — in prod this calls LLM)."""
    node = nodes[node_name]
    state.history.append(node_name)

    if node["type"] == "llm":
        # In production: call litellm.completion(model=node["model"], messages=[...])
        # For demo: simulate responses
        if node_name == "classify":
            # Simulate classification
            text = state.input.lower()
            if any(w in text for w in ["payment", "refund", "invoice", "charge"]):
                state.category = "billing"
            elif any(w in text for w in ["error", "bug", "crash", "api", "500"]):
                state.category = "technical"
            elif any(w in text for w in ["login", "password", "access", "permission"]):
                state.category = "account"
            else:
                state.category = "general"
            print(f"    [{node_name}] → category: {state.category} (model: {node['model']})")

        elif node_name.startswith("handle_"):
            state.resolution = f"Resolved via {node_name} using {node['model']}"
            tools = node.get("tools", [])
            print(f"    [{node_name}] → resolved (model: {node['model']}, tools: {tools})")

        elif node_name == "verify":
            state.verification = "APPROVED"
            print(f"    [{node_name}] → {state.verification}")

    elif node["type"] == "conditional":
        target = node["branches"].get(getattr(state, node["condition"].split(".")[-1]))
        print(f"    [{node_name}] → routing to: {target}")
        if target:
            execute_node(target, state)

    elif node["type"] == "action":
        print(f"    [{node_name}] → {node['action']} (notify: {node.get('notify', 'none')})")

    return state


def run_workflow(input_text: str) -> dict:
    """Run the full workflow graph."""
    state = State(input_text)
    iteration = 0

    # Follow edges from START
    current = "classify"  # First node after START

    while current and iteration < settings["max_iterations"]:
        execute_node(current, state)
        iteration += 1

        # Find next node via edges
        next_node = None
        for edge in edges:
            frm = edge["from"]
            if isinstance(frm, list):
                if current in frm or any(current.startswith(f"handle_") for f in frm if "handle" in f):
                    next_node = edge["to"]
                    break
            elif frm == current:
                if edge.get("type") == "conditional":
                    continue  # Handled inside the node
                if "condition" in edge:
                    cond_field = edge["condition"].split(".")[-1].split(" ")[0]
                    cond_val = edge["condition"].split("== '")[1].rstrip("'") if "==" in edge["condition"] else None
                    if getattr(state, cond_field, None) == cond_val:
                        next_node = edge["to"]
                        break
                else:
                    next_node = edge["to"]
                    break

        if next_node == "END" or next_node is None:
            break
        if next_node == current:
            break  # Prevent self-loops
        current = next_node

    return {
        "decision": state.verification or "completed",
        "category": state.category,
        "resolution": state.resolution,
        "path": " → ".join(state.history),
    }


if __name__ == "__main__":
    tickets = [
        "I was charged twice for my subscription last month",
        "API returns 500 error when calling /users endpoint",
        "I forgot my password and can't log in",
        "What are your business hours?",
    ]

    print("═" * 60)
    print(f"  Workflow: {workflow['name']}")
    print(f"  {workflow['description']}")
    print("═" * 60)

    for ticket in tickets:
        print(f"\n  📩 Ticket: \"{ticket[:50]}...\"")
        result = run_workflow(ticket)
        print(f"  📋 Path: {result['path']}")
        print(f"  ✅ Result: {result['decision']}")
