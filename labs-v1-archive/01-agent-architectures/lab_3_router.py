"""Lab 1.3: Router Agent — Delegate to Specialist Sub-Agents

Build a router that analyzes incoming requests and delegates to the
right specialist agent. Pattern: one brain, many hands.

Use case: A customer support system that routes to billing, technical,
or account specialists based on intent.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentResult:
    agent: str
    response: str
    confidence: float
    metadata: dict = field(default_factory=dict)


# --- Specialist Agents ---

class BillingAgent:
    name = "billing"
    keywords = {"payment", "invoice", "charge", "refund", "bill", "subscription", "price", "cost", "plan"}

    def handle(self, query: str) -> str:
        return (
            f"[BillingAgent] I can help with your billing question. "
            f"Looking into: '{query[:60]}...'\n"
            f"Your current plan: Pro (₹2,499/mo). Last payment: June 1. Next: July 1."
        )


class TechnicalAgent:
    name = "technical"
    keywords = {"error", "bug", "crash", "deploy", "api", "timeout", "integration", "code", "server", "log"}

    def handle(self, query: str) -> str:
        return (
            f"[TechnicalAgent] Let me investigate your technical issue.\n"
            f"Query: '{query[:60]}...'\n"
            f"Checking: API status ✓, Deploy logs ✓, Error traces..."
        )


class AccountAgent:
    name = "account"
    keywords = {"password", "login", "access", "permission", "team", "invite", "role", "security", "2fa"}

    def handle(self, query: str) -> str:
        return (
            f"[AccountAgent] I'll help with your account settings.\n"
            f"Query: '{query[:60]}...'\n"
            f"Your account: kalyan@vegapay.in, Role: Admin, 2FA: enabled."
        )


class GeneralAgent:
    name = "general"
    keywords: set = set()

    def handle(self, query: str) -> str:
        return f"[GeneralAgent] Let me help with your question: '{query[:80]}...'"


# --- Router Agent ---

class RouterAgent:
    """Routes queries to specialist agents based on intent classification.

    In production, replace keyword matching with:
    - LLM-based classification (GPT-4o-mini is fast + cheap)
    - Embedding similarity (embed query, compare to agent descriptions)
    - Fine-tuned classifier (BERT-based, <5ms latency)
    """

    def __init__(self):
        self.agents = [BillingAgent(), TechnicalAgent(), AccountAgent(), GeneralAgent()]
        self.routing_history: list[dict] = []

    def classify(self, query: str) -> tuple[object, float]:
        """Classify query intent and pick the best agent."""
        query_words = set(query.lower().split())

        scores = []
        for agent in self.agents:
            if not agent.keywords:
                scores.append((agent, 0.1))  # fallback score
                continue
            overlap = query_words & agent.keywords
            score = len(overlap) / max(len(agent.keywords), 1)
            scores.append((agent, score))

        scores.sort(key=lambda x: x[1], reverse=True)
        best_agent, confidence = scores[0]

        # If no strong match, fall back to general
        if confidence < 0.1:
            best_agent = self.agents[-1]  # GeneralAgent
            confidence = 0.5

        return best_agent, confidence

    def route(self, query: str) -> AgentResult:
        """Route a query to the appropriate specialist."""
        agent, confidence = self.classify(query)
        response = agent.handle(query)

        result = AgentResult(
            agent=agent.name,
            response=response,
            confidence=confidence,
            metadata={"query_length": len(query), "routing_method": "keyword"},
        )
        self.routing_history.append({"query": query[:50], "agent": agent.name, "confidence": confidence})
        return result


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 1.3: Router Agent")
    print("  Pattern: Classify intent → delegate to specialist")
    print("=" * 70)
    print()

    router = RouterAgent()

    queries = [
        "I was charged twice for my subscription last month",
        "Our API is returning 500 errors on the /users endpoint",
        "How do I add a team member and set their permissions?",
        "I need to deploy a new version but the pipeline is stuck",
        "Can you tell me about your product roadmap for Q3?",
        "I forgot my password and 2fa isn't working",
        "The server timeout increased after the last code deploy",
        "What's the refund policy for annual plans?",
    ]

    for q in queries:
        result = router.route(q)
        print(f"  Q: \"{q}\"")
        print(f"  → Routed to: {result.agent} (confidence: {result.confidence:.0%})")
        print(f"  → {result.response[:100]}")
        print()

    # Routing summary
    print(f"  {'─' * 66}")
    print(f"  ROUTING SUMMARY")
    from collections import Counter
    counts = Counter(h["agent"] for h in router.routing_history)
    for agent, count in counts.most_common():
        print(f"    {agent:<12}: {count} queries ({count/len(queries)*100:.0f}%)")
