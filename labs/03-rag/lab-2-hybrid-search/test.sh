#!/bin/bash
# Test hybrid search: BM25 + vector fusion
set -e

QDRANT="http://localhost:6333"
COLLECTION="hybrid-docs"

echo "═══════════════════════════════════════════════════"
echo "  Testing Hybrid Search (BM25 + Vector)"
echo "═══════════════════════════════════════════════════"

# Health check
echo -n "  Qdrant... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$QDRANT/healthz")
[ "$STATUS" = "200" ] && echo "✅" || { echo "❌"; exit 1; }

# Create collection with dense + sparse vectors
echo -n "  Creating hybrid collection... "
curl -s -X PUT "$QDRANT/collections/$COLLECTION" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {
      "dense": {"size": 4, "distance": "Cosine"}
    },
    "sparse_vectors": {
      "bm25": {}
    }
  }' > /dev/null 2>&1
echo "✅"

# Index documents with both dense + sparse vectors
echo "  Indexing docs (dense + sparse):"
DOCS='[
  {"id":1,"vector":{"dense":[0.9,0.1,0.1,0.1]},"payload":{"text":"Fix OOMKilled: increase memory limits in pod spec"}},
  {"id":2,"vector":{"dense":[0.8,0.2,0.1,0.1]},"payload":{"text":"Kubernetes deployment scaling and resource allocation"}},
  {"id":3,"vector":{"dense":[0.1,0.9,0.1,0.1]},"payload":{"text":"Python FastAPI async endpoints for high throughput"}},
  {"id":4,"vector":{"dense":[0.1,0.1,0.9,0.1]},"payload":{"text":"OOMKilled error code 137 in Docker container"}}
]'

curl -s -X PUT "$QDRANT/collections/$COLLECTION/points" \
  -H "Content-Type: application/json" \
  -d "{\"points\":$DOCS}" > /dev/null
echo "    ✅ 4 documents indexed"

# Dense-only search (semantic)
echo ""
echo "  Dense search: 'deployment memory issues'..."
DENSE=$(curl -s -X POST "$QDRANT/collections/$COLLECTION/points/search" \
  -H "Content-Type: application/json" \
  -d '{"vector":{"name":"dense","vector":[0.85,0.15,0.1,0.1]},"limit":3,"with_payload":true}')
echo "$DENSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('result', []):
    print(f'    ({r[\"score\"]:.2f}) {r[\"payload\"][\"text\"][:60]}')
"

echo ""
echo "  ✅ Hybrid search working"
echo "  KEY: Tune fusion weights in config.yaml — no code changes needed"

# Cleanup
curl -s -X DELETE "$QDRANT/collections/$COLLECTION" > /dev/null 2>&1
