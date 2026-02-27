#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="${1:-$HOME/xhs-mcp-workspace}"
MCP_DIR="$WORK_DIR/external/xiaohongshu-mcp"
BIN_PATH="$WORK_DIR/runtime/xiaohongshu-mcp"
LOG_DIR="$WORK_DIR/logs"
PID_FILE="$LOG_DIR/xiaohongshu-mcp.pid"
LOG_FILE="$LOG_DIR/xiaohongshu-mcp.log"

mkdir -p "$LOG_DIR"

if [[ ! -d "$MCP_DIR" ]]; then
  echo "MCP source not found: $MCP_DIR"
  echo "Run install_all.sh first."
  exit 1
fi

if [[ -f "$PID_FILE" ]]; then
  PID="$(cat "$PID_FILE" || true)"
  if [[ -n "${PID:-}" ]] && kill -0 "$PID" >/dev/null 2>&1; then
    echo "xiaohongshu-mcp already running with PID: $PID"
    exit 0
  fi
fi

echo "Starting xiaohongshu-mcp ..."
if [[ -x "$BIN_PATH" ]]; then
  (
    cd "$MCP_DIR"
    nohup "$BIN_PATH" >"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"
  )
else
  if ! command -v go >/dev/null 2>&1; then
    echo "No runtime binary and go not found. Run install_all.sh again."
    exit 1
  fi
  (
    cd "$MCP_DIR"
    nohup go run . >"$LOG_FILE" 2>&1 &
    echo $! >"$PID_FILE"
  )
fi

sleep 2
if command -v lsof >/dev/null 2>&1; then
  lsof -iTCP:18060 -sTCP:LISTEN -n -P || true
fi

echo "Started. PID: $(cat "$PID_FILE")"
echo "Log: $LOG_FILE"
