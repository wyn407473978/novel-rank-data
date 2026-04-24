from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from novel_rank_data.feedback import append_feedback, summarize_feedback


class FeedbackTests(unittest.TestCase):
    def test_append_feedback_writes_jsonl_row(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "works.jsonl"

            row = append_feedback(
                path,
                {
                    "title": "开局一间小饭馆",
                    "platform": "fanqie",
                    "genre": "都市",
                    "hook": "经营种田",
                    "views": 1000,
                    "favorites": 80,
                    "comments": 12,
                    "revenue": 35.5,
                },
            )

            saved = json.loads(path.read_text(encoding="utf-8").strip())
            self.assertEqual(saved["title"], "开局一间小饭馆")
            self.assertTrue(saved["created_at"])
            self.assertEqual(row["favorite_rate"], 0.08)

    def test_summarize_feedback_groups_by_platform_genre_and_hook(self) -> None:
        rows = [
            {
                "platform": "fanqie",
                "genre": "都市",
                "hook": "经营种田",
                "views": 1000,
                "favorites": 50,
                "comments": 10,
                "revenue": 20,
            },
            {
                "platform": "fanqie",
                "genre": "都市",
                "hook": "经营种田",
                "views": 500,
                "favorites": 50,
                "comments": 5,
                "revenue": 10,
            },
        ]

        summary = summarize_feedback(rows)

        self.assertEqual(summary[0]["platform"], "fanqie")
        self.assertEqual(summary[0]["views"], 1500)
        self.assertEqual(summary[0]["revenue"], 30)
        self.assertEqual(summary[0]["favorite_rate"], 0.0667)


if __name__ == "__main__":
    unittest.main()
