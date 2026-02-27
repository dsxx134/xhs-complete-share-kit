---
name: xiaohongshu-mcp-crawler
description: Crawl Xiaohongshu notes through a local xiaohongshu-mcp HTTP service. Use when collecting recent posts for a specific user, exporting structured JSON/Markdown datasets, or troubleshooting MCP login and detail-fetch failures.
---

# Xiaohongshu MCP Crawler

## Overview

Use this skill to collect Xiaohongshu post data in a stable API-first way instead of brittle UI clicking. Prefer the local `xiaohongshu-mcp` HTTP endpoints for user search, profile feeds, and per-note details.

## Use This Skill When

- The user asks to fetch recent posts for a specific Xiaohongshu account.
- The user needs per-post detail fields: title, content, metrics, images, comments, links.
- UI automation is unstable due to anti-bot challenges or changing page structure.
- The task requires reproducible output files (`json` and `md`) in a local folder.

## Preconditions

1. Start `xiaohongshu-mcp` locally (default `http://127.0.0.1:18060`).
2. Ensure login status is valid:
```bash
curl -sS http://127.0.0.1:18060/api/v1/login/status
```
3. Confirm `is_logged_in` is `true` before running bulk collection.

## Workflow

### 1. Collect Recent Posts for a User

Run the bundled script:

```bash
python3 scripts/fetch_user_recent_posts.py \
  --username "<target_nickname>" \
  --limit 20 \
  --output-dir "<absolute_output_dir>"
```

Optional parameters:

- `--base-url` override MCP host.
- `--timeout-sec` set request timeout.
- `--retries` set retries for detail calls.
- `--user-id` and `--seed-token` bypass keyword user resolution when already known.

Expected outputs:

- `xhs_user_<user_id>_recent<limit>.json`
- `xhs_user_<user_id>_recent<limit>.md`

Both files include per-item `address_bar_detail_url` (`https://www.xiaohongshu.com/explore/{feed_id}`).

### 2. Validate the Result

Check key fields in generated JSON:

- `counts.returned_items_count == requested`
- `counts.detail_error_count == 0` (or inspect `errors`)
- `items[*].urls.address_bar_detail_url` is populated
- `items[*].interact` contains engagement fields when available

### 3. Handle Common Failures

If failures occur, load [references/api_reference.md](references/api_reference.md) and follow the troubleshooting section.

## Resources

- Script: [scripts/fetch_user_recent_posts.py](scripts/fetch_user_recent_posts.py)
- Reference: [references/api_reference.md](references/api_reference.md)
