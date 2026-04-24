#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from novel_rank_data.feedback import format_feedback_report, load_feedback
from novel_rank_data.storage import ensure_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a feedback summary report from manual publishing rows.")
    parser.add_argument(
        "--input",
        default=str(ROOT / "data" / "feedback" / "works.jsonl"),
        help="Feedback JSONL path",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "reports" / "feedback_report.md"),
        help="Markdown report path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = load_feedback(Path(args.input).expanduser().resolve())
    output_path = Path(args.output).expanduser().resolve()
    ensure_dir(output_path.parent)
    output_path.write_text(format_feedback_report(rows), encoding="utf-8")
    print(f"feedback_report={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
