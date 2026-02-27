#!/usr/bin/env python3
"""
Fetch recent Xiaohongshu posts for a target user via local xiaohongshu-mcp HTTP API.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import time
from typing import Any, Dict, List, Optional

import requests


class XHSMCPClient:
    def __init__(self, base_url: str, timeout_sec: int) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = (10, max(10, timeout_sec))
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        resp = self.session.get(self.base_url + path, params=params, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()

    def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = self.session.post(self.base_url + path, json=payload, timeout=self.timeout)
        resp.raise_for_status()
        return resp.json()


def utc_iso_from_ms(ms: Optional[int]) -> Optional[str]:
    if not ms:
        return None
    return dt.datetime.fromtimestamp(ms / 1000, tz=dt.timezone.utc).isoformat()


def resolve_target_user(
    client: XHSMCPClient, username: str
) -> Dict[str, Optional[str]]:
    payload = {
        "keyword": username,
        "filters": {
            "sort_by": "综合",
            "note_type": "不限",
            "publish_time": "不限",
            "search_scope": "不限",
            "location": "不限",
        },
    }
    data = client.post("/feeds/search", payload)
    feeds = ((data.get("data") or {}).get("feeds") or [])
    if not feeds:
        raise RuntimeError(f"No search results for keyword: {username}")

    def candidate_score(feed: Dict[str, Any]) -> int:
        user = ((feed.get("noteCard") or {}).get("user") or {})
        nickname = user.get("nickname") or ""
        if nickname == username:
            return 0
        if username in nickname:
            return 1
        if nickname and nickname in username:
            return 2
        return 9

    chosen = sorted(feeds, key=candidate_score)[0]
    user = ((chosen.get("noteCard") or {}).get("user") or {})
    return {
        "user_id": user.get("userId") or user.get("user_id"),
        "seed_token": chosen.get("xsecToken") or chosen.get("xsec_token"),
        "nickname": user.get("nickname"),
    }


def build_item_skeleton(
    rank: int,
    feed_id: Optional[str],
    xsec_token: Optional[str],
    card: Dict[str, Any],
    user_id: str,
) -> Dict[str, Any]:
    return {
        "rank": rank,
        "feed_id": feed_id,
        "xsec_token": xsec_token,
        "urls": {
            "address_bar_detail_url": (
                f"https://www.xiaohongshu.com/explore/{feed_id}" if feed_id else None
            ),
            "detail_url_with_token": (
                f"https://www.xiaohongshu.com/explore/{feed_id}?xsec_token={xsec_token}&xsec_source=pc_feed"
                if feed_id and xsec_token
                else None
            ),
            "author_profile_url": f"https://www.xiaohongshu.com/user/profile/{user_id}",
        },
        "title": card.get("displayTitle"),
        "desc": None,
        "type": card.get("type"),
        "publish_time_ms": None,
        "publish_time_utc": None,
        "ip_location": None,
        "interact": card.get("interactInfo") or {},
        "images": [],
        "author": card.get("user") or {"userId": user_id},
        "comments_summary": {"count_loaded": 0, "has_more": None, "cursor": None},
        "comments": [],
        "error": None,
    }


def fetch_detail_for_item(
    client: XHSMCPClient,
    item: Dict[str, Any],
    retries: int,
) -> None:
    feed_id = item.get("feed_id")
    xsec_token = item.get("xsec_token")
    if not feed_id or not xsec_token:
        item["error"] = "missing feed_id/xsec_token"
        return

    payload = {
        "feed_id": feed_id,
        "xsec_token": xsec_token,
        "load_all_comments": False,
    }

    last_err: Optional[str] = None
    for attempt in range(1, retries + 1):
        try:
            data = client.post("/feeds/detail", payload)
            inner = ((data.get("data") or {}).get("data") or {})
            note = inner.get("note") or {}
            comments = inner.get("comments") or {}
            comment_list = comments.get("list") or []

            item["title"] = note.get("title") or item.get("title")
            item["desc"] = note.get("desc")
            item["type"] = note.get("type") or item.get("type")
            item["publish_time_ms"] = note.get("time")
            item["publish_time_utc"] = utc_iso_from_ms(note.get("time"))
            item["ip_location"] = note.get("ipLocation")
            item["interact"] = note.get("interactInfo") or item.get("interact") or {}
            item["images"] = [
                {
                    "url": img.get("urlDefault") or img.get("urlPre") or img.get("url"),
                    "width": img.get("width"),
                    "height": img.get("height"),
                    "livePhoto": img.get("livePhoto"),
                }
                for img in (note.get("imageList") or [])
            ]
            item["author"] = note.get("user") or item.get("author") or {}
            item["comments_summary"] = {
                "count_loaded": len(comment_list),
                "has_more": comments.get("hasMore"),
                "cursor": comments.get("cursor"),
            }
            item["comments"] = [
                {
                    "id": c.get("id"),
                    "content": c.get("content"),
                    "likeCount": c.get("likeCount"),
                    "liked": c.get("liked"),
                    "createTime": c.get("createTime"),
                    "ipLocation": c.get("ipLocation"),
                    "userInfo": c.get("userInfo") or {},
                    "subCommentCount": c.get("subCommentCount"),
                }
                for c in comment_list
            ]
            item["error"] = None
            return
        except Exception as exc:  # noqa: BLE001
            last_err = f"attempt{attempt}: {exc}"
            time.sleep(0.8)

    item["error"] = last_err or "unknown detail error"


def render_markdown(result: Dict[str, Any]) -> str:
    lines: List[str] = []
    target_user = result["target_user"]
    counts = result["counts"]

    lines.append(f"# {target_user.get('nickname') or result.get('query_user')} recent posts")
    lines.append("")
    lines.append(
        f"- user: {target_user.get('nickname')} ({target_user.get('user_id')})"
    )
    lines.append(f"- profile: {target_user.get('profile_url')}")
    lines.append(
        f"- visible feeds: {counts.get('profile_feeds_total_visible')} | "
        f"requested: {counts.get('requested_recent_count')} | "
        f"returned: {counts.get('returned_items_count')} | "
        f"detail_success: {counts.get('detail_success_count')} | "
        f"detail_error: {counts.get('detail_error_count')}"
    )
    lines.append("")

    for item in result.get("items", []):
        interact = item.get("interact") or {}
        lines.append(f"## {item.get('rank')}. {item.get('title') or '(no title)'}")
        lines.append(
            f"- detail_url: {(item.get('urls') or {}).get('address_bar_detail_url')}"
        )
        lines.append(
            f"- token_url: {(item.get('urls') or {}).get('detail_url_with_token')}"
        )
        lines.append(
            f"- likedCount: {interact.get('likedCount')} | "
            f"collectedCount: {interact.get('collectedCount')} | "
            f"commentCount: {interact.get('commentCount')} | "
            f"sharedCount: {interact.get('sharedCount')}"
        )
        lines.append(
            f"- liked: {interact.get('liked')} | collected: {interact.get('collected')}"
        )
        lines.append(
            f"- images: {len(item.get('images') or [])} | "
            f"comments_loaded: {(item.get('comments_summary') or {}).get('count_loaded')}"
        )
        desc = (item.get("desc") or "").replace("\n", " ").strip()
        if len(desc) > 240:
            desc = desc[:240] + "..."
        lines.append(f"- content: {desc}")
        if item.get("error"):
            lines.append(f"- error: {item.get('error')}")
        lines.append("")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch recent user posts from Xiaohongshu MCP")
    parser.add_argument("--username", required=True, help="Target nickname keyword")
    parser.add_argument("--limit", type=int, default=20, help="Recent post count")
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Output directory for json and md files",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:18060/api/v1",
        help="xiaohongshu-mcp API base URL",
    )
    parser.add_argument("--timeout-sec", type=int, default=40, help="HTTP timeout seconds")
    parser.add_argument("--retries", type=int, default=2, help="Detail API retry count")
    parser.add_argument("--user-id", default=None, help="Optional resolved user id")
    parser.add_argument(
        "--seed-token",
        default=None,
        help="Optional seed xsec token to call /user/profile directly",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = XHSMCPClient(args.base_url, args.timeout_sec)

    login = client.get("/login/status")
    if not (login.get("success") and (login.get("data") or {}).get("is_logged_in")):
        raise RuntimeError("MCP is not logged in. Login first via /api/v1/login/qrcode.")

    resolved = {
        "user_id": args.user_id,
        "seed_token": args.seed_token,
        "nickname": args.username,
    }
    if not (resolved["user_id"] and resolved["seed_token"]):
        resolved = resolve_target_user(client, args.username)

    user_id = resolved.get("user_id")
    seed_token = resolved.get("seed_token")
    if not user_id or not seed_token:
        raise RuntimeError("Cannot resolve user_id or seed_token.")

    profile = client.post(
        "/user/profile",
        {"user_id": user_id, "xsec_token": seed_token},
    )
    profile_data = ((profile.get("data") or {}).get("data") or {})
    user_basic = profile_data.get("userBasicInfo") or {}
    interactions = profile_data.get("interactions") or []
    feeds = (profile_data.get("feeds") or [])[: max(1, args.limit)]

    result: Dict[str, Any] = {
        "query_user": args.username,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": {"service": "xiaohongshu-mcp", "base_url": args.base_url},
        "target_user": {
            "user_id": user_id,
            "nickname": user_basic.get("nickname") or resolved.get("nickname"),
            "desc": user_basic.get("desc"),
            "red_id": user_basic.get("redId"),
            "ip_location": user_basic.get("ipLocation"),
            "avatar": user_basic.get("images"),
            "background": user_basic.get("imageb"),
            "interactions": interactions,
            "profile_url": f"https://www.xiaohongshu.com/user/profile/{user_id}",
            "profile_url_with_token": (
                f"https://www.xiaohongshu.com/user/profile/{user_id}"
                f"?xsec_token={seed_token}&xsec_source=pc_note"
            ),
            "feeds_total_from_profile": len(profile_data.get("feeds") or []),
        },
        "counts": {},
        "items": [],
        "errors": [],
    }

    for idx, feed in enumerate(feeds, start=1):
        card = feed.get("noteCard") or {}
        item = build_item_skeleton(
            rank=idx,
            feed_id=feed.get("id"),
            xsec_token=feed.get("xsecToken") or feed.get("xsec_token"),
            card=card,
            user_id=user_id,
        )
        fetch_detail_for_item(client, item, retries=max(1, args.retries))
        if item.get("error"):
            result["errors"].append(
                {"rank": idx, "feed_id": item.get("feed_id"), "error": item.get("error")}
            )
        result["items"].append(item)
        time.sleep(0.12)

    result["counts"] = {
        "profile_feeds_total_visible": len(profile_data.get("feeds") or []),
        "requested_recent_count": max(1, args.limit),
        "returned_items_count": len(result["items"]),
        "detail_success_count": sum(1 for it in result["items"] if not it.get("error")),
        "detail_error_count": len(result["errors"]),
    }

    out_dir = pathlib.Path(args.output_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    basename = f"xhs_user_{user_id}_recent{max(1, args.limit)}"
    json_path = out_dir / f"{basename}.json"
    md_path = out_dir / f"{basename}.md"

    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(result), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "json": str(json_path),
                "md": str(md_path),
                "counts": result["counts"],
                "target_user": {
                    "user_id": user_id,
                    "nickname": result["target_user"]["nickname"],
                },
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
