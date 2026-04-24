#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from novel_rank_data.feedback import append_feedback


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append one manual publishing feedback row.")
    parser.add_argument("--title", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--genre", required=True)
    parser.add_argument("--hook", required=True)
    parser.add_argument("--chapters", type=float, default=0)
    parser.add_argument("--words", type=float, default=0)
    parser.add_argument("--views", type=float, default=0)
    parser.add_argument("--favorites", type=float, default=0)
    parser.add_argument("--comments", type=float, default=0)
    parser.add_argument("--revenue", type=float, default=0)
    parser.add_argument("--notes", default="")
    parser.add_argument(
        "--output",
        default=str(ROOT / "data" / "feedback" / "works.jsonl"),
        help="Feedback JSONL path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    row = append_feedback(
        Path(args.output).expanduser().resolve(),
        {
            "title": args.title,
            "platform": args.platform,
            "genre": args.genre,
            "hook": args.hook,
            "chapters": args.chapters,
            "words": args.words,
            "views": args.views,
            "favorites": args.favorites,
            "comments": args.comments,
            "revenue": args.revenue,
            "notes": args.notes,
        },
    )
    print(f"feedback_recorded={row['title']} favorite_rate={row['favorite_rate']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
