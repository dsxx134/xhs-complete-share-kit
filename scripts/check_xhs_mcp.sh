#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:18060/api/v1}"

echo "Checking service health ..."
curl -sS "${BASE_URL%/api/v1}/health" || true
echo
echo "Checking login status ..."
curl -sS "$BASE_URL/login/status" || true
echo
