"""Lab 1.2: Multi-Agent Collaboration

Build two agents that collaborate on a task:
- ResearchAgent: gathers information
- WriterAgent: synthesizes into a report

Demonstrates: message passing, agent roles, coordination patterns.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field


# --- Message protocol between agents ---

@dataclass
class AgentMessage:
    """A message passed between agents."""
    sender: str
    receiver: str
    content: str
    msg_type: str = "text"  # text, request, response, done
    metadata: dict = field(default_factory=dict)


class MessageBus:
    """Simple message bus for agent communication."""

    def __init__(self):
        self.messages: list[AgentMessage] = []
        self.subscribers: dict[str, list] = {}

    def send(self, msg: AgentMessage):
        self.messages.append(msg)
        if msg.receiver in self.subscribers:
            for callback in self.subscribers[msg.receiver]:
                callback(msg)

    def subscribe(self, agent_name: str, callback):
        self.subscribers.setdefault(agent_name, []).append(callback)

    def get_history(self, agent_name: str) -> list[AgentMessage]:
        return [m for m in self.messages if m.sender == agent_name or m.receiver == agent_name]


# --- Agent base class ---

class BaseAgent:
    """Base agent with message handling."""

    def __init__(self, name: str, role: str, bus: MessageBus):
        self.name = name
        self.role = role
        self.bus = bus
        self.bus.subscribe(name, self.handle_message)
        self.output: str = ""

    def handle_message(self, msg: AgentMessage):
        raise NotImplementedError

    def send(self, receiver: str, content: str, msg_type: str = "text"):
        self.bus.send(AgentMessage(
            sender=self.name, receiver=receiver,
            content=content, msg_type=msg_type,
        ))


# --- Research Agent ---

class ResearchAgent(BaseAgent):
    """Gathers information from multiple sources."""

    def __init__(self, bus: MessageBus):
        super().__init__("researcher", "Research and gather factual information", bus)
        self.knowledge_base = {
            "agent architectures": {
                "react": "ReAct combines reasoning traces with tool actions. Published by Yao et al. 2022.",
                "tool_use": "Function calling lets LLMs invoke external tools. OpenAI, Anthropic, Google all support it.",
                "multi_agent": "Multiple specialized agents collaborate. Frameworks: CrewAI, AutoGen, LangGraph.",
                "planning": "Tree-of-thought, plan-and-execute patterns for complex multi-step tasks.",
            },
            "deployment challenges": {
                "latency": "Agent loops add 3-10x latency vs single LLM call. Mitigation: parallel tool calls, caching.",
                "cost": "Each reasoning step = more tokens. GPT-4 agents can cost $0.10-$1.00 per task.",
                "reliability": "Agents fail 20-40% on complex tasks. Need retries, fallbacks, human-in-the-loop.",
                "observability": "Hard to debug reasoning chains. Need tracing (LangSmith, Arize) + structured logging.",
            },
            "production patterns": {
                "circuit_breaker": "Stop calling failed tools. States: closed → open → half-open.",
                "rate_limiting": "Prevent runaway agents from burning through API budgets.",
                "timeout": "Kill agent loops after N steps or T seconds. Prevent infinite loops.",
                "human_in_loop": "Escalate to humans when confidence is low or stakes are high.",
            },
        }

    def handle_message(self, msg: AgentMessage):
        if msg.msg_type == "request":
            research = self.research(msg.content)
            self.send(msg.sender, research, msg_type="response")

    def research(self, topic: str) -> str:
        """Research a topic and return findings."""
        findings = []
        topic_lower = topic.lower()

        for category, items in self.knowledge_base.items():
            if any(word in topic_lower for word in category.split()):
                findings.append(f"\n## {category.title()}\n")
                for key, value in items.items():
                    findings.append(f"- **{key}**: {value}")

        if not findings:
            return f"Limited information found on: {topic}. Recommend external research."

        return "\n".join(findings)


# --- Writer Agent ---

class WriterAgent(BaseAgent):
    """Synthesizes research into clear, structured reports."""

    def __init__(self, bus: MessageBus):
        super().__init__("writer", "Synthesize information into clear reports", bus)
        self._pending_research: list[str] = []

    def handle_message(self, msg: AgentMessage):
        if msg.msg_type == "response":
            self._pending_research.append(msg.content)

    def request_research(self, topic: str):
        """Ask the researcher for information."""
        self.send("researcher", topic, msg_type="request")

    def write_report(self, title: str) -> str:
        """Synthesize all gathered research into a report."""
        research = "\n".join(self._pending_research)

        report = f"""# {title}

## Executive Summary

This report covers the current state of {title.lower()}, including architectures,
deployment challenges, and production patterns for operating AI agents at scale.

## Findings

{research}

## Recommendations

1. **Start simple** — Use ReAct for single-task agents before moving to multi-agent
2. **Instrument everything** — Add tracing from day one, not after the first outage
3. **Set budgets** — Token limits and timeouts prevent runaway costs
4. **Plan for failure** — Circuit breakers + human escalation for high-stakes decisions

## Conclusion

Production AI agents require the same operational rigor as any distributed system,
plus additional concerns around cost, non-determinism, and reasoning quality.

---
*Generated by: WriterAgent + ResearchAgent collaboration*
*Research sources: {len(self._pending_research)} topics analyzed*
"""
        self.output = report
        return report


# --- Orchestrator ---

def run_multi_agent_task(topic: str) -> str:
    """Orchestrate a research + writing task across two agents."""
    bus = MessageBus()
    researcher = ResearchAgent(bus)
    writer = WriterAgent(bus)

    print(f"🔍 ResearchAgent: researching '{topic}'...")

    # Writer requests research on multiple aspects
    subtopics = [
        f"{topic} architectures",
        f"{topic} deployment challenges",
        f"{topic} production patterns",
    ]

    for subtopic in subtopics:
        print(f"   📨 Requesting: {subtopic}")
        writer.request_research(subtopic)

    # Writer synthesizes
    print(f"\n✍️  WriterAgent: synthesizing report...")
    report = writer.write_report(f"Production AI Agents: {topic}")

    print(f"\n📊 Message bus: {len(bus.messages)} messages exchanged")
    return report


# --- Run ---

if __name__ == "__main__":
    print("=" * 60)
    print("  LAB 1.2: Multi-Agent Collaboration")
    print("  Pattern: Research Agent + Writer Agent")
    print("=" * 60)
    print()

    report = run_multi_agent_task("AI Agents")

    print("\n" + "─" * 60)
    print("GENERATED REPORT:")
    print("─" * 60)
    print(report)
