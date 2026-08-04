"""Lab 1.5: Agent-to-Agent Communication — Google A2A Protocol

The A2A (Agent-to-Agent) protocol by Google (April 2025) is the
HTTP for AI agents — a standard for agent discovery, task delegation,
and inter-agent communication across frameworks and companies.

What you'll build:
- Agent Cards (capability manifests — "here's what I can do")
- A2A Task lifecycle (submitted → working → completed/failed)
- Agent discovery via .well-known registry
- Multi-agent pipeline: OrchestratorAgent → CreditAgent + FraudAgent

Real-world use: your LangChain agent can delegate to someone else's
CrewAI agent without any shared codebase.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# ── A2A Core Types ────────────────────────────────────────────────────────────

class TaskState(Enum):
    SUBMITTED  = "submitted"
    WORKING    = "working"
    COMPLETED  = "completed"
    FAILED     = "failed"
    CANCELLED  = "cancelled"


@dataclass
class AgentCapability:
    name: str
    description: str
    input_schema: dict     # JSON Schema for what this skill accepts
    output_schema: dict    # JSON Schema for what it returns


@dataclass
class AgentCard:
    """
    Published at /.well-known/agent.json — lets other agents discover this one.
    Think of it as an API spec + business card combined.
    """
    name: str
    description: str
    url: str               # Where to send tasks
    version: str
    capabilities: list[AgentCapability]
    auth: dict = field(default_factory=lambda: {"scheme": "bearer"})
    provider: str = "AgentStack Academy"

    def to_json(self) -> str:
        return json.dumps({
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "version": self.version,
            "provider": {"name": self.provider},
            "authentication": self.auth,
            "skills": [
                {
                    "id": c.name,
                    "name": c.name,
                    "description": c.description,
                    "inputModes": ["application/json"],
                    "outputModes": ["application/json"],
                }
                for c in self.capabilities
            ],
        }, indent=2)


@dataclass
class Message:
    role: str    # "user" | "agent"
    parts: list[dict]   # text, data, file parts

    @staticmethod
    def text(role: str, content: str) -> "Message":
        return Message(role=role, parts=[{"type": "text", "text": content}])

    @staticmethod
    def data(role: str, payload: dict) -> "Message":
        return Message(role=role, parts=[{"type": "data", "data": payload}])

    def get_text(self) -> str:
        return " ".join(p.get("text", "") for p in self.parts if p.get("type") == "text")

    def get_data(self) -> dict:
        for p in self.parts:
            if p.get("type") == "data":
                return p["data"]
        return {}


@dataclass
class Task:
    """Unit of work sent from one agent to another."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    skill: str = ""
    state: TaskState = TaskState.SUBMITTED
    messages: list[Message] = field(default_factory=list)
    artifacts: list[dict] = field(default_factory=list)   # Results
    error: str = ""
    created_at: float = field(default_factory=time.time)
    completed_at: float = 0.0

    def add_message(self, msg: Message):
        self.messages.append(msg)

    def complete(self, result: dict):
        self.state = TaskState.COMPLETED
        self.artifacts.append({"name": "result", "parts": [{"type": "data", "data": result}]})
        self.completed_at = time.time()

    def fail(self, error: str):
        self.state = TaskState.FAILED
        self.error = error
        self.completed_at = time.time()

    @property
    def latency_ms(self) -> float:
        return (self.completed_at - self.created_at) * 1000 if self.completed_at else 0


# ── Agent Registry (Discovery) ────────────────────────────────────────────────

class AgentRegistry:
    """
    Simulates a .well-known discovery service.
    In production: DNS + HTTPS fetch to https://agent.example.com/.well-known/agent.json
    """
    def __init__(self):
        self._cards: dict[str, AgentCard] = {}
        self._agents: dict[str, "BaseA2AAgent"] = {}

    def register(self, agent: "BaseA2AAgent"):
        self._cards[agent.card.url] = agent.card
        self._agents[agent.card.url] = agent
        print(f"  📋 Registered: {agent.card.name} @ {agent.card.url}")

    def discover(self, skill: str) -> list[AgentCard]:
        """Find agents that have a matching skill."""
        results = []
        for card in self._cards.values():
            if any(c.name == skill for c in card.capabilities):
                results.append(card)
        return results

    def send_task(self, url: str, task: Task) -> Task:
        """Route a task to the target agent."""
        agent = self._agents.get(url)
        if not agent:
            task.fail(f"Agent not found at {url}")
            return task
        return agent.handle(task)


# Singleton registry
registry = AgentRegistry()


# ── Base A2A Agent ─────────────────────────────────────────────────────────────

class BaseA2AAgent:
    """Any agent that speaks A2A — framework agnostic."""

    def __init__(self, card: AgentCard):
        self.card = card
        self.tasks_handled = 0
        registry.register(self)

    def handle(self, task: Task) -> Task:
        task.state = TaskState.WORKING
        try:
            result = self.run_skill(task.skill, task.messages)
            task.complete(result)
        except Exception as e:
            task.fail(str(e))
        self.tasks_handled += 1
        return task

    def run_skill(self, skill: str, messages: list[Message]) -> dict:
        raise NotImplementedError

    def delegate(self, skill: str, payload: dict, context: str = "") -> dict:
        """Find the right agent and delegate a task to it."""
        candidates = registry.discover(skill)
        if not candidates:
            raise RuntimeError(f"No agent found with skill: {skill}")

        target = candidates[0]
        task = Task(skill=skill)
        task.add_message(Message.text("user", context))
        task.add_message(Message.data("user", payload))

        result_task = registry.send_task(target.url, task)
        if result_task.state == TaskState.FAILED:
            raise RuntimeError(f"Delegated task failed: {result_task.error}")

        # Extract result from artifacts
        for artifact in result_task.artifacts:
            for part in artifact.get("parts", []):
                if part.get("type") == "data":
                    return part["data"]
        return {}


# ── Specialist Agents ──────────────────────────────────────────────────────────

class CreditScoringAgent(BaseA2AAgent):
    """
    Specialist: scores credit applications.
    Published skill: "credit_score"
    """

    def __init__(self):
        super().__init__(AgentCard(
            name="CreditScoringAgent",
            description="Evaluates creditworthiness from income, history, and employment",
            url="agents://credit-scoring/v1",
            version="1.0",
            capabilities=[
                AgentCapability(
                    name="credit_score",
                    description="Score a credit application (0-100 risk, lower = safer)",
                    input_schema={"income": "number", "credit_history_years": "number", "defaults": "number"},
                    output_schema={"risk_score": "number", "approved": "boolean", "limit": "number"},
                )
            ],
        ))

    def run_skill(self, skill: str, messages: list[Message]) -> dict:
        if skill != "credit_score":
            raise ValueError(f"Unknown skill: {skill}")

        data = messages[-1].get_data()
        income = data.get("income", 0)
        history = data.get("credit_history_years", 0)
        defaults = data.get("defaults", 0)

        # Scoring logic
        risk = 100 - (
            min(income / 5000, 40) +        # income contribution (max 40)
            min(history * 3, 30) +          # history contribution (max 30)
            max(0, 20 - defaults * 10)      # defaults penalty
        )
        risk = max(0, min(100, risk))
        approved = risk < 60 and defaults == 0
        limit = int(income * 6 * (1 - risk / 100)) if approved else 0

        return {"risk_score": round(risk, 1), "approved": approved, "credit_limit": limit}


class FraudDetectionAgent(BaseA2AAgent):
    """
    Specialist: detects suspicious patterns in applications.
    Published skill: "fraud_check"
    """

    def __init__(self):
        super().__init__(AgentCard(
            name="FraudDetectionAgent",
            description="Detects fraud signals in financial applications",
            url="agents://fraud-detection/v1",
            version="1.0",
            capabilities=[
                AgentCapability(
                    name="fraud_check",
                    description="Check an application for fraud signals",
                    input_schema={"applicant_id": "string", "income": "number", "address_changes": "number"},
                    output_schema={"fraud_score": "number", "signals": "list", "block": "boolean"},
                )
            ],
        ))

    def run_skill(self, skill: str, messages: list[Message]) -> dict:
        if skill != "fraud_check":
            raise ValueError(f"Unknown skill: {skill}")

        data = messages[-1].get_data()
        signals = []
        fraud_score = 0.0

        income = data.get("income", 0)
        address_changes = data.get("address_changes", 0)
        applicant_id = data.get("applicant_id", "")

        if income > 1_000_000:
            signals.append("Unusually high income declared")
            fraud_score += 0.4
        if address_changes > 3:
            signals.append(f"High address churn: {address_changes} changes in 12 months")
            fraud_score += 0.3
        if applicant_id in ("BLOCKED_001", "BLOCKED_002"):
            signals.append("Applicant ID on watchlist")
            fraud_score += 0.8

        fraud_score = min(1.0, fraud_score)
        return {
            "fraud_score": round(fraud_score, 2),
            "signals": signals,
            "block": fraud_score > 0.5,
        }


class LoanOrchestratorAgent(BaseA2AAgent):
    """
    Orchestrator: receives loan applications, delegates to specialists.
    Knows nothing about credit scoring or fraud logic —
    it just routes to the right agents via A2A.
    """

    def __init__(self):
        super().__init__(AgentCard(
            name="LoanOrchestratorAgent",
            description="End-to-end loan application processor",
            url="agents://loan-orchestrator/v1",
            version="1.0",
            capabilities=[
                AgentCapability(
                    name="process_loan",
                    description="Full loan application: fraud check + credit score + decision",
                    input_schema={"applicant_id": "string", "income": "number", "credit_history_years": "number"},
                    output_schema={"decision": "string", "limit": "number", "reason": "string"},
                )
            ],
        ))

    def run_skill(self, skill: str, messages: list[Message]) -> dict:
        if skill != "process_loan":
            raise ValueError(f"Unknown skill: {skill}")

        data = messages[-1].get_data()
        app_id = data.get("applicant_id", "unknown")

        print(f"\n    🎯 Orchestrator processing: {app_id}")

        # Step 1: Fraud check (delegate to FraudDetectionAgent via A2A)
        print(f"       → Delegating fraud_check to {registry.discover('fraud_check')[0].name}")
        fraud = self.delegate("fraud_check", {
            "applicant_id": app_id,
            "income": data.get("income", 0),
            "address_changes": data.get("address_changes", 0),
        }, context=f"Fraud check for loan application {app_id}")

        print(f"       ← Fraud score: {fraud['fraud_score']}, Block: {fraud['block']}")

        if fraud["block"]:
            return {
                "decision": "rejected",
                "credit_limit": 0,
                "reason": f"Blocked: {'; '.join(fraud['signals'])}",
            }

        # Step 2: Credit scoring (delegate to CreditScoringAgent via A2A)
        print(f"       → Delegating credit_score to {registry.discover('credit_score')[0].name}")
        credit = self.delegate("credit_score", {
            "income": data.get("income", 0),
            "credit_history_years": data.get("credit_history_years", 0),
            "defaults": data.get("defaults", 0),
        }, context=f"Credit score for loan application {app_id}")

        print(f"       ← Risk score: {credit['risk_score']}, Approved: {credit['approved']}, Limit: ₹{credit['credit_limit']:,}")

        return {
            "decision": "approved" if credit["approved"] else "rejected",
            "credit_limit": credit["credit_limit"],
            "risk_score": credit["risk_score"],
            "fraud_score": fraud["fraud_score"],
            "reason": "All checks passed" if credit["approved"] else f"Risk score too high ({credit['risk_score']})",
        }


# ── Demo ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 1.5: Agent-to-Agent Communication (Google A2A Protocol)")
    print("  Discovery → Delegation → Task Lifecycle")
    print("=" * 70)
    print()

    # Boot agents — each registers their Agent Card in the global registry
    print("  AGENT REGISTRATION:")
    fraud_agent  = FraudDetectionAgent()
    credit_agent = CreditScoringAgent()
    orchestrator = LoanOrchestratorAgent()

    # Show Agent Cards
    print(f"\n  AGENT CARDS (/.well-known/agent.json):")
    for agent in [fraud_agent, credit_agent, orchestrator]:
        skills = [c.name for c in agent.card.capabilities]
        print(f"    {agent.card.url:<40} skills: {skills}")

    # Discovery demo
    print(f"\n  DISCOVERY: Who can do 'credit_score'?")
    results = registry.discover("credit_score")
    for r in results:
        print(f"    → Found: {r.name} @ {r.url}")

    # Process loan applications
    print(f"\n  PROCESSING LOAN APPLICATIONS:")
    applications = [
        {"applicant_id": "APP-001", "income": 150000, "credit_history_years": 5, "defaults": 0, "address_changes": 1},
        {"applicant_id": "APP-002", "income": 35000,  "credit_history_years": 1, "defaults": 2, "address_changes": 2},
        {"applicant_id": "BLOCKED_001", "income": 200000, "credit_history_years": 3, "defaults": 0, "address_changes": 5},
        {"applicant_id": "APP-003", "income": 2000000, "credit_history_years": 8, "defaults": 0, "address_changes": 2},
    ]

    print(f"\n  {'ID':<14} {'Decision':<12} {'Limit':>12} {'Reason'}")
    print(f"  {'─'*14} {'─'*12} {'─'*12} {'─'*35}")

    for app in applications:
        task = Task(skill="process_loan")
        task.add_message(Message.data("user", app))
        result_task = registry.send_task("agents://loan-orchestrator/v1", task)

        if result_task.state == TaskState.COMPLETED:
            r = result_task.artifacts[0]["parts"][0]["data"]
            icon = "✅" if r["decision"] == "approved" else "❌"
            limit_str = f"₹{r['credit_limit']:>10,}" if r['credit_limit'] > 0 else f"{'—':>12}"
            print(f"  {app['applicant_id']:<14} {icon} {r['decision']:<10} {limit_str}  {r['reason'][:40]}")
        else:
            print(f"  {app['applicant_id']:<14} ERROR: {result_task.error}")

    # Stats
    print(f"\n  {'─' * 66}")
    print(f"  AGENT STATS:")
    for agent in [fraud_agent, credit_agent, orchestrator]:
        print(f"    {agent.card.name:<28}: {agent.tasks_handled} tasks handled")

    print(f"\n  💡 KEY A2A CONCEPTS DEMONSTRATED:")
    print("    • Agent Card  — published capability manifest (/.well-known/agent.json)")
    print("    • Discovery   — find agents by skill, not by hardcoded URL")
    print("    • Task        — unit of work with full lifecycle (submitted→working→done)")
    print("    • Delegation  — orchestrator knows WHAT to do, not HOW")
    print("    • Interop     — fraud agent could be LangChain, credit agent CrewAI")
    print("    • Framework   — zero shared code between agents, just the protocol")
