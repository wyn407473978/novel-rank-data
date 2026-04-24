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
from novel_rank_data.opportunities import format_opportunity_report, score_opportunities
from novel_rank_data.storage import ensure_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a ranked web novel opportunity report.")
    parser.add_argument(
        "--input",
        default=str(ROOT / "data" / "normalized" / "rankings.jsonl"),
        help="Normalized rankings JSONL path",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "reports" / "opportunities.md"),
        help="Markdown output path",
    )
    parser.add_argument("--limit", type=int, default=20, help="Maximum opportunities to include")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    records = load_normalized_records(Path(args.input).expanduser().resolve())
    opportunities = score_opportunities(records, limit=args.limit)
    output_path = Path(args.output).expanduser().resolve()
    ensure_dir(output_path.parent)
    output_path.write_text(format_opportunity_report(opportunities), encoding="utf-8")
    print(f"opportunities={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
