from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Any


TITLE_KEYS = ("bookName", "book_name", "bookTitle", "novelName", "title", "name")
AUTHOR_KEYS = ("authorName", "author_name", "author", "writer", "authorNickName")
CATEGORY_KEYS = ("categoryName", "category_name", "category", "className", "class_name")
SUBCATEGORY_KEYS = ("subCategoryName", "sub_category_name", "subCategory", "subCateName")
INTRO_KEYS = ("intro", "description", "desc", "summary", "bookIntro", "abstract")
TAG_KEYS = ("tagList", "tags", "tag_name", "keywords", "labelList", "themeTags")
RANK_KEYS = ("rank", "rankNo", "rankNum", "sortNo", "serialNo", "position", "idx")
WORD_COUNT_KEYS = ("wordCount", "word_count", "size", "words", "totalWordNum")
STATUS_KEYS = ("bookStatus", "serialStatus", "status", "writingStatus")
ID_KEYS = ("bookId", "book_id", "novelId", "itemId", "id")


BOOK_LINK_HINTS = ("book", "novel", "info", "catalog", "book_id", "onebook")
BOOK_TEXT_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9《》【】·\-\[\]（）()]{2,40}")
NOISE_TITLES = {
    "首页",
    "排行",
    "排行榜",
    "更多",
    "全部",
    "登录",
    "注册",
    "最近更新",
    "查看全部",
    "作家专区",
    "男频精选",
    "女频精选",
    "作品库",
    "VIP作品",
    "完结作品",
    "驻站作品",
    "经典文库",
    "免费文库",
    "晋江小报",
    "作者",
}
NOISE_TITLE_PATTERNS = (
    "公告",
    "公示",
    "计划",
    "活动",
    "官网",
    "平台",
    "作家",
    "维权",
    "处罚",
    "升级",
    "上线",
    "福利",
    "拟获奖",
    "护航",
    "治理",
    "登录",
    "注册",
    "下载",
)
GENERIC_CATEGORY_LABELS = {
    "玄幻",
    "奇幻",
    "武侠",
    "仙侠",
    "都市",
    "都市娱乐",
    "现实",
    "历史",
    "军事",
    "科幻",
    "游戏",
    "悬疑",
    "总裁豪门",
    "穿越历史",
    "原创",
    "移动端",
}


def _pick_first(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, "", [], {}):
            return payload[key]
    return None


def _pick_first_key_value(payload: dict[str, Any], keys: tuple[str, ...]) -> tuple[str | None, Any]:
    for key in keys:
        if key in payload and payload[key] not in (None, "", [], {}):
            return key, payload[key]
    return None, None


def _normalize_tags(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [token.strip() for token in re.split(r"[,|/、\s]+", value) if token.strip()]
    if isinstance(value, list):
        tags = []
        for item in value:
            if isinstance(item, str) and item.strip():
                tags.append(item.strip())
            elif isinstance(item, dict):
                tag_value = _pick_first(item, ("name", "tagName", "title"))
                if isinstance(tag_value, str) and tag_value.strip():
                    tags.append(tag_value.strip())
        return tags
    return []


def _strip_html(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


@dataclass
class ParsedDocument:
    title: str
    visible_text: str
    anchors: list[dict[str, str]]
    scripts: list[dict[str, str]]


class DocumentParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._title_parts: list[str] = []
        self._text_parts: list[str] = []
        self._anchors: list[dict[str, str]] = []
        self._scripts: list[dict[str, str]] = []
        self._in_title = False
        self._anchor_href: str | None = None
        self._anchor_text_parts: list[str] = []
        self._script_attrs: dict[str, str] | None = None
        self._script_parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {key: value or "" for key, value in attrs}
        if tag == "title":
            self._in_title = True
        elif tag == "a":
            self._anchor_href = attrs_dict.get("href")
            self._anchor_text_parts = []
        elif tag == "script":
            self._script_attrs = attrs_dict
            self._script_parts = []

    def handle_endtag(self, tag: str) -> None:
        if tag == "title":
            self._in_title = False
        elif tag == "a":
            if self._anchor_href:
                text = re.sub(r"\s+", " ", "".join(self._anchor_text_parts)).strip()
                self._anchors.append({"href": self._anchor_href, "text": text})
            self._anchor_href = None
            self._anchor_text_parts = []
        elif tag == "script":
            if self._script_attrs is not None:
                self._scripts.append(
                    {"attrs": self._script_attrs, "content": "".join(self._script_parts).strip()}
                )
            self._script_attrs = None
            self._script_parts = []

    def handle_data(self, data: str) -> None:
        cleaned = re.sub(r"\s+", " ", data).strip()
        if self._in_title and cleaned:
            self._title_parts.append(cleaned)
        if self._anchor_href is not None and cleaned:
            self._anchor_text_parts.append(cleaned)
        if self._script_attrs is not None:
            self._script_parts.append(data)
        elif cleaned:
            self._text_parts.append(cleaned)

    def parsed(self) -> ParsedDocument:
        return ParsedDocument(
            title=" ".join(self._title_parts).strip(),
            visible_text=" ".join(self._text_parts).strip(),
            anchors=self._anchors,
            scripts=self._scripts,
        )


def parse_document(html: str) -> ParsedDocument:
    parser = DocumentParser()
    parser.feed(html)
    return parser.parsed()


def _extract_balanced_json(text: str, start_index: int) -> str | None:
    if start_index >= len(text) or text[start_index] not in "{[":
        return None
    opening = text[start_index]
    closing = "}" if opening == "{" else "]"
    depth = 0
    in_string = False
    escaped = False
    for index in range(start_index, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return text[start_index : index + 1]
    return None


def _iter_json_blobs(script_text: str) -> list[Any]:
    blobs: list[Any] = []
    stripped = script_text.strip().removesuffix(";")
    if not stripped:
        return blobs
    candidates: list[str] = []
    if stripped.startswith("{") or stripped.startswith("["):
        candidates.append(stripped)

    markers = (
        "__INITIAL_STATE__",
        "__NEXT_DATA__",
        "__NUXT__",
        "window.__INITIAL_STATE__",
        "window.__NUXT__",
        "window.__NEXT_DATA__",
        "window.__DATA__",
        "rankData",
        "pageData",
        "props",
    )
    for marker in markers:
        for match in re.finditer(re.escape(marker), script_text):
            brace_index = min(
                [index for index in (script_text.find("{", match.end()), script_text.find("[", match.end())) if index != -1],
                default=-1,
            )
            if brace_index != -1:
                blob = _extract_balanced_json(script_text, brace_index)
                if blob:
                    candidates.append(blob)

    seen = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            blobs.append(json.loads(candidate))
        except json.JSONDecodeError:
            continue
    return blobs


def _record_from_dict(payload: dict[str, Any]) -> dict[str, Any] | None:
    title_key, title = _pick_first_key_value(payload, TITLE_KEYS)
    author = _pick_first(payload, AUTHOR_KEYS)
    if not isinstance(title, str) or len(title.strip()) < 2:
        return None
    normalized_title = title.strip()
    if _looks_like_noise_title(normalized_title):
        return None
    has_book_signal = any(
        _pick_first(payload, keys)
        for keys in (AUTHOR_KEYS, CATEGORY_KEYS, SUBCATEGORY_KEYS, INTRO_KEYS, TAG_KEYS, ID_KEYS, WORD_COUNT_KEYS)
    )
    if title_key == "name" and not has_book_signal:
        return None
    if len(normalized_title) <= 4 and not has_book_signal:
        return None
    record = {
        "title": normalized_title,
        "author": author.strip() if isinstance(author, str) else None,
        "category": _pick_first(payload, CATEGORY_KEYS),
        "subcategory": _pick_first(payload, SUBCATEGORY_KEYS),
        "intro": _pick_first(payload, INTRO_KEYS),
        "tags": _normalize_tags(_pick_first(payload, TAG_KEYS)),
        "rank": _pick_first(payload, RANK_KEYS),
        "word_count": _pick_first(payload, WORD_COUNT_KEYS),
        "status": _pick_first(payload, STATUS_KEYS),
        "book_id": _pick_first(payload, ID_KEYS),
    }
    intro = record["intro"]
    if isinstance(intro, str):
        record["intro"] = _strip_html(unescape(intro))
    if isinstance(record["category"], str):
        record["category"] = record["category"].strip()
    if isinstance(record["subcategory"], str):
        record["subcategory"] = record["subcategory"].strip()
    if isinstance(record["status"], str):
        record["status"] = record["status"].strip()
    return record


def _looks_like_noise_title(title: str) -> bool:
    if title in NOISE_TITLES:
        return True
    if title.isdigit():
        return True
    if title in GENERIC_CATEGORY_LABELS:
        return True
    if any(pattern in title for pattern in NOISE_TITLE_PATTERNS):
        return True
    if "," in title or "，" in title:
        return True
    return False


def _walk_for_records(payload: Any, output: list[dict[str, Any]]) -> None:
    if isinstance(payload, dict):
        record = _record_from_dict(payload)
        if record:
            output.append(record)
        for value in payload.values():
            _walk_for_records(value, output)
    elif isinstance(payload, list):
        for item in payload:
            _walk_for_records(item, output)


def extract_embedded_records(document: ParsedDocument) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for script in document.scripts:
        for blob in _iter_json_blobs(script["content"]):
            _walk_for_records(blob, records)
    unique: list[dict[str, Any]] = []
    seen: set[tuple[Any, ...]] = set()
    for record in records:
        key = (
            record.get("title"),
            record.get("author"),
            record.get("category"),
            record.get("rank"),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(record)
    return unique


def extract_anchor_records(document: ParsedDocument) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen_titles: set[str] = set()
    for anchor in document.anchors:
        href = anchor["href"]
        text = anchor["text"]
        if not text or text in NOISE_TITLES:
            continue
        if _looks_like_noise_title(text):
            continue
        if not BOOK_TEXT_RE.fullmatch(text):
            continue
        if not any(hint in href for hint in BOOK_LINK_HINTS):
            continue
        normalized = text.strip()
        if normalized in seen_titles:
            continue
        seen_titles.add(normalized)
        candidates.append({"title": normalized, "author": None, "tags": []})
    return candidates


def parse_table_like_rows(document: ParsedDocument) -> list[dict[str, Any]]:
    text = document.visible_text
    pattern = re.compile(
        r"(?P<title>[\u4e00-\u9fffA-Za-z0-9《》【】·\-\[\]（）()]{2,40})\s+"
        r"(?P<author>[\u4e00-\u9fffA-Za-z0-9·_\-]{2,30})\s+"
        r"(?P<category>原创|衍生|玄幻|奇幻|武侠|仙侠|都市|现实|军事|历史|游戏|体育|科幻|轻小说|爱情|剧情|悬疑)"
    )
    rows: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for match in pattern.finditer(text):
        key = (match.group("title"), match.group("author"), match.group("category"))
        if key in seen:
            continue
        seen.add(key)
        rows.append(
            {
                "title": match.group("title"),
                "author": match.group("author"),
                "category": match.group("category"),
                "tags": [],
            }
        )
    return rows


def extract_records(html: str) -> tuple[ParsedDocument, list[dict[str, Any]]]:
    document = parse_document(html)
    anchor_records = extract_anchor_records(document)
    if sum(1 for anchor in document.anchors if "onebook.php" in anchor["href"]) >= 20 and anchor_records:
        return document, anchor_records

    records = extract_embedded_records(document)
    if not records:
        records = parse_table_like_rows(document)
    if not records:
        records = anchor_records
    return document, records
