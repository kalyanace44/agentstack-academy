"""Lab 9.3: Self-Healing Data Pipeline Agent (1M events/day)

An ETL pipeline agent that:
- Monitors pipeline health in real-time
- Detects failures (schema drift, source outages, data quality)
- Auto-remediates common issues without human intervention
- Escalates novel failures to on-call engineers
"""
from __future__ import annotations

import random
import time
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum


class FailureType(Enum):
    SCHEMA_DRIFT = "schema_drift"
    SOURCE_TIMEOUT = "source_timeout"
    DATA_QUALITY = "data_quality"
    VOLUME_ANOMALY = "volume_anomaly"
    TRANSFORM_ERROR = "transform_error"
    SINK_FAILURE = "sink_failure"


class RemediationAction(Enum):
    RETRY = "retry"
    SKIP_RECORD = "skip_record"
    USE_DEFAULT = "use_default"
    SWITCH_SOURCE = "switch_source"
    ALERT_HUMAN = "alert_human"
    ADAPT_SCHEMA = "adapt_schema"
    BACKFILL = "backfill"


@dataclass
class PipelineEvent:
    source: str
    record_count: int
    timestamp: float = field(default_factory=time.time)
    failure: FailureType | None = None
    error_msg: str = ""


@dataclass
class Remediation:
    failure: FailureType
    action: RemediationAction
    success: bool
    duration_ms: float
    records_affected: int
    details: str = ""


class SelfHealingPipeline:
    """Pipeline agent with automatic failure detection and remediation."""

    def __init__(self):
        self.events_processed = 0
        self.failures_detected = 0
        self.auto_remediated = 0
        self.escalated = 0
        self.remediations: list[Remediation] = []
        self.health_history: list[float] = []

        # Remediation playbook
        self.playbook: dict[FailureType, list[RemediationAction]] = {
            FailureType.SOURCE_TIMEOUT: [RemediationAction.RETRY, RemediationAction.SWITCH_SOURCE, RemediationAction.ALERT_HUMAN],
            FailureType.SCHEMA_DRIFT: [RemediationAction.ADAPT_SCHEMA, RemediationAction.USE_DEFAULT, RemediationAction.ALERT_HUMAN],
            FailureType.DATA_QUALITY: [RemediationAction.SKIP_RECORD, RemediationAction.USE_DEFAULT, RemediationAction.ALERT_HUMAN],
            FailureType.VOLUME_ANOMALY: [RemediationAction.ALERT_HUMAN],
            FailureType.TRANSFORM_ERROR: [RemediationAction.RETRY, RemediationAction.SKIP_RECORD, RemediationAction.ALERT_HUMAN],
            FailureType.SINK_FAILURE: [RemediationAction.RETRY, RemediationAction.BACKFILL, RemediationAction.ALERT_HUMAN],
        }

    def process_batch(self, events: list[PipelineEvent]) -> dict:
        """Process a batch of events, auto-healing failures."""
        results = {"processed": 0, "failed": 0, "healed": 0, "escalated": 0}

        for event in events:
            self.events_processed += event.record_count

            if event.failure:
                self.failures_detected += 1
                results["failed"] += 1
                remediation = self._attempt_remediation(event)
                if remediation.success:
                    self.auto_remediated += 1
                    results["healed"] += 1
                else:
                    self.escalated += 1
                    results["escalated"] += 1
            else:
                results["processed"] += 1

        # Calculate health score
        total = results["processed"] + results["failed"]
        health = results["processed"] / max(total, 1)
        self.health_history.append(health)
        return results

    def _attempt_remediation(self, event: PipelineEvent) -> Remediation:
        """Try remediation actions from playbook until one succeeds."""
        actions = self.playbook.get(event.failure, [RemediationAction.ALERT_HUMAN])

        for action in actions:
            start = time.perf_counter()
            success = self._execute_action(action, event)
            duration = (time.perf_counter() - start) * 1000

            remediation = Remediation(
                failure=event.failure, action=action, success=success,
                duration_ms=round(duration, 1), records_affected=event.record_count,
                details=f"Source: {event.source}, Error: {event.error_msg[:50]}",
            )
            self.remediations.append(remediation)

            if success:
                return remediation

        # All actions failed
        return Remediation(
            failure=event.failure, action=RemediationAction.ALERT_HUMAN,
            success=False, duration_ms=0, records_affected=event.record_count,
        )

    def _execute_action(self, action: RemediationAction, event: PipelineEvent) -> bool:
        """Execute a remediation action. Returns success/failure."""
        time.sleep(0.001)  # Simulate action time

        # Simulate success rates per action type
        success_rates = {
            RemediationAction.RETRY: 0.7,
            RemediationAction.SKIP_RECORD: 0.95,
            RemediationAction.USE_DEFAULT: 0.9,
            RemediationAction.SWITCH_SOURCE: 0.6,
            RemediationAction.ADAPT_SCHEMA: 0.8,
            RemediationAction.BACKFILL: 0.85,
            RemediationAction.ALERT_HUMAN: 0.0,  # Always "fails" to try next
        }
        return random.random() < success_rates.get(action, 0.5)

    @property
    def stats(self) -> dict:
        return {
            "events_processed": self.events_processed,
            "failures_detected": self.failures_detected,
            "auto_remediated": self.auto_remediated,
            "escalated": self.escalated,
            "heal_rate": round(self.auto_remediated / max(self.failures_detected, 1), 3),
            "avg_health": round(sum(self.health_history) / max(len(self.health_history), 1), 3),
        }


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 9.3: Self-Healing Data Pipeline (1M events/day)")
    print("  Auto-detect and remediate failures without human intervention")
    print("=" * 70)
    print()

    pipeline = SelfHealingPipeline()

    # Simulate 24 hours of pipeline operation
    print("  ⚙️  Simulating 24 hours of pipeline operation...\n")
    sources = ["payments_api", "transactions_db", "user_events", "fraud_stream"]

    for hour in range(24):
        batch = []
        for _ in range(random.randint(8, 15)):
            source = random.choice(sources)
            records = random.randint(100, 5000)

            # 15% failure rate
            if random.random() < 0.15:
                failure = random.choice(list(FailureType))
                batch.append(PipelineEvent(
                    source=source, record_count=records,
                    failure=failure, error_msg=f"Simulated {failure.value} from {source}",
                ))
            else:
                batch.append(PipelineEvent(source=source, record_count=records))

        pipeline.process_batch(batch)

    # Results
    stats = pipeline.stats
    print(f"  📊 24-HOUR SUMMARY:")
    print(f"  {'─' * 60}")
    print(f"    Events processed:    {stats['events_processed']:,}")
    print(f"    Failures detected:   {stats['failures_detected']}")
    print(f"    Auto-remediated:     {stats['auto_remediated']} ({stats['heal_rate']:.0%})")
    print(f"    Escalated to human:  {stats['escalated']}")
    print(f"    Avg pipeline health: {stats['avg_health']:.1%}")
    print()

    # Remediation breakdown
    print("  🔧 REMEDIATION BREAKDOWN:")
    action_counts = defaultdict(int)
    action_success = defaultdict(int)
    for r in pipeline.remediations:
        action_counts[r.action.value] += 1
        if r.success:
            action_success[r.action.value] += 1

    for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
        successes = action_success[action]
        rate = successes / count if count > 0 else 0
        print(f"    {action:<18}: {count:>3} attempts, {successes:>3} successes ({rate:.0%})")

    print(f"\n  {'─' * 60}")
    print("  💡 KEY PATTERNS:")
    print("    • Playbook-driven: ordered list of actions per failure type")
    print("    • Escalation ladder: retry → skip → default → human")
    print("    • Volume anomaly always escalates (could be data loss)")
    print("    • Track heal rate per source to identify chronic issues")
    print("    • Auto-remediation saves ~3 hours of on-call engineer time/day")
