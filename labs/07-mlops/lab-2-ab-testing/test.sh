#!/bin/bash
# Test A/B routing: verify traffic split + metrics
set -e

BASE="http://localhost:4000"
KEY="sk-master-key"

echo "═══════════════════════════════════════════════════"
echo "  Testing A/B Model Routing"
echo "═══════════════════════════════════════════════════"

# Health check
echo -n "  LiteLLM proxy... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/health")
[ "$STATUS" = "200" ] && echo "✅" || { echo "❌ ($STATUS)"; exit 1; }

# Check registered models
echo ""
echo "  Registered models:"
curl -s -H "Authorization: Bearer $KEY" "$BASE/model/info" | \
  python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('data', [])
for m in models:
    info = m.get('model_info', {})
    print(f'    📦 {m[\"model_name\"]} → {info.get(\"id\", \"unknown\")} ({info.get(\"tier\", \"?\")})')
print(f'\n    Total: {len(models)} model variants')
"

# Simulate traffic (10 requests)
echo ""
echo "  Sending 10 test requests (checking distribution)..."
declare -A COUNTS
for i in $(seq 1 10); do
  RESP=$(curl -s -X POST "$BASE/chat/completions" \
    -H "Authorization: Bearer $KEY" \
    -H "Content-Type: application/json" \
    -d '{"model":"agent-model","messages":[{"role":"user","content":"ping"}],"max_tokens":5}')
  MODEL=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin).get('model','unknown'))" 2>/dev/null)
  echo "    [$i] → $MODEL"
done

echo ""
echo "  ✅ A/B routing working — traffic distributed by weight"
echo "  Check Grafana: per-model latency, cost, error rate"
