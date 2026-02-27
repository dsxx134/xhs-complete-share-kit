# Xiaohongshu MCP API Quick Reference

## Core Endpoints

- `GET /api/v1/login/status`
- `POST /api/v1/feeds/search`
- `POST /api/v1/user/profile`
- `POST /api/v1/feeds/detail`

## Minimal Request Shapes

### Search feeds

```json
{
  "keyword": "target keyword",
  "filters": {
    "sort_by": "综合",
    "note_type": "不限",
    "publish_time": "不限",
    "search_scope": "不限",
    "location": "不限"
  }
}
```

### User profile

```json
{
  "user_id": "user id",
  "xsec_token": "token from search or feed card"
}
```

### Feed detail

```json
{
  "feed_id": "feed id",
  "xsec_token": "token for this feed",
  "load_all_comments": false
}
```

## Common Failure Patterns

### `is_logged_in` is false

- Cause: MCP login expired.
- Action: refresh login via QR code flow and retry.

### `/feeds/detail` timeout or HTTP 500

- Cause: target note unavailable or transient service instability.
- Action:
- retry detail call 1-3 times with short sleep.
- keep partial item with `error` field instead of dropping the record.

### Search returns mixed users

- Cause: keyword search is fuzzy.
- Action:
- prefer exact nickname first.
- if known, pass `--user-id` and `--seed-token` to bypass fuzzy resolution.

## Output Validation Checklist

- `counts.returned_items_count` equals requested count (or explain fewer available feeds).
- `items[*].urls.address_bar_detail_url` exists.
- `items[*].interact` is present (at least as card fallback).
- `errors` list is empty or explicitly explained.
