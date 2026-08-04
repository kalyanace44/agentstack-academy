"""Lab 2.3: Entity Memory — Track Knowledge About Entities Over Time

Build a memory system that extracts, stores, and updates facts about
named entities (people, companies, products) across conversations.
"""
from __future__ import annotations

import re
import time
from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class Fact:
    subject: str
    predicate: str
    value: str
    confidence: float = 1.0
    timestamp: float = field(default_factory=time.time)
    source: str = ""


class EntityMemory:
    """Tracks structured knowledge about entities."""

    def __init__(self):
        self.entities: dict[str, list[Fact]] = defaultdict(list)
        self.total_facts = 0

    def add_fact(self, subject: str, predicate: str, value: str, confidence: float = 1.0, source: str = ""):
        """Add or update a fact about an entity."""
        subject = subject.lower().strip()
        # Update existing fact if same predicate
        for fact in self.entities[subject]:
            if fact.predicate == predicate:
                fact.value = value
                fact.confidence = confidence
                fact.timestamp = time.time()
                fact.source = source
                return
        self.entities[subject].append(Fact(
            subject=subject, predicate=predicate, value=value,
            confidence=confidence, source=source,
        ))
        self.total_facts += 1

    def get_entity(self, name: str) -> list[Fact]:
        return self.entities.get(name.lower().strip(), [])

    def extract_and_store(self, text: str, source: str = "conversation"):
        """Extract entities and facts from text using patterns."""
        # Simple pattern-based extraction (use NER + LLM in production)
        patterns = [
            (r'(\w+)(?:\'s| has a) (?:credit )?(?:score|limit) (?:is |of )?(\d[\d,]+)', "credit_score"),
            (r'(\w+) (?:works at|is at|joined) (\w+)', "employer"),
            (r'(\w+)(?:\'s)? (?:email|mail) (?:is )?(\S+@\S+)', "email"),
            (r'(\w+) (?:prefers?|likes?|wants?) (.+?)(?:\.|$)', "preference"),
            (r'(\w+)(?:\'s)? income (?:is )?(?:₹|Rs\.?)?([\d,]+)', "income"),
        ]
        for pattern, predicate in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                self.add_fact(match.group(1), predicate, match.group(2), source=source)

    def query(self, entity: str, predicate: str = None) -> str:
        """Query what we know about an entity."""
        facts = self.get_entity(entity)
        if not facts:
            return f"No information about '{entity}'"
        if predicate:
            facts = [f for f in facts if predicate.lower() in f.predicate.lower()]
        return "; ".join(f"{f.predicate}: {f.value}" for f in facts)


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 2.3: Entity Memory")
    print("  Extract + track structured facts about entities")
    print("=" * 70)
    print()

    mem = EntityMemory()

    # Simulate conversation extractions
    messages = [
        "Rahul's credit score is 720 and he works at Vegapay",
        "Rahul's income is ₹1,50,000 per month",
        "Rahul prefers quick responses without too much detail",
        "Priya works at Razorpay and her credit limit is 300000",
        "Rahul's credit score is 745",  # UPDATE — should overwrite 720
    ]

    print("  📝 Processing messages...\n")
    for msg in messages:
        mem.extract_and_store(msg)
        print(f"    \"{msg[:70]}\"")

    print(f"\n  📊 Extracted {mem.total_facts} facts about {len(mem.entities)} entities\n")

    # Query
    print(f"  {'─' * 60}")
    for entity in ["rahul", "priya"]:
        facts = mem.get_entity(entity)
        print(f"  Entity: {entity.title()}")
        for f in facts:
            print(f"    • {f.predicate}: {f.value}")
        print()

    # Verify update worked
    rahul_score = [f for f in mem.get_entity("rahul") if f.predicate == "credit_score"]
    assert rahul_score[0].value == "745", "Should have updated to 745"
    print("  ✅ Entity update working (720 → 745 overwritten)")
