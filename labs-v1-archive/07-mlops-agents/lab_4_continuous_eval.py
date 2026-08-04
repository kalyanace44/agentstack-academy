"""Lab 7.4: Continuous Evaluation — Detect Quality Regressions

Monitor model quality on production traffic in real-time.
Alert when performance degrades with statistical significance.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field


@dataclass
class EvalWindow:
    model: str
    metric: str
    baseline_mean: float
    baseline_std: float
    current_values: list[float] = field(default_factory=list)
    alerts: list[str] = field(default_factory=list)


class ContinuousEval:
    """Monitor production quality and detect regressions."""

    def __init__(self, alert_threshold: float = 0.05, min_samples: int = 30):
        self.alert_threshold = alert_threshold
        self.min_samples = min_samples
        self.windows: dict[str, EvalWindow] = {}

    def set_baseline(self, model: str, metric: str, mean: float, std: float):
        key = f"{model}:{metric}"
        self.windows[key] = EvalWindow(model=model, metric=metric, baseline_mean=mean, baseline_std=std)

    def observe(self, model: str, metric: str, value: float) -> str | None:
        """Record an observation. Returns alert message if regression detected."""
        key = f"{model}:{metric}"
        if key not in self.windows:
            return None
        window = self.windows[key]
        window.current_values.append(value)

        if len(window.current_values) < self.min_samples:
            return None

        # Z-test against baseline
        current_mean = sum(window.current_values[-50:]) / len(window.current_values[-50:])
        n = len(window.current_values[-50:])
        se = window.baseline_std / math.sqrt(n) if n > 0 else 1

        z = (current_mean - window.baseline_mean) / se if se > 0 else 0
        p = 2 * (1 - 0.5 * (1 + math.erf(abs(z) / math.sqrt(2))))

        # Check for degradation (metric dropped)
        if p < self.alert_threshold and current_mean < window.baseline_mean:
            change_pct = (current_mean - window.baseline_mean) / window.baseline_mean * 100
            alert = f"🚨 {model}/{metric} DEGRADED: {window.baseline_mean:.3f} → {current_mean:.3f} ({change_pct:+.1f}%, p={p:.4f})"
            window.alerts.append(alert)
            return alert
        return None


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 7.4: Continuous Evaluation")
    print("  Detect quality regressions on production traffic")
    print("=" * 70)
    print()

    evaluator = ContinuousEval(alert_threshold=0.05, min_samples=20)

    # Set baselines from historical data
    evaluator.set_baseline("gpt-4o", "quality_score", mean=0.85, std=0.08)
    evaluator.set_baseline("gpt-4o", "latency", mean=1.5, std=0.3)
    evaluator.set_baseline("claude-sonnet", "quality_score", mean=0.88, std=0.06)

    print("  📈 Baselines set:")
    print("    gpt-4o/quality: mean=0.85, std=0.08")
    print("    gpt-4o/latency: mean=1.5s, std=0.3s")
    print("    claude-sonnet/quality: mean=0.88, std=0.06")
    print()

    # Phase 1: Normal traffic (no alerts)
    print("  PHASE 1: Normal traffic (50 requests)")
    alerts = []
    for _ in range(50):
        evaluator.observe("gpt-4o", "quality_score", random.gauss(0.84, 0.08))
        evaluator.observe("gpt-4o", "latency", random.gauss(1.6, 0.3))
        a = evaluator.observe("claude-sonnet", "quality_score", random.gauss(0.87, 0.06))
        if a:
            alerts.append(a)
    print(f"    Alerts: {len(alerts)} {'✅ (none expected)' if not alerts else '⚠️'}")

    # Phase 2: GPT-4o degrades (simulating a provider issue)
    print("\n  PHASE 2: gpt-4o quality drops (provider regression)")
    alerts = []
    for _ in range(40):
        a = evaluator.observe("gpt-4o", "quality_score", random.gauss(0.72, 0.10))
        if a:
            alerts.append(a)
        evaluator.observe("claude-sonnet", "quality_score", random.gauss(0.87, 0.06))

    for alert in alerts[:3]:
        print(f"    {alert}")
    print(f"    Total alerts: {len(alerts)}")

    # Phase 3: Latency spike
    print("\n  PHASE 3: gpt-4o latency spike")
    alerts = []
    for _ in range(30):
        a = evaluator.observe("gpt-4o", "latency", random.gauss(3.5, 0.5))
        if a:
            alerts.append(a)

    for alert in alerts[:2]:
        print(f"    {alert}")

    print(f"\n  {'─' * 66}")
    print("  💡 ACTIONS ON ALERT:")
    print("    1. Auto-route traffic to healthy provider (claude-sonnet)")
    print("    2. Page on-call engineer if degradation persists > 5 min")
    print("    3. Log incident for provider SLA tracking")
    print("    4. Trigger canary rollback if this was a recently deployed model")
    print("\n  ✅ Continuous eval catches regressions humans would miss for hours")
