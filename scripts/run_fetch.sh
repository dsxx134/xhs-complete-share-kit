#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage:"
  echo "  $0 <username> [limit] [output_dir]"
  echo "Example:"
  echo "  $0 每日一花AI 20 \$HOME/xhs-mcp-workspace/output"
  exit 1
fi

USERNAME="$1"
LIMIT="${2:-20}"
OUTPUT_DIR="${3:-$HOME/xhs-mcp-workspace/output}"
SKILL_SCRIPT="$HOME/.codex/skills/xiaohongshu-mcp-crawler/scripts/fetch_user_recent_posts.py"

if [[ ! -f "$SKILL_SCRIPT" ]]; then
  echo "Skill script not found: $SKILL_SCRIPT"
  echo "Run install_all.sh first."
  exit 1
fi

mkdir -p "$OUTPUT_DIR"

python3 "$SKILL_SCRIPT" \
  --username "$USERNAME" \
  --limit "$LIMIT" \
  --output-dir "$OUTPUT_DIR"
