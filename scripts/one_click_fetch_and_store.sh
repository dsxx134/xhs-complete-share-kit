#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage:"
  echo "  $0 <username> [limit] [work_dir] [feishu_config_json]"
  echo "Example:"
  echo "  $0 每日一花AI 20 \$HOME/xhs-mcp-workspace ./config/feishu_config.json"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
USERNAME="$1"
LIMIT="${2:-20}"
WORK_DIR="${3:-$HOME/xhs-mcp-workspace}"
CONFIG_PATH="${4:-$ROOT_DIR/config/feishu_config.json}"
QR_PATH="$ROOT_DIR/xhs_login_qrcode.png"

echo "[1/5] Install all ..."
"$ROOT_DIR/scripts/install_all.sh" "$WORK_DIR"

echo "[2/5] Start MCP ..."
"$ROOT_DIR/scripts/start_xhs_mcp.sh" "$WORK_DIR"

echo "[3/5] Check MCP status ..."
"$ROOT_DIR/scripts/check_xhs_mcp.sh"

LOGIN_JSON="$(curl -sS http://127.0.0.1:18060/api/v1/login/status || true)"
LOGGED_IN="$(python3 - <<'PY' "$LOGIN_JSON"
import json,sys
try:
    obj=json.loads(sys.argv[1])
    print("1" if (obj.get("data") or {}).get("is_logged_in") else "0")
except Exception:
    print("0")
PY
)"

if [[ "$LOGGED_IN" != "1" ]]; then
  echo "Not logged in. Generating QR code ..."
  python3 "$ROOT_DIR/scripts/get_login_qrcode.py" --output "$QR_PATH"
  echo "Please scan this QR code with Xiaohongshu app:"
  echo "  $QR_PATH"
  echo "Waiting up to 120 seconds for login ..."
  for _ in $(seq 1 120); do
    S="$(curl -sS http://127.0.0.1:18060/api/v1/login/status || true)"
    OK="$(python3 - <<'PY' "$S"
import json,sys
try:
    obj=json.loads(sys.argv[1])
    print("1" if (obj.get("data") or {}).get("is_logged_in") else "0")
except Exception:
    print("0")
PY
)"
    if [[ "$OK" == "1" ]]; then
      echo "Login success."
      break
    fi
    sleep 1
  done
fi

AFTER_LOGIN="$(curl -sS http://127.0.0.1:18060/api/v1/login/status || true)"
AFTER_OK="$(python3 - <<'PY' "$AFTER_LOGIN"
import json,sys
try:
    obj=json.loads(sys.argv[1])
    print("1" if (obj.get("data") or {}).get("is_logged_in") else "0")
except Exception:
    print("0")
PY
)"
if [[ "$AFTER_OK" != "1" ]]; then
  echo "Login still not complete. Please run this script again after scanning."
  exit 1
fi

if [[ ! -f "$CONFIG_PATH" ]]; then
  echo "Feishu config not found: $CONFIG_PATH"
  echo "Copy and fill: $ROOT_DIR/config/feishu_config.example.json -> $ROOT_DIR/config/feishu_config.json"
  exit 1
fi

PLACEHOLDER_CHECK="$(python3 - <<'PY' "$CONFIG_PATH"
import json,sys
cfg=json.load(open(sys.argv[1],'r',encoding='utf-8'))
vals=[cfg.get('app_id',''),cfg.get('app_secret',''),cfg.get('app_token',''),cfg.get('table_id','')]
bad=0
for v in vals:
    s=str(v)
    if not s or 'xxxx' in s.lower():
        bad=1
print("1" if bad else "0")
PY
)"
if [[ "$PLACEHOLDER_CHECK" == "1" ]]; then
  echo "Feishu config has placeholders. Please fill config first:"
  echo "  $CONFIG_PATH"
  exit 1
fi

echo "[4/5] Fetch + store ..."
"$ROOT_DIR/scripts/run_fetch_and_store.sh" "$USERNAME" "$LIMIT" "$WORK_DIR/output" "$CONFIG_PATH"

echo "[5/5] Done."
echo "Output dir: $WORK_DIR/output"
