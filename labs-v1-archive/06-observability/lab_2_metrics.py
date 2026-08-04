"""Lab 6.2: Prometheus Metrics for AI Agents

Build a metrics collection system that tracks agent-specific KPIs:
- Request rate, latency (p50/p95/p99), error rate
- Token usage and cost per team/model
- Cache hit rate
- Active tasks and queue depth
"""
from __future__ import annotations

import time
import math
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class MetricPoint:
    value: float
    timestamp: float = field(default_factory=time.time)
    labels: dict = field(default_factory=dict)


class Histogram:
    """Simple histogram for latency percentiles."""

    def __init__(self):
        self.values: list[float] = []

    def observe(self, value: float):
        self.values.append(value)

    def percentile(self, p: float) -> float:
        if not self.values:
            return 0.0
        sorted_vals = sorted(self.values)
        idx = int(len(sorted_vals) * p / 100)
        return sorted_vals[min(idx, len(sorted_vals) - 1)]

    @property
    def count(self) -> int:
        return len(self.values)

    @property
    def mean(self) -> float:
        return sum(self.values) / max(len(self.values), 1)


class AgentMetrics:
    """Production metrics collector for AI agent observability."""

    def __init__(self):
        self.requests_total = 0
        self.errors_total = 0
        self.tokens_total = 0
        self.cost_total = 0.0
        self.cache_hits = 0
        self.cache_misses = 0

        self.latency = Histogram()
        self.latency_by_model: dict[str, Histogram] = defaultdict(Histogram)
        self.requests_by_team: dict[str, int] = defaultdict(int)
        self.tokens_by_team: dict[str, int] = defaultdict(int)
        self.cost_by_team: dict[str, float] = defaultdict(float)
        self.errors_by_type: dict[str, int] = defaultdict(int)

    def record_request(self, model: str, team: str, latency_s: float, tokens: int = 0, cost: float = 0.0):
        self.requests_total += 1
        self.tokens_total += tokens
        self.cost_total += cost
        self.latency.observe(latency_s)
        self.latency_by_model[model].observe(latency_s)
        self.requests_by_team[team] += 1
        self.tokens_by_team[team] += tokens
        self.cost_by_team[team] += cost

    def record_error(self, error_type: str):
        self.errors_total += 1
        self.errors_by_type[error_type] += 1

    def record_cache(self, hit: bool):
        if hit:
            self.cache_hits += 1
        else:
            self.cache_misses += 1

    def prometheus_exposition(self) -> str:
        """Generate Prometheus text exposition format."""
        lines = []
        lines.append(f"# HELP agent_requests_total Total agent requests")
        lines.append(f"# TYPE agent_requests_total counter")
        lines.append(f"agent_requests_total {self.requests_total}")
        lines.append(f"agent_errors_total {self.errors_total}")
        lines.append(f"agent_tokens_total {self.tokens_total}")
        lines.append(f"agent_cost_usd_total {self.cost_total:.6f}")
        lines.append(f"# HELP agent_latency_seconds Agent request latency")
        lines.append(f"# TYPE agent_latency_seconds summary")
        lines.append(f'agent_latency_seconds{{quantile="0.5"}} {self.latency.percentile(50):.4f}')
        lines.append(f'agent_latency_seconds{{quantile="0.95"}} {self.latency.percentile(95):.4f}')
        lines.append(f'agent_latency_seconds{{quantile="0.99"}} {self.latency.percentile(99):.4f}')
        lines.append(f"agent_cache_hit_ratio {self.cache_hits / max(self.cache_hits + self.cache_misses, 1):.4f}")
        for team, count in self.requests_by_team.items():
            lines.append(f'agent_requests_by_team{{team="{team}"}} {count}')
        for team, cost in self.cost_by_team.items():
            lines.append(f'agent_cost_by_team{{team="{team}"}} {cost:.6f}')
        return "\n".join(lines)

    def dashboard_summary(self) -> dict:
        return {
            "requests": self.requests_total,
            "error_rate": round(self.errors_total / max(self.requests_total, 1), 4),
            "latency_p50": round(self.latency.percentile(50), 3),
            "latency_p95": round(self.latency.percentile(95), 3),
            "latency_p99": round(self.latency.percentile(99), 3),
            "tokens_total": self.tokens_total,
            "cost_total": round(self.cost_total, 4),
            "cache_hit_rate": round(self.cache_hits / max(self.cache_hits + self.cache_misses, 1), 3),
            "top_team_by_cost": max(self.cost_by_team.items(), key=lambda x: x[1])[0] if self.cost_by_team else "n/a",
        }


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 6.2: Prometheus Metrics for AI Agents")
    print("  Track latency, cost, errors, cache — per team and model")
    print("=" * 70)
    print()

    import random
    metrics = AgentMetrics()

    # Simulate 100 requests across teams and models
    teams = ["lending", "support", "fraud", "kyc"]
    models = ["gpt-4o", "gpt-4o-mini", "claude-sonnet"]

    for i in range(100):
        team = random.choice(teams)
        model = random.choice(models)
        latency = random.gauss(1.5, 0.5) if model == "gpt-4o" else random.gauss(0.8, 0.2)
        tokens = random.randint(200, 2000)
        cost = tokens * (0.000003 if "mini" in model else 0.00001)

        # 5% error rate
        if random.random() < 0.05:
            metrics.record_error(random.choice(["timeout", "rate_limit", "provider_error"]))
        else:
            metrics.record_request(model, team, max(0.1, latency), tokens, cost)

        # 30% cache hit
        metrics.record_cache(random.random() < 0.3)

    # Display
    print("  📊 DASHBOARD SUMMARY (100 requests simulated)")
    print("  " + "─" * 64)
    summary = metrics.dashboard_summary()
    for key, val in summary.items():
        print(f"    {key:<20}: {val}")

    print(f"\n  💰 COST BY TEAM:")
    for team, cost in sorted(metrics.cost_by_team.items(), key=lambda x: -x[1]):
        bar = "█" * int(cost / max(metrics.cost_by_team.values()) * 30)
        print(f"    {team:<12} ${cost:.4f}  {bar}")

    print(f"\n  📈 PROMETHEUS EXPOSITION (first 10 lines):")
    for line in metrics.prometheus_exposition().split("\n")[:10]:
        print(f"    {line}")

    print(f"\n  ✅ Metrics ready for Grafana dashboards + alerting")
