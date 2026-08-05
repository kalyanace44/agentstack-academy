#!/bin/bash
# Full stack health check
set -e

echo "═══════════════════════════════════════════════════"
echo "  Full Production Stack — Health Check"
echo "═══════════════════════════════════════════════════"

PASS=0 FAIL=0

check() {
  local name=$1 url=$2
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null || echo "000")
  if [ "$STATUS" = "200" ]; then
    echo "  ✅ $name"
    ((PASS++))
  else
    echo "  ❌ $name (HTTP $STATUS)"
    ((FAIL++))
  fi
}

check "LiteLLM Proxy    :4000" "http://localhost:4000/health"
check "Qdrant VectorDB  :6333" "http://localhost:6333/healthz"
check "LangFuse Traces  :3000" "http://localhost:3000"
check "Prometheus       :9090" "http://localhost:9090/-/healthy"
check "Grafana          :3001" "http://localhost:3001/api/health"

# Redis (TCP check)
echo -n "  "
PONG=$(redis-cli -h localhost ping 2>/dev/null || echo "FAIL")
if [ "$PONG" = "PONG" ]; then
  echo "✅ Redis Memory    :6379"
  ((PASS++))
else
  echo "❌ Redis Memory    :6379"
  ((FAIL++))
fi

echo ""
echo "  ─────────────────────────────────"
echo "  Results: $PASS passed, $FAIL failed"
echo ""
if [ $FAIL -eq 0 ]; then
  echo "  🚀 Full stack operational!"
  echo ""
  echo "  Endpoints:"
  echo "    LLM API:    http://localhost:4000"
  echo "    Traces:     http://localhost:3000"
  echo "    Metrics:    http://localhost:9090"
  echo "    Dashboard:  http://localhost:3001 (admin/admin)"
else
  echo "  ⚠️  Some services need attention"
fi
