#!/usr/bin/env bash
set -euo pipefail

WORK_DIR="${1:-$HOME/xhs-mcp-workspace}"
PID_FILE="$WORK_DIR/logs/xiaohongshu-mcp.pid"

if [[ ! -f "$PID_FILE" ]]; then
  echo "PID file not found: $PID_FILE"
  exit 0
fi

PID="$(cat "$PID_FILE" || true)"
if [[ -z "${PID:-}" ]]; then
  echo "Empty PID file."
  exit 0
fi

if kill -0 "$PID" >/dev/null 2>&1; then
  kill "$PID"
  echo "Stopped xiaohongshu-mcp (PID: $PID)"
else
  echo "Process not running: $PID"
fi

rm -f "$PID_FILE"
