from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
import json
import re
from typing import Any


GENRE_KEYWORDS = {
    "玄幻": ("玄幻", "修仙", "修真", "仙侠", "宗门", "飞升", "仙", "武圣"),
    "都市": ("都市", "神豪", "校花", "职场", "娱乐圈", "高武", "创业", "豪门"),
    "历史": ("历史", "三国", "大唐", "大明", "权谋", "王朝", "侯门", "朝堂"),
    "科幻": ("科幻", "末世", "赛博", "星际", "机甲", "高维", "无限", "副本"),
    "悬疑": ("悬疑", "规则", "诡异", "破案", "侦探", "惊悚", "怪谈"),
    "言情": ("言情", "先婚后爱", "总裁", "追妻", "破镜重圆", "甜宠", "暗恋"),
    "纯爱": ("纯爱", "双男主", "CP", "宿敌", "校草", "电竞"),
    "年代": ("年代", "重生", "下乡", "八零", "军婚", "种田"),
}

HOOK_KEYWORDS = {
    "系统/金手指": ("系统", "外挂", "金手指", "面板", "简化", "词条"),
    "重生/回档": ("重生", "回档", "重回", "再来一次", "重新做人"),
    "逆袭打脸": ("逆袭", "打脸", "退婚", "翻身", "崛起", "复仇"),
    "先婚后爱": ("先婚后爱", "联姻", "协议结婚", "婚后", "离婚"),
    "规则怪谈": ("规则", "怪谈", "副本", "诡异", "惊悚"),
    "末世生存": ("末世", "囤货", "求生", "天灾", "废土"),
    "经营种田": ("种田", "经营", "开店", "直播", "发家", "美食"),
    "高能关系": ("修罗场", "暗恋", "宿敌", "拉扯", "追妻", "掉马"),
}

STOPWORDS = {
    "小说",
    "一个",
    "他们",
    "她们",
    "我们",
    "你们",
    "这个",
    "那个",
    "开始",
    "自己",
    "首页",
    "官网",
    "平台",
    "移动端",
    "番茄小说网",
    "好看的小说尽在番",
    "茄小说官网",
    "现言",
}
NON_SPECIFIC_CATEGORIES = {"原创", "衍生"}


@dataclass
class MarketSlice:
    records: list[dict[str, Any]]
    top_genres: list[tuple[str, int]]
    top_hooks: list[tuple[str, int]]
    top_title_terms: list[tuple[str, int]]


def _now() -> datetime:
    return datetime.now(UTC)


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def load_normalized_records(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def infer_genre(record: dict[str, Any]) -> str | None:
    explicit = record.get("category") or record.get("subcategory")
    if isinstance(explicit, str) and explicit.strip() and explicit.strip() not in NON_SPECIFIC_CATEGORIES:
        return explicit.strip()
    corpus = " ".join(
        [
            record.get("title") or "",
            record.get("intro") or "",
            " ".join(record.get("tags") or []),
        ]
    )
    for genre, keywords in GENRE_KEYWORDS.items():
        if any(keyword in corpus for keyword in keywords):
            return genre
    return None


def infer_hooks(record: dict[str, Any]) -> list[str]:
    corpus = " ".join(
        [
            record.get("title") or "",
            record.get("intro") or "",
            " ".join(record.get("tags") or []),
        ]
    )
    hooks = [name for name, keywords in HOOK_KEYWORDS.items() if any(keyword in corpus for keyword in keywords)]
    return hooks


def infer_title_terms(record: dict[str, Any]) -> list[str]:
    title = record.get("title") or ""
    tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,8}", title)
    return [token for token in tokens if token not in STOPWORDS]


def enrich_record(record: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(record)
    enriched["genre_inferred"] = infer_genre(record)
    enriched["hooks_inferred"] = infer_hooks(record)
    enriched["title_terms"] = infer_title_terms(record)
    return enriched


def filter_records_by_days(records: list[dict[str, Any]], days: int) -> list[dict[str, Any]]:
    cutoff = _now() - timedelta(days=days)
    return [record for record in records if _parse_timestamp(record["captured_at"]) >= cutoff]


def build_market_slice(records: list[dict[str, Any]]) -> MarketSlice:
    genre_counter: Counter[str] = Counter()
    hook_counter: Counter[str] = Counter()
    title_counter: Counter[str] = Counter()
    for record in records:
        if record.get("genre_inferred"):
            genre_counter.update([record["genre_inferred"]])
        hook_counter.update(record.get("hooks_inferred") or [])
        title_counter.update(record.get("title_terms") or [])
    return MarketSlice(
        records=records,
        top_genres=genre_counter.most_common(5),
        top_hooks=hook_counter.most_common(5),
        top_title_terms=title_counter.most_common(8),
    )


def build_platform_windows(records: list[dict[str, Any]]) -> dict[str, dict[str, MarketSlice]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        grouped[record["platform"]].append(record)
    output: dict[str, dict[str, MarketSlice]] = {}
    for platform, items in grouped.items():
        output[platform] = {
            "daily": build_market_slice(filter_records_by_days(items, 1)),
            "weekly": build_market_slice(filter_records_by_days(items, 7)),
            "monthly": build_market_slice(filter_records_by_days(items, 30)),
        }
    return output


def build_cross_platform_trends(records: list[dict[str, Any]]) -> dict[str, list[tuple[str, int]]]:
    genre_counter: Counter[str] = Counter()
    hook_counter: Counter[str] = Counter()
    for record in records:
        if record.get("genre_inferred"):
            genre_counter.update([record["genre_inferred"]])
        hook_counter.update(record.get("hooks_inferred") or [])
    return {
        "genres": genre_counter.most_common(6),
        "hooks": hook_counter.most_common(6),
    }


def recommend_directions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_platform_genre: dict[str, Counter[str]] = defaultdict(Counter)
    by_platform_hook: dict[str, Counter[str]] = defaultdict(Counter)
    for record in records:
        platform = record["platform"]
        genre = record.get("genre_inferred") or "未明题材"
        by_platform_genre[platform].update([genre])
        by_platform_hook[platform].update(record.get("hooks_inferred") or [])

    directions = []
    for platform, genres in by_platform_genre.items():
        top_genre = genres.most_common(1)[0][0]
        top_hook = next(
            (name for name, _count in by_platform_hook[platform].most_common() if name),
            "强冲突开局",
        )
        directions.append(
            {
                "platform": platform,
                "genre": top_genre,
                "hook": top_hook,
                "warning": "避免只复制标题句式，优先复用读者承诺与节奏。",
            }
        )
        if len(directions) == 3:
            break
    return directions
