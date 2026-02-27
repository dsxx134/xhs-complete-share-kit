#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_URL="${1:-http://127.0.0.1:18060}"

echo "[KB] Required docs:"
echo "  - $ROOT_DIR/AGENTS.md"
echo "  - $ROOT_DIR/knowledge/KNOWLEDGE_BASE.md"

if [[ ! -f "$ROOT_DIR/AGENTS.md" ]]; then
  echo "[KB][ERROR] Missing AGENTS.md"
  exit 1
fi
if [[ ! -f "$ROOT_DIR/knowledge/KNOWLEDGE_BASE.md" ]]; then
  echo "[KB][ERROR] Missing knowledge base"
  exit 1
fi

health="$(curl -sS "$BASE_URL/health" || true)"
login="$(curl -sS "$BASE_URL/api/v1/login/status" || true)"

echo "[KB] health: ${health:-unreachable}"
echo "[KB] login : ${login:-unreachable}"

if [[ -f "$ROOT_DIR/config/feishu_config.json" ]]; then
  python3 - <<'PY' "$ROOT_DIR/config/feishu_config.json"
import json,sys
cfg=json.load(open(sys.argv[1],'r',encoding='utf-8'))
keys=['app_id','app_secret','app_token','table_id']
bad=[k for k in keys if (not str(cfg.get(k,'')).strip()) or ('xxxx' in str(cfg.get(k,'')).lower())]
if bad:
    print('[KB] feishu config: INVALID ->', ','.join(bad))
else:
    print('[KB] feishu config: OK')
PY
else
  echo "[KB] feishu config: missing (config/feishu_config.json)"
fi

echo "[KB] preflight done"
