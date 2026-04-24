from __future__ import annotations

import unittest

from novel_rank_data.opportunities import (
    Opportunity,
    build_hermes_brief,
    score_opportunities,
)


class OpportunityTests(unittest.TestCase):
    def test_score_opportunities_groups_by_platform_genre_and_hook(self) -> None:
        records = [
            {
                "platform": "fanqie",
                "platform_display_name": "番茄小说",
                "audience": "大众免费阅读",
                "capture_day": "2026-04-24",
                "title": "重生后我开店暴富",
                "genre_inferred": "都市",
                "hooks_inferred": ["重生/回档", "经营种田"],
                "title_terms": ["重生后", "开店暴富"],
            },
            {
                "platform": "fanqie",
                "platform_display_name": "番茄小说",
                "audience": "大众免费阅读",
                "capture_day": "2026-04-24",
                "title": "重回八零开饭馆",
                "genre_inferred": "都市",
                "hooks_inferred": ["重生/回档", "经营种田"],
                "title_terms": ["重回八零", "开饭馆"],
            },
            {
                "platform": "fanqie",
                "platform_display_name": "番茄小说",
                "audience": "大众免费阅读",
                "capture_day": "2026-04-23",
                "title": "旧日都市",
                "genre_inferred": "都市",
                "hooks_inferred": ["重生/回档"],
                "title_terms": ["旧日都市"],
            },
        ]

        opportunities = score_opportunities(records)

        top = next(item for item in opportunities if item.hook == "重生/回档")
        self.assertEqual(top.platform, "fanqie")
        self.assertEqual(top.genre, "都市")
        self.assertEqual(top.hook, "重生/回档")
        self.assertEqual(top.heat, 2)
        self.assertEqual(top.growth, 1)
        self.assertGreaterEqual(top.platform_fit, 1)
        self.assertGreater(top.score, 0)

    def test_build_hermes_brief_contains_market_evidence_and_prompt(self) -> None:
        opportunity = Opportunity(
            platform="qidian",
            platform_display_name="起点中文网",
            audience="男频综合",
            genre="玄幻",
            hook="系统/金手指",
            heat=8,
            growth=2,
            saturation_risk=1,
            platform_fit=2,
            actionability=2,
            score=29,
            sample_titles=["我有一个修炼面板", "苟在宗门刷词条"],
            top_terms=["面板", "宗门"],
            evidence_days=["2026-04-24"],
        )

        brief = build_hermes_brief(opportunity)

        self.assertIn("起点中文网", brief)
        self.assertIn("玄幻", brief)
        self.assertIn("系统/金手指", brief)
        self.assertIn("我有一个修炼面板", brief)
        self.assertIn("Write only", brief)
        self.assertIn("不要复制", brief)


if __name__ == "__main__":
    unittest.main()
