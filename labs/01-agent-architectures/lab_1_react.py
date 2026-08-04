"""Lab 1.1: ReAct Agent from Scratch

Build a ReAct (Reasoning + Acting) agent that:
1. Thinks about what to do
2. Takes an action (calls a tool)
3. Observes the result
4. Repeats until done

No frameworks — pure Python + OpenAI API.
"""
from __future__ import annotations

import json
import httpx

# --- Tools (the actions our agent can take) ---

def search_web(query: str) -> str:
    """Simulate a web search."""
    # In production, use a real search API
    knowledge = {
        "python gc": "Python uses reference counting + generational garbage collection. gc.collect() forces a collection cycle.",
        "kubernetes hpa": "HPA scales pods based on CPU/memory or custom metrics. Default sync period is 15s.",
        "react pattern ai": "ReAct = Reasoning + Acting. Agent thinks step-by-step, calls tools, observes results.",
        "vector database": "Vector DBs store embeddings for similarity search. Popular: Pinecone, Qdrant, Weaviate, pgvector.",
    }
    for key, answer in knowledge.items():
        if key in query.lower():
            return answer
    return f"No results found for: {query}"


def calculate(expression: str) -> str:
    """Evaluate a math expression safely."""
    try:
        # Only allow safe math operations
        allowed = set("0123456789+-*/.() ")
        if not all(c in allowed for c in expression):
            return "Error: invalid characters in expression"
        result = eval(expression)  # Safe because we validated chars
        return str(result)
    except Exception as e:
        return f"Error: {e}"


def get_current_time() -> str:
    """Get current UTC time."""
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


# Tool registry
TOOLS = {
    "search_web": {
        "fn": search_web,
        "description": "Search the web for information. Input: search query string.",
    },
    "calculate": {
        "fn": calculate,
        "description": "Evaluate a math expression. Input: expression like '2 + 2' or '100 * 0.15'.",
    },
    "get_current_time": {
        "fn": get_current_time,
        "description": "Get the current UTC time. No input needed.",
    },
}


# --- The ReAct Agent ---

REACT_SYSTEM_PROMPT = """You are a helpful assistant that solves problems step by step.

You have access to these tools:
{tools}

To use a tool, respond with EXACTLY this format:
THOUGHT: <your reasoning about what to do next>
ACTION: <tool_name>
INPUT: <input to the tool>

After seeing the result, continue reasoning:
THOUGHT: <what the result tells you>
ACTION: <next tool or FINISH>

When you have the final answer:
THOUGHT: <final reasoning>
ACTION: FINISH
ANSWER: <your final answer>

Always start with THOUGHT. Never skip the reasoning step.
"""


class ReActAgent:
    """A ReAct agent that reasons and acts in a loop."""

    def __init__(self, model: str = "gpt-4o-mini", base_url: str = None, api_key: str = None):
        self.model = model
        self.base_url = base_url or "https://api.openai.com/v1"
        self.api_key = api_key
        self.max_steps = 8
        self.trace: list[dict] = []

    def run(self, question: str) -> str:
        """Run the agent on a question. Returns the final answer."""
        # Build system prompt with tool descriptions
        tool_desc = "\n".join(f"- {name}: {info['description']}" for name, info in TOOLS.items())
        system = REACT_SYSTEM_PROMPT.format(tools=tool_desc)

        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": question},
        ]

        for step in range(self.max_steps):
            # Get LLM response
            response = self._call_llm(messages)
            self.trace.append({"step": step + 1, "llm_output": response})
            print(f"\n{'='*60}")
            print(f"Step {step + 1}:")
            print(response)

            # Parse the response
            if "ACTION: FINISH" in response:
                # Extract final answer
                answer = response.split("ANSWER:")[-1].strip() if "ANSWER:" in response else response
                self.trace.append({"final_answer": answer})
                return answer

            # Extract action and input
            action, action_input = self._parse_action(response)
            if not action:
                messages.append({"role": "assistant", "content": response})
                messages.append({"role": "user", "content": "Please respond with THOUGHT/ACTION/INPUT format."})
                continue

            # Execute the tool
            if action in TOOLS:
                observation = TOOLS[action]["fn"](action_input)
            else:
                observation = f"Error: Unknown tool '{action}'. Available: {list(TOOLS.keys())}"

            print(f"\n  OBSERVATION: {observation}")
            self.trace.append({"action": action, "input": action_input, "observation": observation})

            # Add to conversation
            messages.append({"role": "assistant", "content": response})
            messages.append({"role": "user", "content": f"OBSERVATION: {observation}"})

        return "Agent reached max steps without finishing."

    def _call_llm(self, messages: list[dict]) -> str:
        """Call the LLM API."""
        import os
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or os.environ.get('OPENAI_API_KEY', 'demo')}",
        }
        payload = {"model": self.model, "messages": messages, "temperature": 0.2, "max_tokens": 500}

        try:
            resp = httpx.post(f"{self.base_url}/chat/completions", json=payload, headers=headers, timeout=30)
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]
        except Exception as e:
            # Fallback: simulate a response for demo purposes
            return self._simulate_response(messages)

    def _simulate_response(self, messages: list[dict]) -> str:
        """Simulate LLM response for offline demo."""
        user_msg = messages[-1]["content"]
        if "OBSERVATION:" in user_msg:
            return "THOUGHT: I now have the information I need.\nACTION: FINISH\nANSWER: Based on my research, " + user_msg.split("OBSERVATION:")[-1].strip()
        return "THOUGHT: I need to search for this information.\nACTION: search_web\nINPUT: " + messages[1]["content"]

    @staticmethod
    def _parse_action(response: str) -> tuple[str | None, str]:
        """Parse ACTION and INPUT from LLM response."""
        action = None
        action_input = ""
        for line in response.split("\n"):
            if line.startswith("ACTION:"):
                action = line.replace("ACTION:", "").strip()
            elif line.startswith("INPUT:"):
                action_input = line.replace("INPUT:", "").strip()
        return action, action_input


# --- Run the demo ---

if __name__ == "__main__":
    print("=" * 60)
    print("  LAB 1.1: ReAct Agent")
    print("  Pattern: Reasoning + Acting in a loop")
    print("=" * 60)

    agent = ReActAgent()

    # Test questions
    questions = [
        "What is the ReAct pattern in AI agents?",
        "What is 15% of 2400 plus 500?",
    ]

    for q in questions:
        print(f"\n{'─'*60}")
        print(f"QUESTION: {q}")
        answer = agent.run(q)
        print(f"\n✅ FINAL ANSWER: {answer}")
        print(f"   Steps taken: {len([t for t in agent.trace if 'action' in t])}")
        agent.trace = []
