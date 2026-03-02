#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_DIR="$ROOT_DIR/.run"

BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"

kill_from_pid_file() {
  local file="$1"
  local name="$2"
  if [[ -f "$file" ]]; then
    local pid
    pid="$(cat "$file" 2>/dev/null || true)"
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      echo "[INFO] 停止 $name (PID=$pid)..."
      kill "$pid" 2>/dev/null || true
      sleep 0.5
      if kill -0 "$pid" 2>/dev/null; then
        kill -9 "$pid" 2>/dev/null || true
      fi
    fi
    rm -f "$file"
  fi
}

kill_from_pid_file "$BACKEND_PID_FILE" "后端"
kill_from_pid_file "$FRONTEND_PID_FILE" "前端"

echo "[INFO] 清理 8000/5173 端口残留进程..."
lsof -ti tcp:8000,tcp:5173 2>/dev/null | xargs kill -9 2>/dev/null || true

echo "[OK] 前后端服务已停止"
