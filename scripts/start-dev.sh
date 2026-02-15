#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$REPO_ROOT/backend"
FRONTEND_DIR="$REPO_ROOT/frontend"
BACKEND_URL="http://127.0.0.1:8000/health"
FRONTEND_URL="http://127.0.0.1:5173"

log() {
  echo "[start-dev] $*"
}

print_manual_port_help() {
  local port="$1"

  cat <<EOF
[start-dev] Manual fix steps for port $port:
  1) Show what is listening:
    lsof -nP -iTCP:$port -sTCP:LISTEN
  2) Stop the process (replace <PID>):
    kill <PID>
  3) If needed, force stop:
    kill -9 <PID>
  4) Confirm port is free:
    lsof -nP -iTCP:$port -sTCP:LISTEN || true
EOF
}

wait_for_url() {
  local name="$1"
  local url="$2"
  local attempts=30
  local delay_seconds=1
  local attempt=1

  while [[ "$attempt" -le "$attempts" ]]; do
    if curl -fsS "$url" >/dev/null 2>&1; then
      log "$name is ready ($url)"
      return 0
    fi

    log "Waiting for $name ($attempt/$attempts)..."
    sleep "$delay_seconds"
    attempt=$((attempt + 1))
  done

  log "$name did not become ready in time ($url)"
  return 1
}

ensure_port_available() {
  local port="$1"
  local service_name="$2"
  local listeners
  listeners="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN 2>/dev/null || true)"

  if [[ -n "$listeners" ]]; then
    log "$service_name cannot start because port $port is already in use"
    echo "$listeners"
    print_manual_port_help "$port"
    log "After freeing the port, run ./scripts/start-dev.sh again"
    exit 1
  fi
}

log "Checking prerequisites"

if [[ ! -x "$BACKEND_DIR/.venv/bin/python" ]]; then
  echo "Missing backend virtualenv at $BACKEND_DIR/.venv"
  echo "Run: cd backend && python3 -m venv .venv && .venv/bin/python -m pip install -e ."
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR/node_modules" ]]; then
  echo "Missing frontend dependencies in $FRONTEND_DIR/node_modules"
  echo "Run: cd frontend && npm install"
  exit 1
fi

ensure_port_available 8000 "Backend"
ensure_port_available 5173 "Frontend"

BACKEND_PID=""
FRONTEND_PID=""

cleanup() {
  if [[ -n "$FRONTEND_PID" ]] && kill -0 "$FRONTEND_PID" 2>/dev/null; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi

  if [[ -n "$BACKEND_PID" ]] && kill -0 "$BACKEND_PID" 2>/dev/null; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
}

trap cleanup EXIT INT TERM

log "Starting backend API on http://127.0.0.1:8000"
"$BACKEND_DIR/.venv/bin/python" -m uvicorn app.api.main:app --host 127.0.0.1 --port 8000 --app-dir "$BACKEND_DIR" &
BACKEND_PID=$!
log "Backend process started (pid=$BACKEND_PID)"

log "Starting frontend dev server on http://127.0.0.1:5173"
(
  cd "$FRONTEND_DIR"
  npm run dev -- --host 127.0.0.1 --port 5173
) &
FRONTEND_PID=$!
log "Frontend process started (pid=$FRONTEND_PID)"

wait_for_url "Backend" "$BACKEND_URL"
wait_for_url "Frontend" "$FRONTEND_URL"
log "All services are up"
log "Frontend: $FRONTEND_URL"
log "Backend:  http://127.0.0.1:8000"
log "Press Ctrl+C to stop both services"

while true; do
  if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
    log "Backend exited"
    wait "$BACKEND_PID" || true
    break
  fi

  if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
    log "Frontend exited"
    wait "$FRONTEND_PID" || true
    break
  fi

  sleep 1
done
