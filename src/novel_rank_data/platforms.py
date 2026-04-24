from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Endpoint:
    name: str
    url: str
    chart: str
    notes: str = ""
    preferred_fetch: str = "http"
    wait_for_selector: str | None = None
    post_wait_ms: int = 0


@dataclass(frozen=True)
class Platform:
    slug: str
    display_name: str
    audience: str
    monetization: str
    endpoints: tuple[Endpoint, ...]


PLATFORMS: dict[str, Platform] = {
    "qidian": Platform(
        slug="qidian",
        display_name="起点中文网",
        audience="男频综合",
        monetization="付费订阅",
        endpoints=(
            Endpoint(
                "rank",
                "https://www.qidian.com/rank/",
                "overall_rank",
                "综合人气榜入口",
                preferred_fetch="browser",
                wait_for_selector="a[href*='/book/']",
                post_wait_ms=4000,
            ),
            Endpoint(
                "readindex",
                "https://www.qidian.com/rank/readindex/",
                "read_index",
                "阅读指数榜",
                preferred_fetch="browser",
                wait_for_selector="a[href*='/book/']",
                post_wait_ms=4000,
            ),
        ),
    ),
    "jjwxc": Platform(
        slug="jjwxc",
        display_name="晋江文学城",
        audience="女频/言情/纯爱",
        monetization="付费订阅",
        endpoints=(
            Endpoint("mobile_rank", "https://wap.jjwxc.net/index.php/rank", "mobile_rank", "移动端排行入口"),
            Endpoint("topten", "https://www.jjwxc.net/topten.php?orderstr=22", "topten", "榜单页，适合解析表格"),
        ),
    ),
    "fanqie": Platform(
        slug="fanqie",
        display_name="番茄小说",
        audience="大众免费阅读",
        monetization="免费分成",
        endpoints=(
            Endpoint("home", "https://fanqienovel.com/", "homepage", "官网男频/女频精选与最近更新"),
        ),
    ),
    "qimao": Platform(
        slug="qimao",
        display_name="七猫小说",
        audience="大众免费阅读",
        monetization="免费分成",
        endpoints=(
            Endpoint("home", "https://www.qimao.com/", "homepage", "官网排行榜与最近更新"),
        ),
    ),
    "zongheng": Platform(
        slug="zongheng",
        display_name="纵横中文网",
        audience="男频综合",
        monetization="付费订阅",
        endpoints=(
            Endpoint("rank", "https://book.zongheng.com/rank.html", "rank_page", "榜单页，含多类榜单"),
        ),
    ),
}


def resolve_platforms(selected: list[str] | None) -> list[Platform]:
    if not selected:
        return list(PLATFORMS.values())
    resolved = []
    for slug in selected:
        key = slug.strip().lower()
        if key not in PLATFORMS:
            raise KeyError(f"Unknown platform: {slug}")
        resolved.append(PLATFORMS[key])
    return resolved
