#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import UTC, datetime
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from novel_rank_data.analysis import (
    build_cross_platform_trends,
    build_platform_windows,
    load_normalized_records,
    recommend_directions,
)
from novel_rank_data.storage import ensure_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a markdown market brief from normalized ranking data.")
    parser.add_argument(
        "--input",
        default=str(ROOT / "data" / "normalized" / "rankings.jsonl"),
        help="Normalized JSONL file",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "reports" / "market_brief.md"),
        help="Markdown brief output path",
    )
    return parser.parse_args()


def format_pairs(pairs: list[tuple[str, int]]) -> str:
    if not pairs:
        return "数据不足"
    return "、".join(f"{name}({count})" for name, count in pairs)


def describe_window(label: str, data: dict[str, list[tuple[str, int]]]) -> str:
    return (
        f"- {label}: 题材 {format_pairs(data['genres'])}; "
        f"hooks {format_pairs(data['hooks'])}; "
        f"标题词 {format_pairs(data['terms'])}"
    )


def main() -> int:
    args = parse_args()
    records = load_normalized_records(Path(args.input).expanduser().resolve())
    output_path = Path(args.output).expanduser().resolve()
    ensure_dir(output_path.parent)
    windows = build_platform_windows(records)
    cross = build_cross_platform_trends(records)
    directions = recommend_directions(records)
    checked_date = datetime.now(UTC).strftime("%Y-%m-%d")

    lines = [
        "# Web Novel Market Brief",
        "",
        f"Date checked: {checked_date}",
        f"Records analyzed: {len(records)}",
        "",
        "## Snapshot",
        f"- 跨平台高频题材: {format_pairs(cross['genres'])}",
        f"- 跨平台高频 hooks: {format_pairs(cross['hooks'])}",
        "",
        "## Platform Notes",
    ]

    for platform, slices in windows.items():
        display_name = next(
            (record["platform_display_name"] for record in records if record["platform"] == platform),
            platform,
        )
        lines.extend(
            [
                f"### {display_name} ({platform})",
                describe_window(
                    "Daily",
                    {
                        "genres": slices["daily"].top_genres,
                        "hooks": slices["daily"].top_hooks,
                        "terms": slices["daily"].top_title_terms,
                    },
                ),
                describe_window(
                    "Weekly",
                    {
                        "genres": slices["weekly"].top_genres,
                        "hooks": slices["weekly"].top_hooks,
                        "terms": slices["weekly"].top_title_terms,
                    },
                ),
                describe_window(
                    "Monthly",
                    {
                        "genres": slices["monthly"].top_genres,
                        "hooks": slices["monthly"].top_hooks,
                        "terms": slices["monthly"].top_title_terms,
                    },
                ),
                "",
            ]
        )

    lines.extend(["## Writing Directions For Hermes"])
    if not directions:
        lines.append("- 数据不足，先运行抓取和标准化。")
    else:
        for direction in directions:
            lines.append(
                f"- {direction['platform']}: 主攻 {direction['genre']}，优先结合 {direction['hook']}。"
                f" {direction['warning']}"
            )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"brief={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
