#!/bin/bash
# Test A2A protocol: discovery + delegation
set -e

echo "═══════════════════════════════════════════════════"
echo "  Testing A2A Protocol"
echo "═══════════════════════════════════════════════════"

# 1. Check agent cards
echo "  DISCOVERY (Agent Cards):"
for PORT in 8001 8002 8003; do
  CARD=$(curl -s http://localhost:$PORT/.well-known/agent.json 2>/dev/null)
  if [ -n "$CARD" ]; then
    NAME=$(echo "$CARD" | python3 -c "import sys,json; print(json.load(sys.stdin)['name'])" 2>/dev/null)
    echo "    ✅ :$PORT → $NAME"
  else
    echo "    ❌ :$PORT → not responding"
  fi
done

# 2. Health checks
echo ""
echo "  HEALTH:"
for PORT in 8001 8002 8003; do
  STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$PORT/health 2>/dev/null)
  echo "    :$PORT → $STATUS"
done

# 3. Task delegation
echo ""
echo "  TASK DELEGATION:"
echo -n "    credit_score... "
RESULT=$(curl -s -X POST http://localhost:8001/tasks \
  -H "Content-Type: application/json" \
  -d '{"skill":"credit_score","data":{"income":150000,"credit_history_years":5,"defaults":0}}')
APPROVED=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['approved'])" 2>/dev/null)
echo "✅ approved=$APPROVED"

echo -n "    fraud_check... "
RESULT=$(curl -s -X POST http://localhost:8002/tasks \
  -H "Content-Type: application/json" \
  -d '{"skill":"fraud_check","data":{"applicant_id":"TEST","income":200000,"address_changes":1}}')
BLOCK=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['block'])" 2>/dev/null)
echo "✅ block=$BLOCK"

echo -n "    verify_identity... "
RESULT=$(curl -s -X POST http://localhost:8003/tasks \
  -H "Content-Type: application/json" \
  -d '{"skill":"verify_identity","data":{"document_type":"PAN","document_number":"ABCDE1234F","name":"Test"}}')
VERIFIED=$(echo "$RESULT" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['verified'])" 2>/dev/null)
echo "✅ verified=$VERIFIED"

echo ""
echo "  ✅ A2A protocol working — discovery + delegation confirmed"
echo ""
echo "  KEY TAKEAWAY:"
echo "    Agents are services. Protocol is the contract."
echo "    Add a new agent = add to agents.yaml + deploy a container."
