"""Lab 1.4: Self-Critique Agent — Reflection and Retry

Build an agent that evaluates its own output and retries if quality is low.
Pattern: generate → critique → revise (until quality threshold met).

This prevents bad outputs from reaching users and improves reliability.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class CritiqueResult:
    score: float          # 0-1 quality score
    passed: bool          # meets threshold?
    feedback: str         # what to improve
    issues: list[str] = field(default_factory=list)


class QualityCritic:
    """Evaluates output quality using heuristic rules.

    In production, use an LLM as judge (GPT-4 critiquing GPT-3.5 output).
    This demo uses rule-based checks for zero-dependency execution.
    """

    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold

    def critique(self, query: str, response: str) -> CritiqueResult:
        """Score a response and provide feedback."""
        issues = []
        score = 1.0

        # Check: response length (too short = probably bad)
        if len(response) < 50:
            issues.append("Response too short — lacks detail")
            score -= 0.3

        # Check: response addresses the query
        query_keywords = set(re.findall(r'\w{4,}', query.lower()))
        response_keywords = set(re.findall(r'\w{4,}', response.lower()))
        overlap = query_keywords & response_keywords
        if len(overlap) < len(query_keywords) * 0.3:
            issues.append("Response doesn't address key terms from the query")
            score -= 0.3

        # Check: has structure (bullet points, paragraphs, headers)
        if len(response) > 200 and '\n' not in response:
            issues.append("Long response without structure — add paragraphs or bullet points")
            score -= 0.15

        # Check: no hedging/filler
        filler_phrases = ["i think", "maybe", "possibly", "i'm not sure", "it depends"]
        filler_count = sum(1 for p in filler_phrases if p in response.lower())
        if filler_count > 1:
            issues.append(f"Too much hedging ({filler_count} filler phrases) — be more direct")
            score -= 0.1 * filler_count

        # Check: factual markers (numbers, specifics)
        has_specifics = bool(re.search(r'\d+', response)) or any(
            w in response.lower() for w in ["specifically", "for example", "such as"]
        )
        if not has_specifics and len(response) > 100:
            issues.append("Lacks specifics — add examples or data points")
            score -= 0.1

        score = max(0.0, min(1.0, score))
        feedback = "; ".join(issues) if issues else "Response looks good."

        return CritiqueResult(
            score=round(score, 2),
            passed=score >= self.threshold,
            feedback=feedback,
            issues=issues,
        )


class SelfCritiqueAgent:
    """Agent that generates, critiques, and revises its output.

    Loop: generate → critique → if fails, revise with feedback → repeat
    Max retries prevent infinite loops.
    """

    def __init__(self, max_retries: int = 3, quality_threshold: float = 0.7):
        self.max_retries = max_retries
        self.critic = QualityCritic(threshold=quality_threshold)
        self.trace: list[dict] = []

    def generate(self, query: str, feedback: str = "") -> str:
        """Generate a response. If feedback is provided, incorporate it.

        In production: call LLM with the query + critique feedback.
        Demo: simulate improving responses based on feedback.
        """
        base_responses = {
            "deploy": "To deploy an AI agent to production:\n\n1. Containerize with Docker (multi-stage build, non-root user)\n2. Deploy to Kubernetes with HPA for auto-scaling\n3. Add health checks (liveness + readiness probes)\n4. Set resource limits (2Gi RAM minimum for LLM contexts)\n5. Configure circuit breakers for provider failover\n\nExample: Our credit scoring agent handles 500 req/min with 3 replicas, scaling to 20 during peak.",
            "cost": "Managing AI agent costs requires three layers:\n\n1. Per-request budget: cap tokens at 4096 for simple tasks, 16K for complex\n2. Per-team daily limits: engineering gets 1M tokens/day, support gets 200K\n3. Model routing: use GPT-4o-mini (₹0.15/1M) for 80% of tasks, GPT-4o (₹2.50/1M) only when quality score drops below 0.8\n\nReal example: switching 60% of our routing to GPT-4o-mini saved ₹3.5L/month with zero quality regression.",
            "default": "I can help with that.",
        }

        # Pick best matching response
        for key, resp in base_responses.items():
            if key in query.lower():
                response = resp
                break
        else:
            response = base_responses["default"]

        # If we have feedback, simulate improvement
        if feedback and "too short" in feedback.lower():
            response += "\n\nAdditional details: This approach has been validated at scale across multiple fintech deployments with 99.9% uptime."
        if feedback and "structure" in feedback.lower():
            response = response.replace(". ", ".\n")
        if feedback and "specifics" in feedback.lower():
            response += "\n\nSpecifically, latency p95 is 2.3s, error rate 0.1%, cost per request ₹0.02."

        return response

    def run(self, query: str) -> dict:
        """Run the generate-critique-revise loop."""
        self.trace = []
        feedback = ""

        for attempt in range(self.max_retries + 1):
            # Generate
            response = self.generate(query, feedback)

            # Critique
            critique = self.critic.critique(query, response)

            self.trace.append({
                "attempt": attempt + 1,
                "response_length": len(response),
                "score": critique.score,
                "passed": critique.passed,
                "issues": critique.issues,
            })

            if critique.passed:
                return {
                    "response": response,
                    "quality_score": critique.score,
                    "attempts": attempt + 1,
                    "trace": self.trace,
                }

            # Prepare feedback for next attempt
            feedback = critique.feedback

        # Max retries exhausted — return best effort
        return {
            "response": response,
            "quality_score": critique.score,
            "attempts": self.max_retries + 1,
            "warning": "Max retries reached — response may be suboptimal",
            "trace": self.trace,
        }


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 1.4: Self-Critique Agent")
    print("  Pattern: Generate → Critique → Revise (until quality threshold)")
    print("=" * 70)
    print()

    agent = SelfCritiqueAgent(max_retries=3, quality_threshold=0.7)

    queries = [
        "How do I deploy an AI agent to production?",
        "How do I manage AI agent costs?",
        "What is machine learning?",  # Will trigger short response → retry
    ]

    for q in queries:
        print(f"  Q: \"{q}\"")
        print(f"  {'─' * 64}")
        result = agent.run(q)

        for step in result["trace"]:
            status = "✅ PASS" if step["passed"] else "🔄 RETRY"
            print(f"    Attempt {step['attempt']}: score={step['score']:.2f} {status}")
            if step["issues"]:
                for issue in step["issues"]:
                    print(f"      → {issue}")

        print(f"\n  Final: score={result['quality_score']:.2f}, attempts={result['attempts']}")
        print(f"  Response: {result['response'][:120]}...")
        print()
