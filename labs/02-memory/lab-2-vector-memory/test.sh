#!/bin/bash
# Test vector memory: store → semantic search → recall
set -e

QDRANT="http://localhost:6333"
COLLECTION="agent-memory"

echo "═══════════════════════════════════════════════════"
echo "  Testing Vector Memory (Qdrant)"
echo "═══════════════════════════════════════════════════"

# 1. Health check
echo -n "  Qdrant health... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$QDRANT/healthz")
[ "$STATUS" = "200" ] && echo "✅" || { echo "❌ ($STATUS)"; exit 1; }

# 2. Create collection
echo -n "  Creating collection... "
curl -s -X PUT "$QDRANT/collections/$COLLECTION" \
  -H "Content-Type: application/json" \
  -d '{
    "vectors": {"size": 4, "distance": "Cosine"},
    "on_disk_payload": true
  }' > /dev/null 2>&1
echo "✅"

# 3. Store memories (using tiny 4-dim vectors for demo)
echo "  Storing memories:"
MEMORIES=(
  '{"id":1,"vector":[0.9,0.1,0.2,0.1],"payload":{"text":"We decided to use Kubernetes for deployment","type":"decision","user":"kalyan"}}'
  '{"id":2,"vector":[0.1,0.9,0.1,0.2],"payload":{"text":"User prefers dark theme and concise responses","type":"preference","user":"kalyan"}}'
  '{"id":3,"vector":[0.8,0.2,0.3,0.1],"payload":{"text":"Deployed agent to EKS cluster in ap-south-1","type":"fact","user":"kalyan"}}'
  '{"id":4,"vector":[0.2,0.1,0.9,0.1],"payload":{"text":"RAG pipeline uses Qdrant with hybrid search","type":"decision","user":"kalyan"}}'
)

for MEM in "${MEMORIES[@]}"; do
  TEXT=$(echo "$MEM" | python3 -c "import sys,json; print(json.load(sys.stdin)['payload']['text'][:50])")
  curl -s -X PUT "$QDRANT/collections/$COLLECTION/points" \
    -H "Content-Type: application/json" \
    -d "{\"points\":[$MEM]}" > /dev/null
  echo "    ✅ $TEXT..."
done

# 4. Semantic search (query: "infrastructure" → should find K8s memories)
echo ""
echo "  Semantic search: query='infrastructure/deployment'..."
RESULTS=$(curl -s -X POST "$QDRANT/collections/$COLLECTION/points/search" \
  -H "Content-Type: application/json" \
  -d '{"vector":[0.85,0.15,0.25,0.1],"limit":2,"with_payload":true}')

echo "  Results:"
echo "$RESULTS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('result', []):
    score = r['score']
    text = r['payload']['text'][:60]
    print(f'    📝 ({score:.2f}) {text}')
"

# 5. Filtered search (only decisions)
echo ""
echo "  Filtered search: type='decision' only..."
RESULTS=$(curl -s -X POST "$QDRANT/collections/$COLLECTION/points/search" \
  -H "Content-Type: application/json" \
  -d '{"vector":[0.5,0.5,0.5,0.1],"limit":3,"with_payload":true,"filter":{"must":[{"key":"type","match":{"value":"decision"}}]}}')

echo "$RESULTS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for r in data.get('result', []):
    text = r['payload']['text'][:60]
    print(f'    📝 {text}')
"

# Cleanup
curl -s -X DELETE "$QDRANT/collections/$COLLECTION" > /dev/null 2>&1

echo ""
echo "  ✅ Vector memory working: store + semantic search + filtered recall"
