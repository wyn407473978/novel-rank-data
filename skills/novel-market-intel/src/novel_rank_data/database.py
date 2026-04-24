from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Iterable


SCHEMA = """
CREATE TABLE IF NOT EXISTS fetch_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    capture_day TEXT NOT NULL,
    capture_time TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    platform TEXT NOT NULL,
    platform_display_name TEXT NOT NULL,
    endpoint_name TEXT NOT NULL,
    chart TEXT NOT NULL,
    fetch_method TEXT,
    source_url TEXT,
    final_url TEXT,
    status_code INTEGER,
    record_count INTEGER,
    raw_json_path TEXT NOT NULL,
    raw_html_path TEXT NOT NULL,
    error TEXT,
    UNIQUE(capture_day, capture_time, platform, endpoint_name)
);

CREATE TABLE IF NOT EXISTS ranking_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_hash TEXT NOT NULL UNIQUE,
    capture_day TEXT NOT NULL,
    capture_time TEXT NOT NULL,
    captured_at TEXT NOT NULL,
    platform TEXT NOT NULL,
    platform_display_name TEXT NOT NULL,
    audience TEXT,
    monetization TEXT,
    chart TEXT NOT NULL,
    endpoint_name TEXT NOT NULL,
    source_url TEXT,
    source_file TEXT NOT NULL,
    book_id TEXT,
    title TEXT NOT NULL,
    author TEXT,
    category TEXT,
    subcategory TEXT,
    intro TEXT,
    tags_json TEXT,
    rank_value TEXT,
    word_count TEXT,
    status TEXT,
    genre_inferred TEXT,
    hooks_json TEXT,
    title_terms_json TEXT
);

CREATE INDEX IF NOT EXISTS idx_ranking_records_platform_time
ON ranking_records(platform, captured_at);

CREATE INDEX IF NOT EXISTS idx_ranking_records_title
ON ranking_records(platform, title);
"""


def get_connection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def _hash_record(record: dict[str, object]) -> str:
    base = {
        "captured_at": record["captured_at"],
        "platform": record["platform"],
        "endpoint_name": record["endpoint_name"],
        "title": record["title"],
        "author": record.get("author"),
        "book_id": record.get("book_id"),
        "source_url": record.get("source_url"),
    }
    payload = json.dumps(base, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def replace_fetch_runs(connection: sqlite3.Connection, runs: Iterable[dict[str, object]]) -> None:
    with connection:
        for run in runs:
            connection.execute(
                """
                INSERT INTO fetch_runs (
                    capture_day, capture_time, captured_at, platform, platform_display_name,
                    endpoint_name, chart, fetch_method, source_url, final_url, status_code,
                    record_count, raw_json_path, raw_html_path, error
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(capture_day, capture_time, platform, endpoint_name) DO UPDATE SET
                    captured_at=excluded.captured_at,
                    platform_display_name=excluded.platform_display_name,
                    chart=excluded.chart,
                    fetch_method=excluded.fetch_method,
                    source_url=excluded.source_url,
                    final_url=excluded.final_url,
                    status_code=excluded.status_code,
                    record_count=excluded.record_count,
                    raw_json_path=excluded.raw_json_path,
                    raw_html_path=excluded.raw_html_path,
                    error=excluded.error
                """,
                (
                    run["capture_day"],
                    run["capture_time"],
                    run["captured_at"],
                    run["platform"],
                    run["platform_display_name"],
                    run["endpoint_name"],
                    run["chart"],
                    run.get("fetch_method"),
                    run.get("source_url"),
                    run.get("final_url"),
                    run.get("status_code"),
                    run.get("record_count"),
                    run["raw_json_path"],
                    run["raw_html_path"],
                    run.get("error"),
                ),
            )


def replace_ranking_records(connection: sqlite3.Connection, records: Iterable[dict[str, object]]) -> int:
    count = 0
    with connection:
        for record in records:
            record_hash = _hash_record(record)
            connection.execute(
                """
                INSERT INTO ranking_records (
                    record_hash, capture_day, capture_time, captured_at, platform,
                    platform_display_name, audience, monetization, chart, endpoint_name,
                    source_url, source_file, book_id, title, author, category, subcategory,
                    intro, tags_json, rank_value, word_count, status, genre_inferred,
                    hooks_json, title_terms_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(record_hash) DO UPDATE SET
                    platform_display_name=excluded.platform_display_name,
                    audience=excluded.audience,
                    monetization=excluded.monetization,
                    chart=excluded.chart,
                    source_url=excluded.source_url,
                    source_file=excluded.source_file,
                    book_id=excluded.book_id,
                    category=excluded.category,
                    subcategory=excluded.subcategory,
                    intro=excluded.intro,
                    tags_json=excluded.tags_json,
                    rank_value=excluded.rank_value,
                    word_count=excluded.word_count,
                    status=excluded.status,
                    genre_inferred=excluded.genre_inferred,
                    hooks_json=excluded.hooks_json,
                    title_terms_json=excluded.title_terms_json
                """,
                (
                    record_hash,
                    record["capture_day"],
                    record["capture_time"],
                    record["captured_at"],
                    record["platform"],
                    record["platform_display_name"],
                    record.get("audience"),
                    record.get("monetization"),
                    record["chart"],
                    record["endpoint_name"],
                    record.get("source_url"),
                    record["source_file"],
                    record.get("book_id"),
                    record["title"],
                    record.get("author"),
                    record.get("category"),
                    record.get("subcategory"),
                    record.get("intro"),
                    json.dumps(record.get("tags") or [], ensure_ascii=False),
                    None if record.get("rank") is None else str(record.get("rank")),
                    None if record.get("word_count") is None else str(record.get("word_count")),
                    record.get("status"),
                    record.get("genre_inferred"),
                    json.dumps(record.get("hooks_inferred") or [], ensure_ascii=False),
                    json.dumps(record.get("title_terms") or [], ensure_ascii=False),
                ),
            )
            count += 1
    return count
