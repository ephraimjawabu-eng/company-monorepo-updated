#!/usr/bin/env bash
set -euo pipefail

# CI smoke script: ensures the worker can process an enqueued run against the local FastAPI server
# Assumes Redis is available at REDIS_URL and backend running at BACKEND_URL
REDIS_URL=${REDIS_URL:-redis://localhost:6379}
BACKEND_URL=${BACKEND_URL:-http://localhost:8000}

echo "Starting CI smoke test against $BACKEND_URL with Redis $REDIS_URL"

# enqueue a run
RESP=$(curl -s -X POST "$BACKEND_URL/gateway/orchestrate" -H 'Content-Type: application/json' -d '{"name":"ci-smoke","domain":"ci","brief":"ci smoke"}')
echo "Enqueue response: $RESP"
RUN_ID=$(echo "$RESP" | python -c "import sys,json;print(json.load(sys.stdin).get('run_id',''))")
if [ -z "$RUN_ID" ]; then
  echo "No run_id returned"
  exit 1
fi

# poll until completed or timeout
for i in $(seq 1 30); do
  sleep 2
  STATUS=$(curl -s "$BACKEND_URL/gateway/runs/$RUN_ID" | python -c "import sys,json;print(json.load(sys.stdin).get('status',''))")
  echo "Run $RUN_ID status: $STATUS"
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    exit 0
  fi
done

echo "Run did not complete in time"
exit 1
