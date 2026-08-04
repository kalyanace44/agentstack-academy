#!/bin/bash
# End-to-end health check for the full stack
set -e

echo "═══════════════════════════════════════════════════"
echo "  Full Stack Health Check"
echo "═══════════════════════════════════════════════════"

check() {
  local name=$1 url=$2
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
  if [ "$STATUS" = "200" ]; then
    echo "  ✅ $name ($url)"
  else
    echo "  ❌ $name ($url) — HTTP $STATUS"
    return 1
  fi
}

PASS=0 FAIL=0

check "LiteLLM Proxy" "http://localhost:4000/health" && ((PASS++)) || ((FAIL++))
check "Qdrant VectorDB" "http://localhost:6333/healthz" && ((PASS++)) || ((FAIL++))
check "LangFuse Traces" "http://localhost:3000" && ((PASS++)) || ((FAIL++))
check "Agent App" "http://localhost:8080/health" && ((PASS++)) || ((FAIL++))

# Redis (different check)
echo -n "  "
PONG=$(redis-cli -h localhost ping 2>/dev/null || echo "FAIL")
if [ "$PONG" = "PONG" ]; then
  echo "✅ Redis Memory (localhost:6379)"
  ((PASS++))
else
  echo "❌ Redis Memory — not responding"
  ((FAIL++))
fi

echo ""
echo "  Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && echo "  🚀 Full stack is operational!" || echo "  ⚠️  Some services need attention"
