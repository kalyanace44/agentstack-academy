"""Lab 7.1: Model Registry — Version, Tag, and Promote Models

Manage model versions through stages: development → staging → production.
Track metadata, performance metrics, and lineage.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class Stage(Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


@dataclass
class ModelVersion:
    name: str
    version: str
    provider: str         # openai, anthropic, self-hosted
    model_id: str         # gpt-4o, claude-sonnet-4-20250514, etc.
    stage: Stage = Stage.DEVELOPMENT
    metrics: dict = field(default_factory=dict)
    config: dict = field(default_factory=dict)  # temperature, max_tokens, system prompt
    created_at: float = field(default_factory=time.time)
    promoted_at: float = 0.0
    promoted_by: str = ""


class ModelRegistry:
    """Track and manage model versions across environments."""

    def __init__(self):
        self.models: dict[str, list[ModelVersion]] = {}
        self.active_production: dict[str, ModelVersion] = {}
        self.history: list[dict] = []

    def register(self, name: str, version: str, provider: str, model_id: str, config: dict = None) -> ModelVersion:
        """Register a new model version."""
        mv = ModelVersion(name=name, version=version, provider=provider, model_id=model_id, config=config or {})
        self.models.setdefault(name, []).append(mv)
        self.history.append({"action": "register", "name": name, "version": version, "time": time.time()})
        return mv

    def promote(self, name: str, version: str, to_stage: Stage, by: str = "system") -> bool:
        """Promote a model version to a new stage."""
        versions = self.models.get(name, [])
        mv = next((v for v in versions if v.version == version), None)
        if not mv:
            return False

        # Validation gates
        if to_stage == Stage.STAGING and not mv.metrics:
            print(f"    ⚠️  Cannot promote to staging without metrics")
            return False
        if to_stage == Stage.PRODUCTION and mv.stage != Stage.STAGING:
            print(f"    ⚠️  Must pass through staging first")
            return False

        old_stage = mv.stage
        mv.stage = to_stage
        mv.promoted_at = time.time()
        mv.promoted_by = by

        if to_stage == Stage.PRODUCTION:
            # Archive previous production version
            if name in self.active_production:
                self.active_production[name].stage = Stage.ARCHIVED
            self.active_production[name] = mv

        self.history.append({
            "action": "promote", "name": name, "version": version,
            "from": old_stage.value, "to": to_stage.value, "by": by,
        })
        return True

    def set_metrics(self, name: str, version: str, metrics: dict):
        versions = self.models.get(name, [])
        mv = next((v for v in versions if v.version == version), None)
        if mv:
            mv.metrics = metrics

    def get_production(self, name: str) -> ModelVersion | None:
        return self.active_production.get(name)

    def list_versions(self, name: str) -> list[ModelVersion]:
        return self.models.get(name, [])


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 7.1: Model Registry")
    print("  Version, tag, and promote models through stages")
    print("=" * 70)
    print()

    registry = ModelRegistry()

    # Register versions
    print("  📦 Registering model versions...")
    registry.register("credit-scorer", "v1.0", "openai", "gpt-4o",
                     config={"temperature": 0.1, "system_prompt": "You are a credit risk analyst..."})
    registry.register("credit-scorer", "v1.1", "openai", "gpt-4o-mini",
                     config={"temperature": 0.1, "system_prompt": "You are a credit risk analyst..."})
    registry.register("credit-scorer", "v2.0", "anthropic", "claude-sonnet-4-20250514",
                     config={"temperature": 0.0, "system_prompt": "Analyze credit risk..."})
    print(f"    Registered 3 versions of 'credit-scorer'")

    # Add metrics from eval
    print("\n  📊 Adding evaluation metrics...")
    registry.set_metrics("credit-scorer", "v1.0", {"accuracy": 0.82, "latency_p95": 2.1, "cost_per_req": 0.003})
    registry.set_metrics("credit-scorer", "v1.1", {"accuracy": 0.79, "latency_p95": 0.8, "cost_per_req": 0.0004})
    registry.set_metrics("credit-scorer", "v2.0", {"accuracy": 0.88, "latency_p95": 2.5, "cost_per_req": 0.005})

    # Promote through stages
    print("\n  🚀 Promotion workflow:")
    print("    v1.0: dev → staging → production")
    registry.promote("credit-scorer", "v1.0", Stage.STAGING, by="ml-engineer")
    registry.promote("credit-scorer", "v1.0", Stage.PRODUCTION, by="ml-lead")
    print(f"    ✅ v1.0 is now in production")

    print("\n    v2.0: dev → staging (better accuracy)")
    registry.promote("credit-scorer", "v2.0", Stage.STAGING, by="ml-engineer")
    print(f"    ✅ v2.0 in staging for canary testing")

    print("\n    v2.0: staging → production (replaces v1.0)")
    registry.promote("credit-scorer", "v2.0", Stage.PRODUCTION, by="ml-lead")
    print(f"    ✅ v2.0 promoted, v1.0 archived")

    # Show current state
    print(f"\n  {'─' * 66}")
    print("  REGISTRY STATE:")
    for mv in registry.list_versions("credit-scorer"):
        print(f"    {mv.version:<6} | {mv.stage.value:<12} | {mv.model_id:<25} | acc={mv.metrics.get('accuracy', '?')}")

    prod = registry.get_production("credit-scorer")
    print(f"\n  🟢 Active production: {prod.name} {prod.version} ({prod.model_id})")
    print(f"     Accuracy: {prod.metrics['accuracy']}, Latency p95: {prod.metrics['latency_p95']}s")
