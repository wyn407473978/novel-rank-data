from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Opportunity:
    platform: str
    platform_display_name: str
    audience: str
    genre: str
    hook: str
    heat: int
    growth: int
    saturation_risk: int
    platform_fit: int
    actionability: int
    score: int
    sample_titles: list[str]
    top_terms: list[str]
    evidence_days: list[str]


PLATFORM_HOOK_FIT: dict[str, set[str]] = {
    "qidian": {"系统/金手指", "经营种田", "末世生存", "规则怪谈"},
    "zongheng": {"系统/金手指", "逆袭打脸", "规则怪谈"},
    "fanqie": {"先婚后爱", "重生/回档", "逆袭打脸", "经营种田", "末世生存"},
    "qimao": {"先婚后爱", "重生/回档", "逆袭打脸", "经营种田", "末世生存"},
    "jjwxc": {"重生/回档", "高能关系", "先婚后爱", "经营种田"},
}


def _latest_two_days(records: list[dict[str, Any]]) -> tuple[str | None, str | None]:
    days = sorted({str(record.get("capture_day")) for record in records if record.get("capture_day")}, reverse=True)
    current = days[0] if days else None
    previous = days[1] if len(days) > 1 else None
    return current, previous


def _hooks_for(record: dict[str, Any]) -> list[str]:
    hooks = record.get("hooks_inferred") or []
    if isinstance(hooks, list) and hooks:
        return [str(hook) for hook in hooks if hook]
    return ["强冲突开局"]


def _genre_for(record: dict[str, Any]) -> str:
    return str(record.get("genre_inferred") or record.get("category") or "未明题材")


def _platform_fit(platform: str, hook: str) -> int:
    if hook in PLATFORM_HOOK_FIT.get(platform, set()):
        return 2
    if hook == "强冲突开局":
        return 1
    return 0


def _actionability(genre: str, hook: str) -> int:
    score = 0
    if genre != "未明题材":
        score += 1
    if hook != "强冲突开局":
        score += 1
    return score


def score_opportunities(records: list[dict[str, Any]], limit: int | None = None) -> list[Opportunity]:
    current_day, previous_day = _latest_two_days(records)
    if not current_day:
        return []

    current_groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    previous_counts: Counter[tuple[str, str, str]] = Counter()

    for record in records:
        platform = str(record.get("platform") or "")
        if not platform:
            continue
        genre = _genre_for(record)
        for hook in _hooks_for(record):
            key = (platform, genre, hook)
            if record.get("capture_day") == current_day:
                current_groups[key].append(record)
            elif previous_day and record.get("capture_day") == previous_day:
                previous_counts[key] += 1

    opportunities: list[Opportunity] = []
    for (platform, genre, hook), items in current_groups.items():
        term_counter: Counter[str] = Counter()
        sample_titles: list[str] = []
        evidence_days = sorted({str(item.get("capture_day")) for item in items if item.get("capture_day")})
        for item in items:
            title = str(item.get("title") or "").strip()
            if title and title not in sample_titles and len(sample_titles) < 5:
                sample_titles.append(title)
            terms = item.get("title_terms") or []
            if isinstance(terms, list):
                term_counter.update(str(term) for term in terms if term)

        heat = len(items)
        growth = heat - previous_counts[(platform, genre, hook)] if previous_day else 0
        saturation_risk = 0
        if heat >= 12:
            saturation_risk += 2
        elif heat >= 6:
            saturation_risk += 1
        if term_counter and term_counter.most_common(1)[0][1] >= 3:
            saturation_risk += 1

        fit = _platform_fit(platform, hook)
        actionability = _actionability(genre, hook)
        clarity_penalty = 0
        if genre == "未明题材":
            clarity_penalty += 8
        if hook == "强冲突开局":
            clarity_penalty += 4
        score = (
            min(heat, 20) * 3
            + max(growth, 0) * 2
            + fit * 3
            + actionability * 4
            - saturation_risk * 2
            - clarity_penalty
        )
        first = items[0]
        opportunities.append(
            Opportunity(
                platform=platform,
                platform_display_name=str(first.get("platform_display_name") or platform),
                audience=str(first.get("audience") or ""),
                genre=genre,
                hook=hook,
                heat=heat,
                growth=growth,
                saturation_risk=saturation_risk,
                platform_fit=fit,
                actionability=actionability,
                score=score,
                sample_titles=sample_titles,
                top_terms=[term for term, _count in term_counter.most_common(8)],
                evidence_days=evidence_days,
            )
        )

    opportunities.sort(key=lambda item: (item.score, item.heat, item.growth), reverse=True)
    return opportunities[:limit] if limit else opportunities


def format_opportunity_report(opportunities: list[Opportunity]) -> str:
    lines = [
        "# Web Novel Opportunity Report",
        "",
        "说明: 分数是选题方向评分，不是收入预测。真实收益还需要发布后的阅读、收藏、追读和收入反馈校准。",
        "",
    ]
    if not opportunities:
        lines.append("暂无机会数据。请先运行抓取和标准化。")
        return "\n".join(lines) + "\n"

    for index, item in enumerate(opportunities, start=1):
        growth = f"{item.growth:+d}" if item.growth else "0"
        lines.extend(
            [
                f"## {index}. {item.platform_display_name} / {item.genre} / {item.hook}",
                f"- Score: {item.score}",
                f"- Evidence days: {', '.join(item.evidence_days) or 'unknown'}",
                f"- Heat: {item.heat}; Growth: {growth}; Saturation risk: {item.saturation_risk}",
                f"- Platform fit: {item.platform_fit}; Actionability: {item.actionability}",
                f"- Top title terms: {', '.join(item.top_terms) or '数据不足'}",
                f"- Sample titles: {' / '.join(item.sample_titles) or '数据不足'}",
                f"- Writing angle: {_opening_strategy(item)}",
                "",
            ]
        )
    return "\n".join(lines)


def _opening_strategy(opportunity: Opportunity) -> str:
    if opportunity.platform in {"fanqie", "qimao"}:
        return f"前 200 字直接进入压力场景，用{opportunity.hook}制造即时爽点，章节末保留清晰钩子。"
    if opportunity.platform == "jjwxc":
        return f"用关系压力开场，让{opportunity.hook}落到人物选择和情绪拉扯上。"
    return f"先亮出主角目标和能力差异，再把{opportunity.hook}接到可持续升级线。"


def build_hermes_brief(opportunity: Opportunity) -> str:
    sample_titles = "\n".join(f"- {title}" for title in opportunity.sample_titles) or "- 数据不足"
    top_terms = "、".join(opportunity.top_terms) or "数据不足"
    return f"""# Hermes Writing Brief

## Market Target

- Platform: {opportunity.platform_display_name} ({opportunity.platform})
- Reader segment: {opportunity.audience or "未标注"}
- Genre lane: {opportunity.genre}
- Core hook: {opportunity.hook}
- Directional score: {opportunity.score}
- Evidence days: {", ".join(opportunity.evidence_days) or "unknown"}

## Observed Evidence

Sample titles:
{sample_titles}

Top title terms: {top_terms}

## Writing Strategy

- Opening: {_opening_strategy(opportunity)}
- Chapter rhythm: 每章只推进一个明确冲突，结尾留下新信息差、危险或关系反转。
- Reader promise: 复用题材和 hook 的读者承诺，不要复制具体书名、角色、设定或桥段。
- Risk control: 不要复制榜单作品；不要把市场词硬塞进标题；不要用大段世界观说明开头。

## Ready Prompt

Write only one Chinese web novel opening scene for Hermes.

Target platform: {opportunity.platform_display_name}
Target readers: {opportunity.audience or "platform-native web novel readers"}
Genre: {opportunity.genre}
Core hook: {opportunity.hook}
Market signals to absorb: {top_terms}

Scene constraints:
- 前 200 字必须进入压力场景
- 解释比例控制在 15% 以内
- 对白承担冲突、信息差或情绪变化，不承担主题总结
- 每个主要角色要有不同的说话习惯
- 至少加入一个像真实观察得来的社会细节或职业细节
- 不要复制任何已存在小说的书名、人物、设定或桥段
- 输出 only 正文，不要解释创作思路
"""
