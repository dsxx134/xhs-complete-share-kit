#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
from pathlib import Path

import requests


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Fetch login QR code from xiaohongshu-mcp")
    p.add_argument(
        "--base-url",
        default="http://127.0.0.1:18060/api/v1",
        help="xiaohongshu-mcp API base URL",
    )
    p.add_argument("--output", required=True, help="Output png path")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    out = Path(args.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    resp = requests.get(args.base_url.rstrip("/") + "/login/qrcode", timeout=(10, 30))
    resp.raise_for_status()
    data = resp.json()
    if not data.get("success"):
        raise RuntimeError(f"QR API failed: {data}")
    img = ((data.get("data") or {}).get("img") or "")
    if not img:
        raise RuntimeError("No img field returned by login/qrcode")

    prefix = "base64,"
    idx = img.find(prefix)
    b64 = img[idx + len(prefix) :] if idx >= 0 else img
    out.write_bytes(base64.b64decode(b64))

    print(
        json.dumps(
            {
                "ok": True,
                "output": str(out),
                "timeout": (data.get("data") or {}).get("timeout"),
                "is_logged_in": (data.get("data") or {}).get("is_logged_in"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
