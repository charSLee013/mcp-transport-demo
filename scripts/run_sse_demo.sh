#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PY="${ROOT_DIR}/.venv/bin/python"
SERVER_PY="${ROOT_DIR}/examples/snippets/servers/sse_progress_demo.py"
CLIENT_PY="${ROOT_DIR}/examples/snippets/clients/sse_progress_client.py"
LOG_FILE="/tmp/sse_server.log"

if [[ ! -x "$PY" ]]; then
  echo "[run] .venv python not found at $PY" >&2
  exit 1
fi

echo "[run] killing existing demo server (if any)"
# best-effort kill by script path
if pgrep -f "$SERVER_PY" >/dev/null 2>&1; then
  pkill -9 -f "$SERVER_PY" || true
fi
# also kill anything listening on :8000 (best-effort)
if command -v lsof >/dev/null 2>&1; then
  if lsof -ti :8000 >/dev/null 2>&1; then
    lsof -ti :8000 | xargs -r kill -9 || true
  fi
fi

echo "[run] starting server -> $SERVER_PY"
(
  cd "$ROOT_DIR"
  PYTHONPATH=src "$PY" "$SERVER_PY" >"$LOG_FILE" 2>&1 &
  echo $! > /tmp/sse_server.pid
)
SERVER_PID="$(cat /tmp/sse_server.pid)"
echo "[run] server pid=${SERVER_PID} (logs: $LOG_FILE)"

cleanup() {
  echo "[run] stopping server pid=${SERVER_PID}"
  kill "$SERVER_PID" >/dev/null 2>&1 || true
  wait "$SERVER_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# wait until server responds on /messages/ (POST returns 400 without session_id)
echo -n "[run] waiting for server to be ready"
for i in {1..20}; do
  if curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8000/messages/ | grep -q "^400$"; then
    echo " -> ready"
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

echo "[run] running client -> $CLIENT_PY (logging to /tmp/sse_client.log)"
:
> /tmp/sse_client.log
(
  cd "$ROOT_DIR"
  PYTHONPATH=src "$PY" "$CLIENT_PY" > /tmp/sse_client.log 2>&1
)
echo "[run] client output saved: /tmp/sse_client.log"

echo "[run] client finished; stopping server"
