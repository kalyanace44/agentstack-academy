"""Lab 6.4: Cost Attribution — Per-Team, Per-Model Tracking + Alerts

Track and alert on AI spend across teams, models, and tasks.
Essential for multi-team environments where cost accountability matters.
"""
from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field


MODEL_PRICING = {  # USD per 1M tokens (input/output avg)
    "gpt-4o": 6.25,
    "gpt-4o-mini": 0.375,
    "claude-sonnet": 9.0,
    "claude-haiku": 2.4,
}


@dataclass
class CostAlert:
    team: str
    alert_type: str  # "daily_limit", "spike", "anomaly"
    message: str
    current_spend: float
    threshold: float
    timestamp: float = field(default_factory=time.time)


class CostTracker:
    """Track AI costs per team/model with alerting."""

    def __init__(self):
        self.spend_by_team: dict[str, float] = defaultdict(float)
        self.spend_by_model: dict[str, float] = defaultdict(float)
        self.spend_by_team_model: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self.daily_budgets: dict[str, float] = {}
        self.alerts: list[CostAlert] = []
        self.total_tokens = 0
        self.total_cost = 0.0
        self._hourly_spend: dict[str, list[float]] = defaultdict(list)

    def set_budget(self, team: str, daily_usd: float):
        self.daily_budgets[team] = daily_usd

    def record(self, team: str, model: str, tokens: int):
        """Record token usage and calculate cost."""
        price_per_m = MODEL_PRICING.get(model, 5.0)
        cost = tokens / 1_000_000 * price_per_m

        self.spend_by_team[team] += cost
        self.spend_by_model[model] += cost
        self.spend_by_team_model[team][model] += cost
        self.total_tokens += tokens
        self.total_cost += cost
        self._hourly_spend[team].append(cost)

        # Check alerts
        self._check_budget(team)
        self._check_spike(team, cost)

    def _check_budget(self, team: str):
        if team in self.daily_budgets:
            budget = self.daily_budgets[team]
            spent = self.spend_by_team[team]
            if spent >= budget * 0.8 and not any(
                a.team == team and a.alert_type == "daily_limit" for a in self.alerts
            ):
                self.alerts.append(CostAlert(
                    team=team, alert_type="daily_limit",
                    message=f"Team '{team}' at {spent/budget*100:.0f}% of daily budget (${spent:.4f}/${budget:.4f})",
                    current_spend=spent, threshold=budget,
                ))

    def _check_spike(self, team: str, cost: float):
        history = self._hourly_spend[team]
        if len(history) > 10:
            avg = sum(history[:-1]) / (len(history) - 1)
            if cost > avg * 5 and avg > 0:  # 5x spike
                self.alerts.append(CostAlert(
                    team=team, alert_type="spike",
                    message=f"Cost spike for '{team}': ${cost:.6f} vs avg ${avg:.6f} (5x+)",
                    current_spend=cost, threshold=avg * 5,
                ))

    def report(self) -> str:
        lines = ["COST ATTRIBUTION REPORT", "=" * 50]
        lines.append(f"Total spend: ${self.total_cost:.4f} ({self.total_tokens:,} tokens)")
        lines.append(f"\nBy Team:")
        for team, cost in sorted(self.spend_by_team.items(), key=lambda x: -x[1]):
            budget = self.daily_budgets.get(team)
            pct = f" ({cost/budget*100:.0f}% of ${budget:.2f} budget)" if budget else ""
            lines.append(f"  {team:<12}: ${cost:.4f}{pct}")
        lines.append(f"\nBy Model:")
        for model, cost in sorted(self.spend_by_model.items(), key=lambda x: -x[1]):
            lines.append(f"  {model:<16}: ${cost:.4f}")
        return "\n".join(lines)


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 6.4: Cost Attribution")
    print("  Per-team, per-model cost tracking with budget alerts")
    print("=" * 70)
    print()

    import random
    tracker = CostTracker()

    # Set budgets
    tracker.set_budget("lending", 0.05)
    tracker.set_budget("support", 0.02)
    tracker.set_budget("fraud", 0.10)

    # Simulate traffic
    teams = ["lending", "support", "fraud", "kyc"]
    usage_patterns = {
        "lending": ("gpt-4o", 2000),        # Expensive model, large prompts
        "support": ("gpt-4o-mini", 800),    # Cheap model, small prompts
        "fraud": ("claude-sonnet", 1500),   # Premium for accuracy
        "kyc": ("gpt-4o-mini", 500),        # Simple extraction
    }

    for _ in range(50):
        team = random.choice(teams)
        model, base_tokens = usage_patterns[team]
        tokens = base_tokens + random.randint(-200, 500)
        tracker.record(team, model, tokens)

    # One big spike from lending (simulate a bug)
    tracker.record("lending", "gpt-4o", 50000)

    print(f"  {tracker.report()}")

    if tracker.alerts:
        print(f"\n  🚨 ALERTS ({len(tracker.alerts)}):")
        for alert in tracker.alerts:
            icon = "⚠️" if alert.alert_type == "daily_limit" else "🔥"
            print(f"    {icon} [{alert.alert_type}] {alert.message}")

    # Recommendations
    print(f"\n  {'─' * 66}")
    print("  💡 COST OPTIMIZATION RECOMMENDATIONS:")
    for team, models in tracker.spend_by_team_model.items():
        if "gpt-4o" in models and models["gpt-4o"] > 0.01:
            print(f"    • {team}: Consider GPT-4o-mini for {models['gpt-4o']/tracker.spend_by_team[team]*100:.0f}% of traffic (potential 94% savings)")

    print("\n  ✅ Cost attribution enables accountability and optimization")
