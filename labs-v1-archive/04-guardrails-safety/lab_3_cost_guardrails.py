"""Lab 4.3: Cost Guardrails — Token Budgets, Rate Limiting, Circuit Breakers

Prevent runaway AI agents from bankrupting your company overnight.
Real pattern: an agent in an infinite loop burned $12K in 3 hours at a fintech.

This lab implements three layers of cost protection:
1. Token budget — hard cap per request/session/team
2. Rate limiter — token bucket algorithm (smooth burst handling)
3. Circuit breaker — stop calling providers when they're degraded
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


# --- Layer 1: Token Budget ---

@dataclass
class Budget:
    """Token budget for a team or API key."""
    team: str
    daily_limit: int           # Max tokens per day
    per_request_limit: int     # Max tokens per single request
    daily_used: int = 0
    total_cost_usd: float = 0.0
    reset_at: float = field(default_factory=lambda: time.time() + 86400)

    @property
    def remaining(self) -> int:
        if time.time() > self.reset_at:
            self.daily_used = 0
            self.reset_at = time.time() + 86400
        return max(0, self.daily_limit - self.daily_used)

    def can_spend(self, tokens: int) -> bool:
        """Check if this request is within budget."""
        if tokens > self.per_request_limit:
            return False
        return tokens <= self.remaining

    def spend(self, tokens: int, cost_usd: float = 0.0):
        """Record token usage."""
        self.daily_used += tokens
        self.total_cost_usd += cost_usd


class BudgetManager:
    """Manage token budgets per team."""

    def __init__(self):
        self.budgets: dict[str, Budget] = {}

    def create_budget(self, team: str, daily_limit: int = 1_000_000, per_request: int = 50_000):
        self.budgets[team] = Budget(team=team, daily_limit=daily_limit, per_request_limit=per_request)

    def check(self, team: str, estimated_tokens: int) -> tuple[bool, str]:
        """Check if a request is within budget. Returns (allowed, reason)."""
        budget = self.budgets.get(team)
        if not budget:
            return True, "no budget configured"

        if estimated_tokens > budget.per_request_limit:
            return False, f"request too large ({estimated_tokens} > {budget.per_request_limit} per-request limit)"

        if not budget.can_spend(estimated_tokens):
            return False, f"daily budget exhausted ({budget.daily_used}/{budget.daily_limit} used)"

        return True, "within budget"

    def record(self, team: str, tokens: int, cost_usd: float = 0.0):
        if team in self.budgets:
            self.budgets[team].spend(tokens, cost_usd)


# --- Layer 2: Rate Limiter (Token Bucket) ---

@dataclass
class TokenBucket:
    """Token bucket rate limiter — smooth burst handling."""
    capacity: int          # Max tokens in bucket
    refill_rate: float     # Tokens added per second
    tokens: float = 0.0
    last_refill: float = field(default_factory=time.time)

    def __post_init__(self):
        self.tokens = float(self.capacity)

    def _refill(self):
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

    def try_acquire(self, tokens: int = 1) -> bool:
        """Try to acquire tokens. Returns True if allowed."""
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    @property
    def available(self) -> int:
        self._refill()
        return int(self.tokens)


class RateLimiter:
    """Per-team rate limiter."""

    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        self.rpm = requests_per_minute
        self.burst = burst
        self._buckets: dict[str, TokenBucket] = {}

    def _get_bucket(self, key: str) -> TokenBucket:
        if key not in self._buckets:
            self._buckets[key] = TokenBucket(
                capacity=self.burst,
                refill_rate=self.rpm / 60.0,
            )
        return self._buckets[key]

    def allow(self, team: str) -> tuple[bool, dict]:
        """Check if request is allowed. Returns (allowed, metadata)."""
        bucket = self._get_bucket(team)
        allowed = bucket.try_acquire()
        return allowed, {
            "remaining": bucket.available,
            "limit": self.rpm,
            "reset_in": f"{(self.burst - bucket.available) / (self.rpm / 60.0):.1f}s",
        }


# --- Layer 3: Circuit Breaker ---

class CircuitState(Enum):
    CLOSED = "closed"          # Normal — requests flow through
    OPEN = "open"              # Tripped — all requests rejected
    HALF_OPEN = "half_open"    # Testing — allow one request to test recovery


@dataclass
class CircuitBreaker:
    """Per-provider circuit breaker.

    Prevents cascading failures and protects budgets when a provider is degraded.
    Pattern: closed → (failures exceed threshold) → open → (timeout) → half-open → (success) → closed
    """
    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 3

    state: CircuitState = CircuitState.CLOSED
    failures: int = 0
    successes: int = 0
    last_failure_time: float = 0.0

    def can_execute(self) -> tuple[bool, str]:
        """Check if we should send a request to this provider."""
        if self.state == CircuitState.CLOSED:
            return True, "circuit closed (healthy)"

        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.successes = 0
                return True, "circuit half-open (testing recovery)"
            return False, f"circuit OPEN — provider degraded, retry in {self.recovery_timeout - (time.time() - self.last_failure_time):.0f}s"

        # Half-open: allow limited requests
        return True, "circuit half-open (testing)"

    def record_success(self):
        """Record a successful request."""
        if self.state == CircuitState.HALF_OPEN:
            self.successes += 1
            if self.successes >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failures = 0
                print(f"    ✅ Circuit {self.name}: RECOVERED (closed)")
        else:
            self.failures = max(0, self.failures - 1)

    def record_failure(self):
        """Record a failed request."""
        self.failures += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            print(f"    🔴 Circuit {self.name}: reopened (recovery failed)")
        elif self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN
            print(f"    🔴 Circuit {self.name}: TRIPPED ({self.failures} failures)")


# --- Combined Guardrail Pipeline ---

class GuardrailPipeline:
    """Run all guardrails in sequence before forwarding to LLM."""

    def __init__(self):
        self.budgets = BudgetManager()
        self.rate_limiter = RateLimiter(requests_per_minute=60, burst=10)
        self.circuits: dict[str, CircuitBreaker] = {}
        self.metrics = defaultdict(int)

    def add_circuit(self, provider: str, **kwargs):
        self.circuits[provider] = CircuitBreaker(name=provider, **kwargs)

    def check(self, team: str, provider: str, estimated_tokens: int = 1000) -> tuple[bool, list[str]]:
        """Run full guardrail check. Returns (allowed, reasons)."""
        checks = []

        # 1. Rate limit
        allowed, meta = self.rate_limiter.allow(team)
        if not allowed:
            self.metrics["rate_limited"] += 1
            checks.append(f"❌ Rate limited (remaining: {meta['remaining']}, reset: {meta['reset_in']})")
            return False, checks
        checks.append(f"✓ Rate limit OK (remaining: {meta['remaining']})")

        # 2. Budget
        allowed, reason = self.budgets.check(team, estimated_tokens)
        if not allowed:
            self.metrics["budget_exceeded"] += 1
            checks.append(f"❌ Budget exceeded: {reason}")
            return False, checks
        checks.append(f"✓ Budget OK ({reason})")

        # 3. Circuit breaker
        if provider in self.circuits:
            allowed, reason = self.circuits[provider].can_execute()
            if not allowed:
                self.metrics["circuit_open"] += 1
                checks.append(f"❌ Circuit breaker: {reason}")
                return False, checks
            checks.append(f"✓ Circuit OK ({reason})")

        self.metrics["allowed"] += 1
        return True, checks


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 4.3: Cost Guardrails")
    print("  Three layers: Token Budget → Rate Limiter → Circuit Breaker")
    print("=" * 70)
    print()

    pipeline = GuardrailPipeline()

    # Configure
    pipeline.budgets.create_budget("engineering", daily_limit=500_000, per_request=10_000)
    pipeline.budgets.create_budget("support", daily_limit=100_000, per_request=5_000)
    pipeline.add_circuit("openai", failure_threshold=3, recovery_timeout=5.0)
    pipeline.add_circuit("anthropic", failure_threshold=3, recovery_timeout=5.0)

    # --- Scenario 1: Normal operation ---
    print("─" * 70)
    print("  SCENARIO 1: Normal Operation")
    print("─" * 70)
    allowed, checks = pipeline.check("engineering", "openai", estimated_tokens=2000)
    for c in checks:
        print(f"    {c}")
    print(f"  → {'ALLOWED ✅' if allowed else 'BLOCKED 🚫'}")
    pipeline.budgets.record("engineering", 2000, cost_usd=0.01)

    # --- Scenario 2: Oversized request ---
    print(f"\n{'─' * 70}")
    print("  SCENARIO 2: Request Too Large (50K tokens)")
    print("─" * 70)
    allowed, checks = pipeline.check("support", "openai", estimated_tokens=50_000)
    for c in checks:
        print(f"    {c}")
    print(f"  → {'ALLOWED ✅' if allowed else 'BLOCKED 🚫'}")

    # --- Scenario 3: Rate limiting ---
    print(f"\n{'─' * 70}")
    print("  SCENARIO 3: Burst Traffic (15 requests in 1s)")
    print("─" * 70)
    for i in range(15):
        allowed, checks = pipeline.check("engineering", "openai", estimated_tokens=500)
        if not allowed:
            print(f"    Request {i+1}: RATE LIMITED 🚫")
            break
        else:
            print(f"    Request {i+1}: allowed ✓")
            pipeline.budgets.record("engineering", 500)

    # --- Scenario 4: Circuit breaker trip ---
    print(f"\n{'─' * 70}")
    print("  SCENARIO 4: Provider Degradation → Circuit Trips")
    print("─" * 70)
    circuit = pipeline.circuits["openai"]
    for i in range(4):
        circuit.record_failure()
        print(f"    Failure {i+1}: state={circuit.state.value}, failures={circuit.failures}")

    # Now try to send a request
    allowed, checks = pipeline.check("engineering", "openai", estimated_tokens=1000)
    for c in checks:
        print(f"    {c}")
    print(f"  → {'ALLOWED ✅' if allowed else 'BLOCKED 🚫 (protecting budget + user experience)'}")

    # --- Summary ---
    print(f"\n{'─' * 70}")
    print("  GUARDRAIL STATS")
    print("─" * 70)
    for key, val in pipeline.metrics.items():
        print(f"    {key}: {val}")
    print(f"    engineering budget used: {pipeline.budgets.budgets['engineering'].daily_used:,} / 500,000 tokens")
    print(f"    engineering cost: ${pipeline.budgets.budgets['engineering'].total_cost_usd:.4f}")
