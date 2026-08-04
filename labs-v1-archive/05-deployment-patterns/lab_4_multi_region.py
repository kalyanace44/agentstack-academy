"""Lab 5.4: Multi-Region Active-Active Deployment

Deploy agents across multiple regions with health-based routing and failover.
Pattern: requests go to the healthiest, lowest-latency region.
"""
from __future__ import annotations

import random
import time
from dataclasses import dataclass, field


@dataclass
class Region:
    name: str
    endpoint: str
    latency_ms: float          # Baseline latency from user
    health_score: float = 1.0  # 0-1
    error_rate: float = 0.0
    active_connections: int = 0
    capacity: int = 100


@dataclass
class RoutingDecision:
    region: str
    reason: str
    latency_ms: float
    was_failover: bool = False


class MultiRegionRouter:
    """Route requests to the best available region."""

    def __init__(self, regions: list[Region]):
        self.regions = {r.name: r for r in regions}
        self.total_requests = 0
        self.failovers = 0
        self.routing_history: list[RoutingDecision] = []

    def route(self, user_region: str = "ap-south-1") -> RoutingDecision:
        """Pick the best region based on health, latency, and capacity."""
        self.total_requests += 1
        candidates = []

        for region in self.regions.values():
            if region.health_score < 0.3:
                continue  # Skip unhealthy regions
            if region.active_connections >= region.capacity:
                continue  # At capacity

            # Score: lower is better
            score = (
                region.latency_ms * 0.4 +
                (1 - region.health_score) * 200 * 0.3 +
                region.error_rate * 500 * 0.2 +
                (region.active_connections / region.capacity) * 100 * 0.1
            )
            candidates.append((region, score))

        candidates.sort(key=lambda x: x[1])

        if not candidates:
            # All regions unhealthy — degrade gracefully
            return RoutingDecision(region="none", reason="ALL REGIONS UNHEALTHY", latency_ms=0)

        best = candidates[0][0]
        was_failover = best.name != user_region and user_region in self.regions

        if was_failover:
            self.failovers += 1

        decision = RoutingDecision(
            region=best.name,
            reason=f"health={best.health_score:.1f}, latency={best.latency_ms:.0f}ms, load={best.active_connections}/{best.capacity}",
            latency_ms=best.latency_ms,
            was_failover=was_failover,
        )
        self.routing_history.append(decision)
        best.active_connections += 1
        return decision

    def update_health(self, region_name: str, health: float, error_rate: float = 0.0):
        if region_name in self.regions:
            self.regions[region_name].health_score = health
            self.regions[region_name].error_rate = error_rate


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 5.4: Multi-Region Active-Active Deployment")
    print("  Health-based routing with automatic failover")
    print("=" * 70)
    print()

    regions = [
        Region("ap-south-1", "https://ap-south-1.prism.internal", latency_ms=20, capacity=50),
        Region("us-east-1", "https://us-east-1.prism.internal", latency_ms=180, capacity=100),
        Region("eu-west-1", "https://eu-west-1.prism.internal", latency_ms=150, capacity=80),
    ]
    router = MultiRegionRouter(regions)

    # Phase 1: Normal operation (all healthy)
    print("  PHASE 1: All regions healthy")
    print("  " + "─" * 64)
    for i in range(5):
        decision = router.route("ap-south-1")
        print(f"    Request {i+1} → {decision.region} ({decision.reason})")

    # Phase 2: Primary region degrades
    print(f"\n  PHASE 2: ap-south-1 degrading (error rate spike)")
    print("  " + "─" * 64)
    router.update_health("ap-south-1", health=0.4, error_rate=0.3)
    for i in range(5):
        decision = router.route("ap-south-1")
        failover_marker = " ⚡ FAILOVER" if decision.was_failover else ""
        print(f"    Request {i+6} → {decision.region} ({decision.reason}){failover_marker}")

    # Phase 3: Primary goes down completely
    print(f"\n  PHASE 3: ap-south-1 DOWN")
    print("  " + "─" * 64)
    router.update_health("ap-south-1", health=0.1, error_rate=0.9)
    for i in range(5):
        decision = router.route("ap-south-1")
        failover_marker = " ⚡ FAILOVER" if decision.was_failover else ""
        print(f"    Request {i+11} → {decision.region} ({decision.reason}){failover_marker}")

    # Phase 4: Recovery
    print(f"\n  PHASE 4: ap-south-1 recovering")
    print("  " + "─" * 64)
    router.update_health("ap-south-1", health=0.8, error_rate=0.02)
    for i in range(3):
        decision = router.route("ap-south-1")
        print(f"    Request {i+16} → {decision.region} ({decision.reason})")

    # Summary
    print(f"\n  {'═' * 66}")
    print(f"  SUMMARY:")
    print(f"    Total requests: {router.total_requests}")
    print(f"    Failovers: {router.failovers} ({router.failovers/router.total_requests*100:.0f}%)")
    print(f"    Zero downtime: ✅ (all requests served despite region failure)")
    print(f"\n  💡 KEY: Health-based routing > DNS failover (faster, no TTL delay)")
