#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
RUN_DIR="$ROOT_DIR/.run"

BACKEND_PID_FILE="$RUN_DIR/backend.pid"
FRONTEND_PID_FILE="$RUN_DIR/frontend.pid"
BACKEND_LOG="$RUN_DIR/backend.log"
FRONTEND_LOG="$RUN_DIR/frontend.log"

mkdir -p "$RUN_DIR"

if [[ ! -x "$BACKEND_DIR/venv/bin/python" ]]; then
  echo "[ERROR] 未找到后端虚拟环境 Python: $BACKEND_DIR/venv/bin/python"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "[ERROR] 未找到 npm，请先安装 Node.js/npm"
  exit 1
fi

cleanup_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti tcp:"$port" 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "[INFO] 端口 $port 已被占用，正在清理..."
    echo "$pids" | xargs kill -9 2>/dev/null || true
  fi
}

wait_http_ok() {
  local url="$1"
  local retries="${2:-30}"
  local interval="${3:-0.5}"
  for _ in $(seq 1 "$retries"); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      return 0
    fi
    sleep "$interval"
  done
  return 1
}

cleanup_port 8000
cleanup_port 5173

echo "[INFO] 启动后端服务 (8000)..."
(
  cd "$BACKEND_DIR"
  nohup "$BACKEND_DIR/venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 >"$BACKEND_LOG" 2>&1 &
  echo $! >"$BACKEND_PID_FILE"
)

echo "[INFO] 启动前端服务 (5173)..."
(
  cd "$FRONTEND_DIR"
  nohup npm run dev -- --host 0.0.0.0 --port 5173 >"$FRONTEND_LOG" 2>&1 &
  echo $! >"$FRONTEND_PID_FILE"
)

if wait_http_ok "http://127.0.0.1:8000/health" 40 0.5; then
  echo "[OK] 后端已启动: http://127.0.0.1:8000"
else
  echo "[WARN] 后端健康检查未通过，请查看日志: $BACKEND_LOG"
fi

if wait_http_ok "http://127.0.0.1:5173" 40 0.5; then
  echo "[OK] 前端已启动: http://127.0.0.1:5173"
else
  echo "[WARN] 前端健康检查未通过，请查看日志: $FRONTEND_LOG"
fi

echo "[INFO] PID 文件:"
echo "  - $BACKEND_PID_FILE ($(cat "$BACKEND_PID_FILE" 2>/dev/null || echo N/A))"
echo "  - $FRONTEND_PID_FILE ($(cat "$FRONTEND_PID_FILE" 2>/dev/null || echo N/A))"
echo "[INFO] 日志文件:"
echo "  - $BACKEND_LOG"
echo "  - $FRONTEND_LOG"
