#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage:"
  echo "  $0 <username> [limit] [output_dir] [feishu_config_json]"
  echo "Example:"
  echo "  $0 每日一花AI 20 \$HOME/xhs-mcp-workspace/output ./config/feishu_config.json"
  exit 1
fi

USERNAME="$1"
LIMIT="${2:-20}"
OUTPUT_DIR="${3:-$HOME/xhs-mcp-workspace/output}"
CONFIG_PATH="${4:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/config/feishu_config.json}"
SKILL_SCRIPT="$HOME/.codex/skills/xiaohongshu-mcp-crawler/scripts/fetch_user_recent_posts.py"
UPLOAD_SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/upload_to_feishu.py"

if [[ ! -f "$SKILL_SCRIPT" ]]; then
  echo "Skill script not found: $SKILL_SCRIPT"
  echo "Run install_all.sh first."
  exit 1
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Feishu config not found: $CONFIG_PATH"
  echo "Copy config/feishu_config.example.json to config/feishu_config.json and fill your values."
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

echo "[1/2] Fetching data ..."
FETCH_OUT="$(python3 "$SKILL_SCRIPT" --username "$USERNAME" --limit "$LIMIT" --output-dir "$OUTPUT_DIR")"
echo "$FETCH_OUT"

JSON_PATH="$(python3 - <<'PY' "$FETCH_OUT"
import json,sys
try:
    obj=json.loads(sys.argv[1])
    print(obj.get("json",""))
except Exception:
    print("")
PY
)"

if [[ -z "$JSON_PATH" || ! -f "$JSON_PATH" ]]; then
  echo "Cannot locate output json from fetch step."
  exit 1
fi

echo "[2/2] Uploading to Feishu ..."
python3 "$UPLOAD_SCRIPT" --input-json "$JSON_PATH" --config "$CONFIG_PATH"

echo "Done."
echo "Fetched JSON: $JSON_PATH"
