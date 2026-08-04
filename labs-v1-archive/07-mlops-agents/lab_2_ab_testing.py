"""Lab 7.2: A/B Testing for AI Agents

Split traffic between agent configurations and measure statistical significance.
Use z-test to determine if a new config is actually better.
"""
from __future__ import annotations

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Variant:
    name: str
    model: str
    config: dict = field(default_factory=dict)
    weight: float = 0.5  # Traffic percentage


@dataclass
class Observation:
    variant: str
    success: bool
    latency: float
    tokens: int
    quality_score: float  # 0-1


class ABTest:
    """Run an A/B test between two agent configurations."""

    def __init__(self, name: str, control: Variant, treatment: Variant):
        self.name = name
        self.control = control
        self.treatment = treatment
        self.observations: dict[str, list[Observation]] = {control.name: [], treatment.name: []}

    def assign(self, user_id: str) -> Variant:
        """Deterministic assignment based on user_id hash."""
        bucket = hash(user_id) % 100
        return self.treatment if bucket < self.treatment.weight * 100 else self.control

    def record(self, obs: Observation):
        self.observations[obs.variant].append(obs)

    def analyze(self) -> dict:
        """Run statistical analysis on results."""
        ctrl_obs = self.observations[self.control.name]
        treat_obs = self.observations[self.treatment.name]

        if len(ctrl_obs) < 10 or len(treat_obs) < 10:
            return {"status": "insufficient_data", "min_needed": 30}

        # Quality score comparison (z-test for proportions)
        ctrl_mean = sum(o.quality_score for o in ctrl_obs) / len(ctrl_obs)
        treat_mean = sum(o.quality_score for o in treat_obs) / len(treat_obs)

        ctrl_std = math.sqrt(sum((o.quality_score - ctrl_mean)**2 for o in ctrl_obs) / len(ctrl_obs))
        treat_std = math.sqrt(sum((o.quality_score - treat_mean)**2 for o in treat_obs) / len(treat_obs))

        se = math.sqrt(ctrl_std**2 / len(ctrl_obs) + treat_std**2 / len(treat_obs)) or 0.001
        z_score = (treat_mean - ctrl_mean) / se
        p_value = 2 * (1 - self._normal_cdf(abs(z_score)))

        # Latency comparison
        ctrl_latency = sum(o.latency for o in ctrl_obs) / len(ctrl_obs)
        treat_latency = sum(o.latency for o in treat_obs) / len(treat_obs)

        # Cost comparison
        ctrl_cost = sum(o.tokens for o in ctrl_obs) / len(ctrl_obs)
        treat_cost = sum(o.tokens for o in treat_obs) / len(treat_obs)

        significant = p_value < 0.05
        winner = self.treatment.name if treat_mean > ctrl_mean and significant else (
            self.control.name if ctrl_mean > treat_mean and significant else "no_winner"
        )

        return {
            "status": "complete",
            "samples": {"control": len(ctrl_obs), "treatment": len(treat_obs)},
            "quality": {
                "control_mean": round(ctrl_mean, 4),
                "treatment_mean": round(treat_mean, 4),
                "improvement": round((treat_mean - ctrl_mean) / ctrl_mean * 100, 2),
            },
            "latency": {"control": round(ctrl_latency, 3), "treatment": round(treat_latency, 3)},
            "cost_tokens": {"control": round(ctrl_cost), "treatment": round(treat_cost)},
            "significance": {
                "z_score": round(z_score, 3),
                "p_value": round(p_value, 4),
                "significant": significant,
            },
            "winner": winner,
            "recommendation": f"Deploy '{winner}'" if winner != "no_winner" else "Continue testing (no significant difference)",
        }

    @staticmethod
    def _normal_cdf(x: float) -> float:
        return 0.5 * (1 + math.erf(x / math.sqrt(2)))


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 7.2: A/B Testing for AI Agents")
    print("  Measure if a new model config is statistically better")
    print("=" * 70)
    print()

    test = ABTest(
        name="credit-scorer-model-switch",
        control=Variant("gpt-4o", "gpt-4o", {"temperature": 0.1}, weight=0.5),
        treatment=Variant("claude-sonnet", "claude-sonnet-4-20250514", {"temperature": 0.0}, weight=0.5),
    )

    # Simulate 200 requests
    print("  🧪 Running A/B test (200 simulated requests)...\n")
    for i in range(200):
        user_id = f"user_{i}"
        variant = test.assign(user_id)

        # Simulate different quality distributions
        if variant.name == "claude-sonnet":
            quality = min(1.0, random.gauss(0.87, 0.08))
            latency = random.gauss(2.5, 0.4)
            tokens = random.randint(800, 1800)
        else:
            quality = min(1.0, random.gauss(0.82, 0.10))
            latency = random.gauss(1.8, 0.3)
            tokens = random.randint(600, 1500)

        test.record(Observation(
            variant=variant.name, success=quality > 0.5,
            latency=max(0.1, latency), tokens=tokens, quality_score=max(0, quality),
        ))

    # Analyze
    results = test.analyze()
    print(f"  📊 RESULTS:")
    print(f"  {'─' * 64}")
    print(f"  Samples:    control={results['samples']['control']}, treatment={results['samples']['treatment']}")
    print(f"  Quality:    control={results['quality']['control_mean']:.3f}, treatment={results['quality']['treatment_mean']:.3f} ({results['quality']['improvement']:+.1f}%)")
    print(f"  Latency:    control={results['latency']['control']:.2f}s, treatment={results['latency']['treatment']:.2f}s")
    print(f"  Tokens:     control={results['cost_tokens']['control']}, treatment={results['cost_tokens']['treatment']}")
    print(f"  Z-score:    {results['significance']['z_score']}")
    print(f"  P-value:    {results['significance']['p_value']} {'✅ significant' if results['significance']['significant'] else '❌ not significant'}")
    print(f"  Winner:     {results['winner']}")
    print(f"  Action:     {results['recommendation']}")
