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

from novel_rank_data.analysis import build_platform_windows, load_normalized_records, recommend_directions
from novel_rank_data.platforms import PLATFORMS
from novel_rank_data.storage import ensure_dir


ANTI_AI_WARNINGS = [
    "不要用开头大段世界观说明。",
    "不要让所有角色说话都过于工整。",
    "不要在段尾重复总结读者已经看懂的情绪。",
    "避免空泛形容词，优先用动作、职业细节、社会细节。",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a structured prompt input pack for Hermes.")
    parser.add_argument("--platform", required=True, help="Platform slug, such as qidian or jjwxc")
    parser.add_argument(
        "--input",
        default=str(ROOT / "data" / "normalized" / "rankings.jsonl"),
        help="Normalized JSONL file",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="JSON output file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    platform_slug = args.platform.strip().lower()
    if platform_slug not in PLATFORMS:
        raise SystemExit(f"Unknown platform: {platform_slug}")

    records = load_normalized_records(Path(args.input).expanduser().resolve())
    windows = build_platform_windows(records)
    directions = recommend_directions(records)
    platform_windows = windows.get(platform_slug, {})
    platform_meta = PLATFORMS[platform_slug]

    market_signals = []
    for label in ("daily", "weekly", "monthly"):
        market_slice = platform_windows.get(label)
        if not market_slice:
            continue
        market_signals.append(
            {
                "window": label,
                "top_genres": [name for name, _count in market_slice.top_genres[:3]],
                "top_hooks": [name for name, _count in market_slice.top_hooks[:4]],
                "top_title_terms": [name for name, _count in market_slice.top_title_terms[:6]],
            }
        )

    payload = {
        "platform": platform_slug,
        "platform_display_name": platform_meta.display_name,
        "audience": platform_meta.audience,
        "monetization": platform_meta.monetization,
        "market_signals": market_signals,
        "recommended_direction": next(
            (item for item in directions if item["platform"] == platform_slug),
            None,
        ),
        "anti_ai_warnings": ANTI_AI_WARNINGS,
        "prompt_scaffold": {
            "scene_goal": ["主角想得到什么", "障碍是什么", "情绪矛盾是什么", "结尾钩子是什么"],
            "style_constraints": [
                "前200字必须进入压力场景",
                "解释比例控制在15%以内",
                "对白承担冲突，不承担主题总结",
                "每场景至少有一个带观察感的具体细节",
            ],
        },
    }

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else (ROOT / "reports" / f"prompt_inputs_{platform_slug}.json").resolve()
    )
    ensure_dir(output_path.parent)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"prompt_inputs={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
