#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from novel_rank_data.analysis import enrich_record
from novel_rank_data.database import get_connection, replace_fetch_runs, replace_ranking_records
from novel_rank_data.storage import ensure_dir, read_json


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize raw platform snapshots into JSONL.")
    parser.add_argument("--raw-root", default=str(ROOT / "data" / "raw"), help="Raw snapshot root")
    parser.add_argument(
        "--output",
        default=str(ROOT / "data" / "normalized" / "rankings.jsonl"),
        help="Normalized JSONL file",
    )
    parser.add_argument(
        "--db",
        default=str(ROOT / "data" / "novel_rank_data.sqlite"),
        help="SQLite database path",
    )
    return parser.parse_args()


def iter_raw_json_files(raw_root: Path) -> list[Path]:
    latest_by_key: dict[tuple[str, str, str], Path] = {}
    for path in sorted(path for path in raw_root.rglob("*.json") if path.is_file()):
        parts = path.relative_to(raw_root).parts
        if len(parts) < 4:
            continue
        day, platform, capture_time = parts[0], parts[1], parts[2]
        endpoint_name = path.stem
        key = (day, platform, endpoint_name)
        previous = latest_by_key.get(key)
        if previous is None or capture_time > previous.relative_to(raw_root).parts[2]:
            latest_by_key[key] = path
    return sorted(latest_by_key.values())


def main() -> int:
    args = parse_args()
    raw_root = Path(args.raw_root).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()
    db_path = Path(args.db).expanduser().resolve()
    ensure_dir(output.parent)
    rows: list[str] = []
    db_records: list[dict[str, object]] = []
    fetch_runs: list[dict[str, object]] = []

    for path in iter_raw_json_files(raw_root):
        payload = read_json(path)
        parts = path.relative_to(raw_root).parts
        capture_day, platform_slug, capture_time = parts[0], parts[1], parts[2]
        fetch_runs.append(
            {
                "capture_day": capture_day,
                "capture_time": capture_time,
                "captured_at": payload["captured_at"],
                "platform": payload["platform"],
                "platform_display_name": payload["platform_display_name"],
                "endpoint_name": payload["endpoint"]["name"],
                "chart": payload["endpoint"]["chart"],
                "fetch_method": payload["request"].get("fetch_method"),
                "source_url": payload["endpoint"]["url"],
                "final_url": payload["request"].get("final_url"),
                "status_code": payload["request"].get("status_code"),
                "record_count": payload["page"].get("record_count"),
                "raw_json_path": str(path),
                "raw_html_path": str(path.with_suffix(".html")),
                "error": payload["request"].get("error"),
            }
        )
        base = {
            "platform": payload["platform"],
            "platform_display_name": payload["platform_display_name"],
            "audience": payload["audience"],
            "monetization": payload["monetization"],
            "captured_at": payload["captured_at"],
            "capture_day": capture_day,
            "capture_time": capture_time,
            "chart": payload["endpoint"]["chart"],
            "endpoint_name": payload["endpoint"]["name"],
            "source_url": payload["request"]["final_url"] or payload["endpoint"]["url"],
            "source_file": str(path),
        }
        for record in payload.get("records", []):
            normalized = dict(base)
            normalized.update(
                {
                    "title": record.get("title"),
                    "author": record.get("author"),
                    "category": record.get("category"),
                    "subcategory": record.get("subcategory"),
                    "intro": record.get("intro"),
                    "tags": record.get("tags") or [],
                    "rank": record.get("rank"),
                    "word_count": record.get("word_count"),
                    "status": record.get("status"),
                    "book_id": record.get("book_id"),
                }
            )
            enriched = enrich_record(normalized)
            rows.append(json.dumps(enriched, ensure_ascii=False))
            db_records.append(enriched)

    output.write_text("\n".join(rows) + ("\n" if rows else ""), encoding="utf-8")
    ensure_dir(db_path.parent)
    connection = get_connection(db_path)
    replace_fetch_runs(connection, fetch_runs)
    stored = replace_ranking_records(connection, db_records)
    connection.close()
    print(f"normalized_rows={len(rows)} stored_rows={stored} output={output} db={db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
