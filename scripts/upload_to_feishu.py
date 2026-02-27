#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

import requests


def parse_int(v: Any) -> int:
    if v is None:
        return 0
    if isinstance(v, int):
        return v
    s = str(v).strip()
    if not s:
        return 0
    try:
        return int(float(s))
    except Exception:
        return 0


def load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def get_tenant_token(app_id: str, app_secret: str) -> str:
    url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
    resp = requests.post(
        url,
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=(10, 30),
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Get tenant token failed: {data}")
    token = data.get("tenant_access_token")
    if not token:
        raise RuntimeError("No tenant_access_token in response")
    return token


def build_records(data: Dict[str, Any], field_map: Dict[str, str]) -> List[Dict[str, Any]]:
    query_user = data.get("query_user") or (data.get("query") or {}).get("keyword") or ""
    generated_at = data.get("generated_at") or ""
    items = data.get("items") or []
    records: List[Dict[str, Any]] = []

    for item in items:
        if item.get("error"):
            # Skip failed detail items by default.
            continue
        interact = item.get("interact") or {}
        fields: Dict[str, Any] = {}

        def put(key: str, value: Any) -> None:
            field_name = field_map.get(key)
            if field_name:
                fields[field_name] = value

        put("title", item.get("title") or "")
        put("content", item.get("desc") or "")
        put("author", (item.get("author") or {}).get("nickname") or "")
        put("liked_count", parse_int(interact.get("likedCount")))
        put("collected_count", parse_int(interact.get("collectedCount")))
        put("comment_count", parse_int(interact.get("commentCount")))
        put("shared_count", parse_int(interact.get("sharedCount")))
        put("detail_url", ((item.get("urls") or {}).get("address_bar_detail_url") or ""))
        put("feed_id", item.get("feed_id") or "")
        put("rank", parse_int(item.get("rank")))
        put("keyword", query_user)
        put("captured_at", generated_at)

        records.append({"fields": fields})

    return records


def upload_records(
    tenant_token: str,
    app_token: str,
    table_id: str,
    records: List[Dict[str, Any]],
    batch_size: int = 500,
) -> Dict[str, int]:
    url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create"
    headers = {
        "Authorization": f"Bearer {tenant_token}",
        "Content-Type": "application/json",
    }

    success = 0
    failed = 0
    for i in range(0, len(records), batch_size):
        chunk = records[i : i + batch_size]
        resp = requests.post(url, headers=headers, json={"records": chunk}, timeout=(10, 60))
        if resp.status_code >= 400:
            failed += len(chunk)
            continue
        data = resp.json()
        if data.get("code") == 0:
            success += len(chunk)
        else:
            failed += len(chunk)
    return {"success": success, "failed": failed}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Upload fetched XHS data into Feishu Bitable")
    p.add_argument("--input-json", required=True, help="Path to fetched JSON file")
    p.add_argument("--config", required=True, help="Path to feishu_config.json")
    p.add_argument("--dry-run", action="store_true", help="Build records only, do not upload")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    data = load_json(args.input_json)
    cfg = load_json(args.config)

    app_id = cfg.get("app_id", "")
    app_secret = cfg.get("app_secret", "")
    app_token = cfg.get("app_token", "")
    table_id = cfg.get("table_id", "")
    field_map = cfg.get("field_map") or {}
    if not all([app_id, app_secret, app_token, table_id]):
        raise RuntimeError("Config missing one of app_id/app_secret/app_token/table_id")

    records = build_records(data, field_map)
    if args.dry_run:
        print(
            json.dumps(
                {"ok": True, "mode": "dry-run", "records_built": len(records)},
                ensure_ascii=False,
            )
        )
        return 0

    token = get_tenant_token(app_id, app_secret)
    stats = upload_records(token, app_token, table_id, records)
    print(json.dumps({"ok": True, "records_built": len(records), **stats}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
