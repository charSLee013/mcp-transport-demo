#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT_DIR}/.venv/bin/python"
SERVER_PY="${ROOT_DIR}/examples/snippets/servers/streamable_progress_demo.py"
CLIENT_PY="${ROOT_DIR}/examples/snippets/clients/streamable_progress_client.py"
LOG_FILE="/tmp/streamable_http_server.log"

if [[ ! -x "$PY" ]]; then
  echo "[run] .venv python not found at $PY" >&2
  exit 1
fi

echo "[run] killing existing demo server (if any)"
if pgrep -f "$SERVER_PY" >/dev/null 2>&1; then
  pkill -9 -f "$SERVER_PY" || true
fi
if command -v lsof >/dev/null 2>&1; then
  if lsof -ti :8000 >/dev/null 2>&1; then
    lsof -ti :8000 | xargs -r kill -9 || true
  fi
fi

echo "[run] starting server -> $SERVER_PY"
(
  cd "$ROOT_DIR"
  PYTHONPATH=src "$PY" "$SERVER_PY" >"$LOG_FILE" 2>&1 &
  echo $! > /tmp/streamable_http_server.pid
)
SERVER_PID="$(cat /tmp/streamable_http_server.pid)"
echo "[run] server pid=${SERVER_PID} (logs: $LOG_FILE)"

cleanup() {
  echo "[run] stopping server pid=${SERVER_PID}"
  kill "$SERVER_PID" >/dev/null 2>&1 || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo -n "[run] waiting for server to be ready"
for i in {1..20}; do
  STATUS="$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Content-Type: application/json" \
    -X POST \
    --data '{"jsonrpc":"2.0","method":"initialize","id":0,"params":{"protocolVersion":"2025-06-18","clientInfo":{"name":"probe","version":"0.0.0"},"capabilities":{}}}' \
    http://127.0.0.1:8000/mcp || true)"
  if [[ "$STATUS" =~ ^(200|202|400|401|403|406|422)$ ]]; then
    echo " -> ready (status=$STATUS)"
    break
  fi
  echo -n "."
  sleep 0.3
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "\n[run] server exited unexpectedly; tail $LOG_FILE:" >&2
    tail -n +1 "$LOG_FILE" >&2 || true
    exit 1
  fi
  if [[ "$i" -eq 20 ]]; then
    echo "\n[run] server readiness timed out; tail $LOG_FILE:" >&2
    tail -n +1 "$LOG_FILE" >&2 || true
    exit 1
  fi
done

echo "[run] sleeping 5s before client"
sleep 5

echo "[run] running client -> $CLIENT_PY (logging to /tmp/streamable_http_client.log)"
: > /tmp/streamable_http_client.log
(
  cd "$ROOT_DIR"
  PYTHONPATH=src "$PY" "$CLIENT_PY" > /tmp/streamable_http_client.log 2>&1
)
echo "[run] client output saved: /tmp/streamable_http_client.log"

echo "[run] client finished; stopping server"
