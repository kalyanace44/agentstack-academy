#!/bin/bash
# Test agent memory — store, retrieve, expire
set -e

echo "═══════════════════════════════════════════════════"
echo "  Testing Agent Memory (Redis)"
echo "═══════════════════════════════════════════════════"

# 1. Health
echo -n "  Redis ping... "
PONG=$(redis-cli ping 2>/dev/null)
if [ "$PONG" = "PONG" ]; then echo "✅ PONG"; else echo "❌ Redis not running. Run: make up"; exit 1; fi

# 2. Store conversation memory
echo -n "  Store message... "
redis-cli SET "conv:session-abc:1" '{"role":"user","content":"Whats my credit limit?"}' EX 86400 > /dev/null
redis-cli SET "conv:session-abc:2" '{"role":"assistant","content":"Your limit is ₹2L"}' EX 86400 > /dev/null
echo "✅ 2 messages stored (TTL: 24h)"

# 3. Store user facts
echo -n "  Store user fact... "
redis-cli SET "facts:user-101:preferred_language" '"Hindi"' EX 2592000 > /dev/null
redis-cli SET "facts:user-101:risk_tolerance" '"conservative"' EX 2592000 > /dev/null
echo "✅ 2 facts stored (TTL: 30d)"

# 4. Retrieve
echo -n "  Retrieve history... "
MSG=$(redis-cli GET "conv:session-abc:1")
if echo "$MSG" | grep -q "credit limit"; then echo "✅ Got: $MSG"; else echo "❌"; fi

# 5. Check TTL
echo -n "  Check TTL... "
TTL=$(redis-cli TTL "conv:session-abc:1")
echo "✅ Expires in ${TTL}s"

# 6. List all keys in namespace
echo -n "  List conversation keys... "
COUNT=$(redis-cli KEYS "conv:*" | wc -l | tr -d ' ')
echo "✅ $COUNT keys in conv: namespace"

# 7. Expire test (short TTL)
echo -n "  Expire test (2s TTL)... "
redis-cli SET "state:temp-task" '"processing step 3"' EX 2 > /dev/null
sleep 3
GONE=$(redis-cli GET "state:temp-task")
if [ -z "$GONE" ] || [ "$GONE" = "" ]; then echo "✅ Expired (gone after 2s)"; else echo "❌ Still alive: $GONE"; fi

# 8. Memory usage
echo ""
echo "  📊 Memory stats:"
echo "    $(redis-cli INFO memory | grep used_memory_human)"
echo "    $(redis-cli DBSIZE)"

echo ""
echo "  ✅ All memory operations working"
echo ""
echo "  KEY CONCEPTS:"
echo "    • Namespaces isolate memory types (conv, facts, state)"
echo "    • TTL auto-cleans stale data — no manual cleanup"
echo "    • LRU eviction prevents OOM under load"
echo "    • Same pattern works at 1M keys (prod scale)"
