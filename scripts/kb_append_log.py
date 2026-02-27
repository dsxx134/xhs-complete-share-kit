#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="Append run summary to knowledge/RUN_LOG.md")
    p.add_argument("--title", required=True, help="Run title")
    p.add_argument("--input", required=True, help="Input summary")
    p.add_argument("--strategy", required=True, help="Strategy summary")
    p.add_argument("--output", required=True, help="Output files summary")
    p.add_argument("--status", required=True, help="Status summary")
    p.add_argument("--notes", default="", help="Optional notes")
    args = p.parse_args()

    root = Path(__file__).resolve().parents[1]
    log_path = root / "knowledge" / "RUN_LOG.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    block = [
        f"## {ts} | {args.title}",
        "",
        f"- 输入：{args.input}",
        f"- 策略：{args.strategy}",
        f"- 输出：{args.output}",
        f"- 状态：{args.status}",
    ]
    if args.notes.strip():
        block.append(f"- 备注：{args.notes.strip()}")
    block.append("")

    with log_path.open("a", encoding="utf-8") as f:
        f.write("\n".join(block))

    print(str(log_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
