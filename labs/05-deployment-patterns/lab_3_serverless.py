"""Lab 5.3: Serverless Agent Deployment

Deploy AI agents as serverless functions (Lambda/Cloud Run pattern).
Covers cold-start optimization, timeout handling, and cost efficiency.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class InvocationResult:
    status: str  # "success", "timeout", "cold_start", "error"
    response: str
    latency_ms: float
    cold_start: bool
    billed_ms: int
    memory_mb: int = 256


class ServerlessAgent:
    """Simulates a serverless-deployed agent with cold start behavior."""

    def __init__(self, memory_mb: int = 512, timeout_ms: int = 30000):
        self.memory_mb = memory_mb
        self.timeout_ms = timeout_ms
        self._initialized = False
        self._init_time_ms = 800.0  # Cold start: load SDK, tokenizer
        self._last_invocation = 0.0
        self._idle_timeout = 5.0  # Seconds before instance is recycled
        self.invocations = 0
        self.cold_starts = 0
        self.timeouts = 0

    def invoke(self, event: dict) -> InvocationResult:
        """Invoke the agent function."""
        start = time.perf_counter()
        cold_start = False

        # Check if instance is cold
        if not self._initialized or (time.time() - self._last_invocation > self._idle_timeout):
            cold_start = True
            self._initialized = True
            self.cold_starts += 1
            time.sleep(self._init_time_ms / 1000)  # Simulate init

        self._last_invocation = time.time()
        self.invocations += 1

        # Simulate processing
        query = event.get("query", "")
        processing_time_ms = len(query) * 2 + 100  # Simulate proportional to input

        if processing_time_ms > self.timeout_ms:
            self.timeouts += 1
            elapsed = (time.perf_counter() - start) * 1000
            return InvocationResult(
                status="timeout", response="", latency_ms=elapsed,
                cold_start=cold_start, billed_ms=self.timeout_ms, memory_mb=self.memory_mb,
            )

        time.sleep(processing_time_ms / 10000)  # Scale down for demo
        response = f"Processed: {query[:50]}..."
        elapsed = (time.perf_counter() - start) * 1000

        # Billing: round up to nearest 1ms, min 1ms
        billed = max(1, int(elapsed) + 1)

        return InvocationResult(
            status="success", response=response, latency_ms=round(elapsed, 1),
            cold_start=cold_start, billed_ms=billed, memory_mb=self.memory_mb,
        )

    @property
    def stats(self) -> dict:
        return {
            "invocations": self.invocations,
            "cold_starts": self.cold_starts,
            "cold_start_rate": round(self.cold_starts / max(self.invocations, 1), 2),
            "timeouts": self.timeouts,
        }


# Cold start optimization techniques
OPTIMIZATIONS = {
    "Provisioned concurrency": "Keep N instances warm (AWS Lambda). Cost: ~$15/mo per instance.",
    "Minimal dependencies": "Strip unused packages. Use lambda layers for shared deps.",
    "Lazy loading": "Import heavy modules (torch, transformers) only when needed.",
    "Connection pooling": "Reuse HTTP connections across invocations (global httpx.Client).",
    "Response streaming": "Stream partial responses to avoid timeout on long tasks.",
    "Tiered models": "Use fast model (Haiku) for simple tasks, avoid cold start + slow model.",
}


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 5.3: Serverless Agent Deployment")
    print("  Cold starts, timeouts, and cost optimization")
    print("=" * 70)
    print()

    agent = ServerlessAgent(memory_mb=512, timeout_ms=5000)

    # Simulate traffic pattern
    print("  📞 Simulating 10 invocations with gaps...\n")
    events = [
        {"query": "What's my credit limit?", "delay": 0},
        {"query": "Show recent transactions", "delay": 0.5},
        {"query": "Explain this charge", "delay": 0.5},
        {"query": "Calculate EMI for 5L over 3 years", "delay": 0.5},
        {"query": "Transfer status", "delay": 6},  # Gap → cold start
        {"query": "Block my card", "delay": 0},
        {"query": "Fraud alert details", "delay": 0.5},
        {"query": "Account balance", "delay": 0.5},
        {"query": "Close account", "delay": 6},  # Gap → cold start
        {"query": "Final statement", "delay": 0},
    ]

    total_billed = 0
    for event in events:
        if event["delay"]:
            time.sleep(min(event["delay"], 0.01))  # Scale down for demo
            if event["delay"] > 5:
                time.sleep(0.01)
                agent._last_invocation -= 10  # Force cold start

        result = agent.invoke(event)
        cs = "🧊" if result.cold_start else "  "
        print(f"    {cs} {event['query']:<35} {result.latency_ms:>6.1f}ms  billed:{result.billed_ms}ms  [{result.status}]")
        total_billed += result.billed_ms

    stats = agent.stats
    print(f"\n  📊 Stats:")
    print(f"    Total invocations: {stats['invocations']}")
    print(f"    Cold starts: {stats['cold_starts']} ({stats['cold_start_rate']*100:.0f}%)")
    print(f"    Total billed: {total_billed}ms")
    print(f"    Cost (Lambda 512MB): ${total_billed / 1000 * 0.0000083:.6f}")

    print(f"\n  {'─' * 66}")
    print("  COLD START OPTIMIZATION TECHNIQUES:")
    for name, desc in OPTIMIZATIONS.items():
        print(f"    • {name}: {desc}")

    print("\n  ✅ Serverless is ideal for bursty agent workloads with 0 idle cost")
