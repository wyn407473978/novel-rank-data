#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from novel_rank_data.storage import ensure_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a delta report between the latest two capture days.")
    parser.add_argument(
        "--db",
        default=str(ROOT / "data" / "novel_rank_data.sqlite"),
        help="SQLite database path",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "reports" / "market_delta.md"),
        help="Markdown delta report path",
    )
    return parser.parse_args()


def fetch_capture_days(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute(
        "SELECT DISTINCT capture_day FROM ranking_records ORDER BY capture_day DESC LIMIT 2"
    ).fetchall()
    return [row[0] for row in rows]


def load_counts(connection: sqlite3.Connection, capture_day: str, column: str) -> dict[tuple[str, str], int]:
    rows = connection.execute(
        f"""
        SELECT platform, {column}, COUNT(*) AS count
        FROM ranking_records
        WHERE capture_day = ? AND {column} IS NOT NULL AND {column} != ''
        GROUP BY platform, {column}
        """,
        (capture_day,),
    ).fetchall()
    return {(row[0], row[1]): row[2] for row in rows}


def load_hook_counts(connection: sqlite3.Connection, capture_day: str) -> dict[tuple[str, str], int]:
    rows = connection.execute(
        """
        SELECT platform, hooks_json
        FROM ranking_records
        WHERE capture_day = ? AND hooks_json IS NOT NULL AND hooks_json != '[]'
        """,
        (capture_day,),
    ).fetchall()
    counts: dict[tuple[str, str], int] = {}
    for platform, hooks_json in rows:
        for hook in json.loads(hooks_json):
            key = (platform, hook)
            counts[key] = counts.get(key, 0) + 1
    return counts


def top_deltas(current: dict[tuple[str, str], int], previous: dict[tuple[str, str], int], platform: str) -> list[str]:
    entries = []
    labels = {key[1] for key in current if key[0] == platform} | {key[1] for key in previous if key[0] == platform}
    for label in labels:
        now = current.get((platform, label), 0)
        old = previous.get((platform, label), 0)
        delta = now - old
        if delta:
            entries.append((delta, label, now, old))
    entries.sort(reverse=True)
    return [f"{label}: {old} -> {now} ({delta:+d})" for delta, label, now, old in entries[:5]]


def main() -> int:
    args = parse_args()
    db_path = Path(args.db).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    ensure_dir(output_path.parent)

    connection = sqlite3.connect(db_path)
    days = fetch_capture_days(connection)
    if len(days) < 2:
        output_path.write_text(
            "# Market Delta Report\n\n需要至少两个不同抓取日期的数据后才能生成变化报告。\n",
            encoding="utf-8",
        )
        print(f"delta={output_path}")
        return 0

    current_day, previous_day = days[0], days[1]
    genre_current = load_counts(connection, current_day, "genre_inferred")
    genre_previous = load_counts(connection, previous_day, "genre_inferred")
    hook_current = load_hook_counts(connection, current_day)
    hook_previous = load_hook_counts(connection, previous_day)
    platforms = sorted({platform for platform, _ in genre_current.keys()} | {platform for platform, _ in genre_previous.keys()})

    lines = [
        "# Market Delta Report",
        "",
        f"Current day: {current_day}",
        f"Previous day: {previous_day}",
        "",
    ]
    for platform in platforms:
        lines.append(f"## {platform}")
        genre_lines = top_deltas(genre_current, genre_previous, platform)
        hook_lines = top_deltas(hook_current, hook_previous, platform)
        lines.append("### Genre Shifts")
        lines.extend([f"- {line}" for line in genre_lines] or ["- 暂无显著变化。"])
        lines.append("### Hook Shifts")
        lines.extend([f"- {line}" for line in hook_lines] or ["- 暂无显著变化。"])
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"delta={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
