from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse

from novel_rank_data.parsers import (
    NOISE_TITLES,
    extract_anchor_records,
    extract_embedded_records,
    extract_records,
    parse_document,
)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value)).strip()


def _clean_jjwxc_title(value: str) -> str:
    cleaned = value
    if 'class="tooltip">' in cleaned:
        cleaned = cleaned.split('class="tooltip">')[-1]
    if ">" in cleaned and len(cleaned) > 60:
        cleaned = cleaned.split(">")[-1]
    return _clean_text(cleaned)


def _dedupe_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    output = []
    seen: set[tuple[object, ...]] = set()
    for record in records:
        title = record.get("title")
        if not isinstance(title, str) or not title.strip():
            continue
        key = (
            title.strip(),
            record.get("author"),
            record.get("book_id"),
            record.get("category"),
        )
        if key in seen:
            continue
        seen.add(key)
        output.append(record)
    return output


def extract_records_for_platform(
    platform_slug: str,
    html: str,
    endpoint_name: str | None = None,
) -> tuple[object, list[dict[str, object]], str]:
    document = parse_document(html)

    if platform_slug == "fanqie":
        records = extract_fanqie_records(document)
        if records:
            return document, records, "fanqie_embedded"

    if platform_slug == "qidian":
        records = extract_qidian_records(html)
        if records:
            return document, records, "qidian_rank_blocks"

    if platform_slug == "qimao":
        records = extract_qimao_records(html)
        if records:
            return document, records, "qimao_html_blocks"

    if platform_slug == "zongheng":
        records = extract_zongheng_records(html)
        if records:
            return document, records, "zongheng_rank_blocks"

    if platform_slug == "jjwxc":
        records = extract_jjwxc_records(html, endpoint_name=endpoint_name)
        if records:
            return document, records, "jjwxc_links"

    generic_document, generic_records = extract_records(html)
    return generic_document, generic_records, "generic"


def extract_fanqie_records(document: object) -> list[dict[str, object]]:
    records = []
    for record in extract_embedded_records(document):
        if not record.get("book_id") or not record.get("author"):
            continue
        if not record.get("category"):
            continue
        records.append(record)
    return _dedupe_records(records)


def extract_qidian_records(html: str) -> list[dict[str, object]]:
    detail_pattern = re.compile(
        r'<div class="book-img-box">.*?href="//www\.qidian\.com/book/(?P<book_id>\d+)/"[^>]*>.*?</div>'
        r'<div class="book-mid-info"><h2><a [^>]*>(?P<title>.*?)</a></h2>'
        r'<p class="author">.*?<a class="name" [^>]*>(?P<author>.*?)</a>'
        r'(?:.*?<a [^>]*data-eid="qd_C42"[^>]*>(?P<category>.*?)</a>)?'
        r'(?:.*?<a class="go-sub-type" [^>]*>(?P<subcategory>.*?)</a>)?'
        r'(?:.*?<span>(?P<status>连载|完本)</span>)?'
        r'(?:.*?<p class="intro">\s*(?P<intro>.*?)\s*</p>)?',
        re.S,
    )
    summary_pattern = re.compile(
        r'<li data-rid="(?P<rank>\d+)"><div class="num-box">.*?</div><div class="name-box">\s*'
        r'<a class="name" title="[^"]+" href="//www\.qidian\.com/book/(?P<book_id>\d+)/"[^>]*><h2>(?P<title>[^<]+)</h2></a>\s*'
        r'<i class="total">(?P<metric>[^<]*)</i>',
        re.S,
    )
    records = []
    for match in detail_pattern.finditer(html):
        records.append(
            {
                "book_id": match.group("book_id"),
                "title": _clean_text(match.group("title")),
                "author": _clean_text(match.group("author")),
                "category": _clean_text(match.group("category") or "") or None,
                "subcategory": _clean_text(match.group("subcategory") or "") or None,
                "status": _clean_text(match.group("status") or "") or None,
                "intro": _clean_text(match.group("intro") or "") or None,
                "tags": [],
            }
        )
    detailed_ids = {record["book_id"] for record in records if record.get("book_id")}
    for match in summary_pattern.finditer(html):
        if match.group("book_id") in detailed_ids:
            continue
        records.append(
            {
                "book_id": match.group("book_id"),
                "title": _clean_text(match.group("title")),
                "author": None,
                "rank": int(match.group("rank")),
                "tags": [_clean_text(match.group("metric"))],
            }
        )
    return _dedupe_records(records)


def extract_qimao_records(html: str) -> list[dict[str, object]]:
    pattern = re.compile(
        r'<a href="https://www\.qimao\.com/shuku/(?P<book_id>\d+)/"[^>]*class="s-title"[^>]*>\s*(?P<title>.*?)\s*</a>'
        r'.*?<a href="https://www\.qimao\.com/zuozhe/[^"]+"[^>]*class="s-author"[^>]*>\s*(?P<author>.*?)\s*</a>'
        r'(?:.*?<a href="https://www\.qimao\.com/shuku/[^"]+"[^>]*class="s-category"[^>]*>\s*(?P<category>.*?)\s*</a>)?',
        re.S,
    )
    records = []
    for match in pattern.finditer(html):
        title = _clean_text(match.group("title"))
        author = _clean_text(match.group("author"))
        category = _clean_text(match.group("category") or "")
        if title in NOISE_TITLES or title == "作者":
            continue
        records.append(
            {
                "book_id": match.group("book_id"),
                "title": title,
                "author": author or None,
                "category": category or None,
                "tags": [],
            }
        )
    return _dedupe_records(records)


def extract_zongheng_records(html: str) -> list[dict[str, object]]:
    records = []
    start = html.find('<div class="rank_main">')
    end = html.find('<div class="footer">')
    scope = html[start:end] if start != -1 and end != -1 and end > start else html
    item_pattern = re.compile(
        r'<div class="rank_i_num fl">\s*(?P<rank>\d+)\s*</div>\s*<div class="rank_i_bname fl">\s*'
        r'<a href="https://book\.zongheng\.com/book/(?P<book_id>\d+)\.html"[^>]*>(?P<title>.*?)</a>'
        r'(?:\s*<a [^>]*class="rank_i_l_a_author"[^>]*>(?P<author>.*?)</a>)?'
        r'(?:\s*<a [^>]*class="rank_i_l_a_category"[^>]*>\[(?P<category>.*?)\]</a>)?',
        re.S,
    )
    current_chart = None
    chart_pattern = re.compile(r'<div class="rank_i_p_tit">(.*?)</div>', re.S)
    for chunk in re.split(r'(<div class="rank_i_p_tit">.*?</div>)', scope):
        chart_match = chart_pattern.search(chunk)
        if chart_match:
            current_chart = _clean_text(chart_match.group(1))
            continue
        for match in item_pattern.finditer(chunk):
            title = _clean_text(match.group("title"))
            if title in NOISE_TITLES:
                continue
            records.append(
                {
                    "book_id": match.group("book_id"),
                    "title": title,
                    "author": _clean_text(match.group("author") or "") or None,
                    "category": _clean_text(match.group("category") or "") or None,
                    "rank": int(match.group("rank")),
                    "tags": [current_chart] if current_chart else [],
                }
            )
    return _dedupe_records(records)


def extract_jjwxc_records(html: str, endpoint_name: str | None = None) -> list[dict[str, object]]:
    if endpoint_name == "mobile_rank":
        return []

    pattern = re.compile(
        r'onebook\.php\?novelid=(?P<book_id>\d+)[^>]*>(?P<title>.*?)</a>'
        r'(?:(?:(?!onebook\.php\?novelid=).){0,500}?oneauthor\.php\?authorid=\d+[^>]*>(?P<author>.*?)</a>)?',
        re.S,
    )
    records = []
    for match in pattern.finditer(html):
        title = _clean_jjwxc_title(match.group("title"))
        if title in NOISE_TITLES or len(title) < 2:
            continue
        if title in {"作品库", "VIP作品", "完结作品", "驻站作品", "经典文库", "免费文库"}:
            continue
        if len(title) > 60:
            continue
        author = _clean_text(match.group("author") or "") or None
        records.append(
            {
                "book_id": match.group("book_id"),
                "title": title,
                "author": author,
                "tags": [],
            }
        )
    return _dedupe_records(records)
