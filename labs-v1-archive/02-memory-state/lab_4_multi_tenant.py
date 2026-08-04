"""Lab 2.4: Multi-Tenant Memory — Isolation, TTL, Eviction

Production memory that isolates tenants, expires old memories,
and enforces size limits per tenant. Critical for SaaS agents.
"""
from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class MemEntry:
    key: str
    value: str
    tenant: str
    created: float = field(default_factory=time.time)
    ttl: float = 3600.0  # seconds
    access_count: int = 0

    @property
    def expired(self) -> bool:
        return time.time() - self.created > self.ttl


class TenantMemoryStore:
    """Multi-tenant memory store with isolation, TTL, and LRU eviction."""

    def __init__(self, max_per_tenant: int = 100):
        self.max_per_tenant = max_per_tenant
        self._stores: dict[str, OrderedDict[str, MemEntry]] = {}
        self._lock = Lock()
        self._stats = {"writes": 0, "reads": 0, "evictions": 0, "expired": 0}

    def write(self, tenant: str, key: str, value: str, ttl: float = 3600.0):
        """Write a memory entry for a tenant."""
        with self._lock:
            if tenant not in self._stores:
                self._stores[tenant] = OrderedDict()
            store = self._stores[tenant]
            store[key] = MemEntry(key=key, value=value, tenant=tenant, ttl=ttl)
            store.move_to_end(key)
            self._stats["writes"] += 1
            # Evict if over limit
            while len(store) > self.max_per_tenant:
                store.popitem(last=False)
                self._stats["evictions"] += 1

    def read(self, tenant: str, key: str) -> str | None:
        """Read a memory entry. Returns None if not found or expired."""
        with self._lock:
            store = self._stores.get(tenant)
            if not store or key not in store:
                return None
            entry = store[key]
            if entry.expired:
                del store[key]
                self._stats["expired"] += 1
                return None
            entry.access_count += 1
            store.move_to_end(key)
            self._stats["reads"] += 1
            return entry.value

    def list_keys(self, tenant: str) -> list[str]:
        store = self._stores.get(tenant, {})
        return [k for k, v in store.items() if not v.expired]

    def tenant_size(self, tenant: str) -> int:
        return len(self._stores.get(tenant, {}))

    def delete_tenant(self, tenant: str):
        """Delete all data for a tenant (GDPR right to deletion)."""
        with self._lock:
            self._stores.pop(tenant, None)

    @property
    def stats(self) -> dict:
        return {**self._stats, "tenants": len(self._stores), "total_entries": sum(len(s) for s in self._stores.values())}


# --- Demo ---

if __name__ == "__main__":
    print("=" * 70)
    print("  LAB 2.4: Multi-Tenant Memory")
    print("  Isolation + TTL + LRU eviction for SaaS agents")
    print("=" * 70)
    print()

    store = TenantMemoryStore(max_per_tenant=5)

    # Tenant A: Engineering team
    store.write("eng", "user_preference", "concise technical responses", ttl=86400)
    store.write("eng", "last_deploy", "v2.3.1 on June 15", ttl=3600)
    store.write("eng", "api_key_rotation", "next rotation July 1", ttl=86400)

    # Tenant B: Support team
    store.write("support", "escalation_policy", "wait 24h then escalate to L2", ttl=86400)
    store.write("support", "common_issue_1", "password reset flow is broken since v2.3", ttl=3600)

    # Read (isolated)
    print("  📖 Reading memories (tenant-isolated):")
    print(f"    eng/user_preference: {store.read('eng', 'user_preference')}")
    print(f"    support/escalation_policy: {store.read('support', 'escalation_policy')}")
    print(f"    eng reading support data: {store.read('eng', 'escalation_policy')}")  # None!
    print()

    # Eviction demo
    print("  📦 Eviction demo (max 5 per tenant):")
    for i in range(6):
        store.write("eng", f"item_{i}", f"value_{i}")
    print(f"    eng has {store.tenant_size('eng')} entries (wrote 6 + 3 original, max 5)")
    print(f"    Evictions: {store.stats['evictions']}")
    print()

    # TTL demo
    print("  ⏰ TTL demo:")
    store.write("eng", "ephemeral", "gone in 0.01s", ttl=0.01)
    time.sleep(0.02)
    print(f"    Read expired entry: {store.read('eng', 'ephemeral')}")
    print()

    # GDPR deletion
    print("  🗑️  GDPR tenant deletion:")
    print(f"    Before: {store.tenant_size('support')} entries for 'support'")
    store.delete_tenant("support")
    print(f"    After: {store.tenant_size('support')} entries for 'support'")
    print()

    print(f"  📊 Stats: {store.stats}")
    print("  ✅ Multi-tenant memory with full isolation working")
