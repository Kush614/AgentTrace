#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="${HOME}/go-install/go/bin:${PATH}"

cd "$ROOT"
go test ./...
go build -o bin/policy-gate .

echo "Starting policy-gate on :8091..."
./bin/policy-gate &
PID=$!
trap 'kill $PID 2>/dev/null || true' EXIT
sleep 0.5

REQUESTS="${REQUESTS:-10000}"
CONCURRENCY="${CONCURRENCY:-64}"

echo "Load test: ${REQUESTS} requests, concurrency ${CONCURRENCY}"
go run ./cmd/loadtest \
  -url http://127.0.0.1:8091/v1/evaluate \
  -n "$REQUESTS" \
  -c "$CONCURRENCY"

echo
echo "Server metrics:"
curl -s http://127.0.0.1:8091/v1/metrics | python3 -m json.tool
