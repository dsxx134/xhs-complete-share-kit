#!/usr/bin/env bash
set -euo pipefail

# One-shot installer for sharing this kit with others.
# It installs skill files and prepares xiaohongshu-mcp source locally.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILL_SRC_DIR="$ROOT_DIR/skill/xiaohongshu-mcp-crawler"
SKILL_DST_DIR="$HOME/.codex/skills/xiaohongshu-mcp-crawler"
WORK_DIR="${1:-$HOME/xhs-mcp-workspace}"
MCP_DIR="$WORK_DIR/external/xiaohongshu-mcp"
BUNDLED_MCP_DIR="$ROOT_DIR/bundled/xiaohongshu-mcp"
RUNTIME_DIR="$WORK_DIR/runtime"

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH_RAW="$(uname -m)"
case "$ARCH_RAW" in
  arm64|aarch64) ARCH="arm64" ;;
  x86_64|amd64) ARCH="amd64" ;;
  *) ARCH="$ARCH_RAW" ;;
esac
PREBUILT_SRC="$ROOT_DIR/bundled/bin/${OS}-${ARCH}/xiaohongshu-mcp"
PREBUILT_DST="$RUNTIME_DIR/xiaohongshu-mcp"

echo "[1/6] Checking required commands..."
for cmd in python3; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing command: $cmd"
    echo "Please install it first, then rerun this script."
    exit 1
  fi
done

echo "[2/6] Installing skill files to ~/.codex/skills ..."
mkdir -p "$HOME/.codex/skills"
rm -rf "$SKILL_DST_DIR"
cp -R "$SKILL_SRC_DIR" "$SKILL_DST_DIR"
chmod +x "$SKILL_DST_DIR/scripts/fetch_user_recent_posts.py"

echo "[3/6] Preparing workspace at: $WORK_DIR"
mkdir -p "$WORK_DIR/external" "$WORK_DIR/output" "$WORK_DIR/logs" "$RUNTIME_DIR"

echo "[4/6] Installing bundled xiaohongshu-mcp source ..."
if [[ ! -d "$BUNDLED_MCP_DIR" ]]; then
  echo "Bundled MCP source missing: $BUNDLED_MCP_DIR"
  exit 1
fi
rm -rf "$MCP_DIR"
mkdir -p "$(dirname "$MCP_DIR")"
cp -R "$BUNDLED_MCP_DIR" "$MCP_DIR"

echo "[5/6] Preparing runtime binary ..."
if [[ -f "$PREBUILT_SRC" ]]; then
  cp "$PREBUILT_SRC" "$PREBUILT_DST"
  chmod +x "$PREBUILT_DST"
  echo "Using prebuilt binary: $PREBUILT_SRC"
else
  echo "No prebuilt binary for ${OS}-${ARCH}. Fallback to go run will be used."
  if ! command -v go >/dev/null 2>&1; then
    echo "Go is required in fallback mode. Please install Go."
    exit 1
  fi
fi

echo "[6/6] Python dependency check (requests) ..."
python3 - <<'PY'
import importlib.util
import subprocess
import sys

if importlib.util.find_spec("requests") is None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "requests"])
    print("Installed requests")
else:
    print("requests already installed")
PY

CONFIG_EXAMPLE="$ROOT_DIR/config/feishu_config.example.json"
CONFIG_REAL="$ROOT_DIR/config/feishu_config.json"
if [[ -f "$CONFIG_EXAMPLE" && ! -f "$CONFIG_REAL" ]]; then
  cp "$CONFIG_EXAMPLE" "$CONFIG_REAL"
  echo "Created config template: $CONFIG_REAL"
fi

echo
echo "Install done."
echo "Next:"
echo "  1) Start MCP: $ROOT_DIR/scripts/start_xhs_mcp.sh \"$WORK_DIR\""
echo "  2) Check status: $ROOT_DIR/scripts/check_xhs_mcp.sh"
echo "  3) Login until is_logged_in=true."
echo "  4) Fill $ROOT_DIR/config/feishu_config.json"
echo "  5) Run fetch+store: $ROOT_DIR/scripts/run_fetch_and_store.sh 每日一花AI 20 \"$WORK_DIR/output\" \"$ROOT_DIR/config/feishu_config.json\""
