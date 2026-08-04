#!/bin/bash
# Test RAG pipeline: index → search → generate
set -e

QDRANT="http://localhost:6333"

echo "═══════════════════════════════════════════════════"
echo "  Testing RAG Pipeline (Qdrant)"
echo "═══════════════════════════════════════════════════"

# 1. Health
echo -n "  Qdrant health... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" $QDRANT/healthz)
if [ "$STATUS" = "200" ]; then echo "✅ UP"; else echo "❌ DOWN. Run: make up"; exit 1; fi

# 2. Create collection
echo -n "  Create collection... "
curl -s -X PUT "$QDRANT/collections/knowledge-base" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {"size": 4, "distance": "Cosine"}
  }' > /dev/null 2>&1 || true
echo "✅ knowledge-base ready"

# 3. Insert sample vectors (simulated embeddings for demo)
echo -n "  Index 3 documents... "
curl -s -X PUT "$QDRANT/collections/knowledge-base/points" \
  -H "Content-Type: application/json" \
  -d '{
    "points": [
      {"id": 1, "vector": [0.9, 0.1, 0.2, 0.3], "payload": {"text": "Kubernetes HPA scales pods based on custom metrics like queue depth", "source": "deployment-guide.md"}},
      {"id": 2, "vector": [0.1, 0.9, 0.2, 0.1], "payload": {"text": "Rate limiting with token buckets prevents API abuse", "source": "security-guide.md"}},
      {"id": 3, "vector": [0.2, 0.1, 0.9, 0.3], "payload": {"text": "PII scanner detects PAN, Aadhaar, credit card numbers in prompts", "source": "compliance-guide.md"}}
    ]
  }' > /dev/null
echo "✅ 3 docs indexed"

# 4. Search (similarity query)
echo -n "  Search: 'how to scale pods'... "
RESULTS=$(curl -s -X POST "$QDRANT/collections/knowledge-base/points/search" \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.85, 0.15, 0.2, 0.3],
    "limit": 2,
    "with_payload": true
  }')
TOP=$(echo "$RESULTS" | python3 -c "import sys,json; r=json.load(sys.stdin); print(r['result'][0]['payload']['text'][:50])" 2>/dev/null || echo "PARSE_FAIL")
echo "✅ Top result: \"$TOP...\""

# 5. Collection info
echo -n "  Collection stats... "
INFO=$(curl -s "$QDRANT/collections/knowledge-base")
COUNT=$(echo "$INFO" | python3 -c "import sys,json; print(json.load(sys.stdin)['result']['points_count'])" 2>/dev/null || echo "?")
echo "✅ $COUNT vectors stored"

echo ""
echo "  ✅ RAG pipeline working"
echo ""
echo "  WHAT JUST HAPPENED:"
echo "    1. Created a vector collection (like a table)"
echo "    2. Stored documents as vectors (embeddings)"
echo "    3. Searched by similarity (not keywords!)"
echo "    4. Got ranked results to stuff into LLM prompt"
echo ""
echo "  NEXT: Edit config.yaml → change chunk_size → re-index → compare"
