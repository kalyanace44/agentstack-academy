"""Lab 7.3: Canary Deployments — Gradual Rollout with Auto-Rollback

Roll out new model versions gradually (5% → 25% → 50% → 100%).
Auto-rollback if quality drops below threshold.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field


@dataclass
class CanaryConfig:
    stages: list[float] = field(default_factory=lambda: [0.05, 0.25, 0.50, 1.0])
    min_samples_per_stage: int = 20
    quality_threshold: float = 0.75
    error_rate_threshold: float = 0.10
    promotion_delay_s: float = 0.0  # Time between stages (0 for demo)


@dataclass
class CanaryState:
    current_stage: int = 0
    canary_traffic: float = 0.05
    samples_this_stage: int = 0
    quality_scores: list[float] = field(default_factory=list)
    errors: int = 0
    status: str = "running"  # running, promoted, rolled_back


class CanaryDeployment:
    """Manage canary rollout of a new model version."""

    def __init__(self, baseline: str, canary: str, config: CanaryConfig = None):
        self.baseline = baseline
        self.canary = canary
        self.config = config or CanaryConfig()
        self.state = CanaryState(canary_traffic=self.config.stages[0])
        self.decisions: list[str] = []

    def route_request(self) -> str:
        """Route a request to baseline or canary."""
        if random.random() < self.state.canary_traffic:
            return self.canary
        return self.baseline

    def record_result(self, model: str, quality: float, error: bool = False):
        """Record a result and check promotion/rollback criteria."""
        if model != self.canary:
            return  # Only track canary metrics

        self.state.samples_this_stage += 1
        self.state.quality_scores.append(quality)
        if error:
            self.state.errors += 1

        # Check rollback
        if self.state.samples_this_stage >= 5:
            recent_quality = sum(self.state.quality_scores[-10:]) / len(self.state.quality_scores[-10:])
            error_rate = self.state.errors / self.state.samples_this_stage

            if recent_quality < self.config.quality_threshold:
                self._rollback(f"Quality dropped to {recent_quality:.3f} (threshold: {self.config.quality_threshold})")
                return

            if error_rate > self.config.error_rate_threshold:
                self._rollback(f"Error rate {error_rate:.1%} exceeds threshold {self.config.error_rate_threshold:.1%}")
                return

        # Check promotion
        if self.state.samples_this_stage >= self.config.min_samples_per_stage:
            self._promote_stage()

    def _promote_stage(self):
        if self.state.current_stage >= len(self.config.stages) - 1:
            self.state.status = "promoted"
            self.state.canary_traffic = 1.0
            self.decisions.append(f"✅ PROMOTED to 100% — canary passed all stages")
            return

        self.state.current_stage += 1
        self.state.canary_traffic = self.config.stages[self.state.current_stage]
        self.state.samples_this_stage = 0
        avg_quality = sum(self.state.quality_scores) / len(self.state.quality_scores)
        self.decisions.append(
            f"⬆️  Stage {self.state.current_stage}: traffic → {self.state.canary_traffic:.0%} "
            f"(quality: {avg_quality:.3f}, samples: {len(self.state.quality_scores)})"
        )

    def _rollback(self, reason: str):
        self.state.status = "rolled_back"
        self.state.canary_traffic = 0.0
        self.decisions.append(f"🔴 ROLLBACK: {reason}")


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 7.3: Canary Deployments")
    print("  Gradual rollout with auto-rollback on quality drop")
    print("=" * 70)
    print()

    # Scenario 1: Successful canary
    print("  SCENARIO 1: Successful canary (new model is better)")
    print("  " + "─" * 60)
    canary1 = CanaryDeployment(
        baseline="gpt-4o-v1", canary="gpt-4o-v2",
        config=CanaryConfig(stages=[0.05, 0.25, 0.50, 1.0], min_samples_per_stage=10),
    )

    for i in range(60):
        model = canary1.route_request()
        quality = random.gauss(0.88, 0.05) if model == "gpt-4o-v2" else random.gauss(0.82, 0.08)
        canary1.record_result(model, min(1.0, max(0, quality)))
        if canary1.state.status != "running":
            break

    for d in canary1.decisions:
        print(f"    {d}")
    print(f"    Final: {canary1.state.status.upper()}")

    # Scenario 2: Failed canary (auto-rollback)
    print(f"\n  SCENARIO 2: Bad canary (quality regression → rollback)")
    print("  " + "─" * 60)
    canary2 = CanaryDeployment(
        baseline="gpt-4o", canary="gpt-4o-mini-fine-tuned",
        config=CanaryConfig(stages=[0.05, 0.25, 0.50, 1.0], min_samples_per_stage=10, quality_threshold=0.75),
    )

    for i in range(60):
        model = canary2.route_request()
        # Bad model: quality degrades over time
        quality = random.gauss(0.70, 0.15) if model == "gpt-4o-mini-fine-tuned" else random.gauss(0.85, 0.05)
        canary2.record_result(model, min(1.0, max(0, quality)))
        if canary2.state.status != "running":
            break

    for d in canary2.decisions:
        print(f"    {d}")
    print(f"    Final: {canary2.state.status.upper()}")
    print(f"    Requests affected: {len(canary2.state.quality_scores)} (limited blast radius)")

    print(f"\n  ✅ Canary deployment protects production from bad model releases")
