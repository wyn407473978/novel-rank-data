#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from novel_rank_data.analysis import load_normalized_records
from novel_rank_data.opportunities import build_hermes_brief, score_opportunities
from novel_rank_data.storage import ensure_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a Hermes-ready writing brief from scored opportunities.")
    parser.add_argument("--platform", required=True, help="Platform slug such as qidian, jjwxc, fanqie")
    parser.add_argument("--genre", default=None, help="Optional genre lane to force")
    parser.add_argument("--hook", default=None, help="Optional hook to force")
    parser.add_argument(
        "--input",
        default=str(ROOT / "data" / "normalized" / "rankings.jsonl"),
        help="Normalized rankings JSONL path",
    )
    parser.add_argument("--output", default=None, help="Markdown output path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    platform = args.platform.strip().lower()
    records = load_normalized_records(Path(args.input).expanduser().resolve())
    opportunities = [
        item
        for item in score_opportunities(records)
        if item.platform == platform
        and (args.genre is None or item.genre == args.genre)
        and (args.hook is None or item.hook == args.hook)
    ]
    if not opportunities:
        raise SystemExit(f"No opportunity found for platform={platform} genre={args.genre} hook={args.hook}")

    selected = opportunities[0]
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else (ROOT / "reports" / f"hermes_brief_{selected.platform}.md").resolve()
    )
    ensure_dir(output_path.parent)
    output_path.write_text(build_hermes_brief(selected), encoding="utf-8")
    print(f"hermes_brief={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
