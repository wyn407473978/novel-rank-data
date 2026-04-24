from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from novel_rank_data.storage import ensure_dir


NUMERIC_FIELDS = ("chapters", "words", "views", "favorites", "comments", "revenue")


def _number(value: object) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _rate(part: float, whole: float) -> float:
    if whole <= 0:
        return 0.0
    return round(part / whole, 4)


def normalize_feedback(row: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(row)
    normalized.setdefault("created_at", datetime.now(UTC).isoformat())
    for field in NUMERIC_FIELDS:
        normalized[field] = _number(normalized.get(field))
    normalized["favorite_rate"] = _rate(normalized["favorites"], normalized["views"])
    normalized["comment_rate"] = _rate(normalized["comments"], normalized["views"])
    normalized["revenue_per_1k_views"] = round(_rate(normalized["revenue"], normalized["views"]) * 1000, 4)
    return normalized


def append_feedback(path: Path, row: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_feedback(row)
    ensure_dir(path.parent)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(normalized, ensure_ascii=False) + "\n")
    return normalized


def load_feedback(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def summarize_feedback(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = defaultdict(
        lambda: {
            "platform": "",
            "genre": "",
            "hook": "",
            "works": 0,
            "chapters": 0.0,
            "words": 0.0,
            "views": 0.0,
            "favorites": 0.0,
            "comments": 0.0,
            "revenue": 0.0,
        }
    )
    for row in rows:
        platform = str(row.get("platform") or "unknown")
        genre = str(row.get("genre") or "unknown")
        hook = str(row.get("hook") or "unknown")
        key = (platform, genre, hook)
        bucket = grouped[key]
        bucket["platform"] = platform
        bucket["genre"] = genre
        bucket["hook"] = hook
        bucket["works"] += 1
        for field in NUMERIC_FIELDS:
            bucket[field] += _number(row.get(field))

    summaries = []
    for bucket in grouped.values():
        bucket["favorite_rate"] = _rate(bucket["favorites"], bucket["views"])
        bucket["comment_rate"] = _rate(bucket["comments"], bucket["views"])
        bucket["revenue_per_1k_views"] = round(_rate(bucket["revenue"], bucket["views"]) * 1000, 4)
        for field in ("chapters", "words", "views", "favorites", "comments"):
            bucket[field] = int(bucket[field])
        summaries.append(dict(bucket))
    summaries.sort(key=lambda item: (item["revenue"], item["views"], item["favorite_rate"]), reverse=True)
    return summaries


def format_feedback_report(rows: list[dict[str, Any]]) -> str:
    summaries = summarize_feedback(rows)
    lines = [
        "# Web Novel Feedback Report",
        "",
        "说明: 这里统计的是手动录入的发布反馈，用来校准市场机会分数，不代表平台后台完整数据。",
        "",
    ]
    if not summaries:
        lines.append("暂无反馈数据。可以用 `npm run feedback:add -- ...` 录入第一条。")
        return "\n".join(lines) + "\n"

    for item in summaries:
        lines.extend(
            [
                f"## {item['platform']} / {item['genre']} / {item['hook']}",
                f"- Works: {item['works']}; Chapters: {item['chapters']}; Words: {item['words']}",
                f"- Views: {item['views']}; Favorites: {item['favorites']}; Comments: {item['comments']}",
                f"- Favorite rate: {item['favorite_rate']}; Comment rate: {item['comment_rate']}",
                f"- Revenue: {item['revenue']}; Revenue per 1k views: {item['revenue_per_1k_views']}",
                "",
            ]
        )
    return "\n".join(lines)
