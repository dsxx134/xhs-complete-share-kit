# Agent Rules for Xiaohongshu Search (Portable)

This repository uses the following default workflow when user asks:
"在小红书搜索 <关键词> 高赞 最近7天 前N 详细数据".

## Goal

Return top N Xiaohongshu notes for a keyword in recent 7 days, with rich detail:
title, metrics, content, tags, images, comments, and detail URL.

## Required Steps

1. Mandatory knowledge-base preflight (every run):
   - `bash scripts/kb_preflight.sh`
   - Read and follow:
     - `AGENTS.md`
     - `knowledge/KNOWLEDGE_BASE.md`
2. Ensure local MCP service is running:
   - `GET /health`
   - `GET /api/v1/login/status` must be `is_logged_in=true`.
3. Search notes:
   - Endpoint: `POST /api/v1/feeds/search`
   - Filters: keyword + `publish_time=一周内`
4. Sort strategy:
   - Try `sort_by=点赞最多`.
   - If search returns 500, fallback to `sort_by=综合`, then sort by like count locally.
5. For top N feeds, fetch detail:
   - Endpoint: `POST /api/v1/feeds/detail`
   - Parameters: `feed_id`, `xsec_token`, `load_all_comments=false` (default stable mode)
   - Retry each failed detail call up to 3 times with short sleep.
6. Extract rich fields:
   - Basic: `title`, `desc(content)`, `publish_time`, `ip_location`, author info
   - Metrics: liked/collected/comment/shared counts
   - Images: URL + width/height
   - Comments: loaded list + summary (`has_more`, `cursor`)
   - Tags: parse from content by regex `#xxx[话题]#`, fallback `#xxx#`
7. Save outputs:
   - JSON: `output/xhs_search_<keyword>_top<N>_recent7d_highlike_rich_detail.json`
   - Markdown: `output/xhs_search_<keyword>_top<N>_recent7d_highlike_rich_detail.md`
8. Report back:
   - success/error counts
   - top N summary with title, likes, URL
   - explain fallback if API sorting failed
9. Mandatory run log append:
   - `python3 scripts/kb_append_log.py --title ... --input ... --strategy ... --output ... --status ...`

## Default Field Contract

Each item should include at least:
- `rank`
- `feed_id`
- `detail_url`
- `title`
- `content`
- `tags`
- `metrics` (`liked_count`, `collected_count`, `comment_count`, `shared_count`)
- `images[]`
- `comments_summary`
- `comments[]`
- `error` (null when success)

## Reliability Notes

- `点赞最多` may return 500 on some sessions; fallback path is mandatory.
- Comment loading can be slow; prefer stable mode first (`load_all_comments=false`).
- Always keep partial results and explicit `error` fields; do not silently drop failed notes.
