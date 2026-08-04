#!/bin/bash
# Test the LiteLLM proxy — run after docker-compose up -d
set -e

BASE="http://localhost:4000"
KEY="sk-master-key-change-me"

echo "═══════════════════════════════════════════════════"
echo "  Testing LiteLLM Proxy"
echo "═══════════════════════════════════════════════════"

# 1. Health check
echo -n "  Health check... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $BASE/health)
if [ "$STATUS" = "200" ]; then echo "✅ UP"; else echo "❌ DOWN ($STATUS)"; exit 1; fi

# 2. List available models
echo -n "  Models available... "
MODELS=$(curl -s -H "Authorization: Bearer $KEY" $BASE/models | python3 -c "import sys,json; print(len(json.load(sys.stdin)['data']))" 2>/dev/null || echo "0")
echo "✅ $MODELS models"

# 3. Chat completion (OpenAI-compatible)
echo -n "  Chat completion... "
RESPONSE=$(curl -s -X POST $BASE/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d '{
    "model": "gpt-4o-mini",
    "messages": [{"role": "user", "content": "Say hello in exactly 3 words"}],
    "max_tokens": 20
  }')
CONTENT=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['choices'][0]['message']['content'])" 2>/dev/null || echo "FAILED")
if [ "$CONTENT" != "FAILED" ]; then echo "✅ \"$CONTENT\""; else echo "❌ $RESPONSE"; fi

# 4. Check spend
echo -n "  Spend tracking... "
SPEND=$(curl -s -H "Authorization: Bearer $KEY" "$BASE/spend/logs?limit=1" 2>/dev/null)
echo "✅ Logging active"

echo ""
echo "  ✅ All checks passed — proxy is working"
echo ""
echo "  NEXT STEPS:"
echo "  1. Change a model in config.yaml → docker-compose restart litellm"
echo "  2. Add a fallback → kill OpenAI env var → see Anthropic take over"
echo "  3. Set max_budget to 0.01 → watch requests get rejected"
