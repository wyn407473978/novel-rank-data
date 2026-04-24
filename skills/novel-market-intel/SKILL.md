---
name: novel-market-intel
description: Research hot novel trends across Chinese fiction platforms and turn daily, weekly, and monthly ranking signals into actionable market briefs for writing strategy. Use when Hermes Agent needs up-to-date platform heat analysis, genre trend tracking, ranking comparison, trope extraction, or publication-direction recommendations for web novels.
---

# Novel Market Intel

Use this skill when the task is to understand what is hot on Chinese web novel platforms and convert that into writing guidance.

This skill is for market sensing, not prose generation. If the task is to write or rewrite fiction with less AI flavor, use `novel-de-ai-writing` after this skill.

## What To Produce

Produce a market brief with:

- data date stamps for every source checked
- platform-by-platform hot genres and tags
- daily, weekly, and monthly differences
- repeated hook patterns, protagonist types, and opening styles
- saturation risk and whitespace opportunities
- a short writing recommendation Hermes can pass into drafting

## Core Workflow

1. Identify the target platforms.
Default to the mainstream set in [references/platforms.md](references/platforms.md) unless the user narrows the scope.

2. Fetch current ranking signals.
Prefer the bundled script pipeline that ships inside this skill:

```bash
python3 scripts/fetch_rankings.py --platforms qidian jjwxc fanqie qimao zongheng
python3 scripts/normalize_rankings.py
python3 scripts/build_market_brief.py
python3 scripts/build_delta_report.py
```

Run those commands from the skill directory, or use absolute paths inside the installed skill folder such as `~/.hermes/skills/novel-market-intel/scripts/fetch_rankings.py`.

If `scripts/` or `src/` is missing from the installed skill, stop and report that the skill installation is incomplete.
Do not fall back to multi-agent manual browsing by default, because that path is much less reliable and tends to hit anti-bot walls and context overflows.

If the bundled scripts exist but fail:
- first report the exact failing command and error
- then try a narrower scripted run such as a smaller platform subset
- only browse official pages manually if the user explicitly wants a manual fallback

3. Capture signals for three time windows.
- Daily: what is spiking right now
- Weekly: what is sustaining attention
- Monthly: what appears durable enough to influence commissioning and imitation

4. Normalize the signals.
Map every observed work into a normalized schema:
- platform
- capture date
- chart window
- apparent genre
- subgenre
- target audience
- protagonist archetype
- core hook
- update rhythm if visible
- monetization model if obvious: paid, free, ad-driven, mixed

5. Extract market patterns.
Use [references/analysis-framework.md](references/analysis-framework.md) to turn title blurbs, tags, intros, comments, and chart positions into:
- hook families
- pacing norms
- emotional promise
- trope bundles
- taboo or fatigue signals

6. Write the strategy layer.
End with concrete guidance:
- what to imitate
- what to avoid
- what to hybridize
- what kind of opening is most viable on each platform

## Ranking Evidence Rules

- Never invent chart positions, metrics, or titles.
- Always attach explicit dates such as `2026-04-18`.
- If the platform only exposes a current chart and not historical windows, state that limitation and infer cautiously from repeated category presence or editor exposure.
- Distinguish:
  - `Observed`: directly visible on the source page
  - `Inferred`: concluded from repeated patterns across visible works
  - `Hypothesis`: useful but weakly evidenced market guess

## Minimum Viable Output

When time is limited, cover at least:

- `起点中文网`
- `晋江文学城`
- `番茄小说`
- `七猫小说`
- `纵横中文网`

Then optionally extend to `17K`, `飞卢`, `书旗`, `掌阅`, `红袖添香`, `潇湘书院`, `盐言故事`.

## Output Template

Use this structure:

```markdown
# Web Novel Market Brief

Date checked: 2026-04-18
Platforms: 起点 / 晋江 / 番茄 / 七猫 / 纵横

## Snapshot
- One paragraph on what is hot overall

## Platform Notes
### 起点中文网
- Daily:
- Weekly:
- Monthly:
- Dominant hooks:
- Reader promise:
- Saturation risk:
- Opportunity:

### 晋江文学城
...

## Cross-Platform Trends
- Trend 1
- Trend 2
- Trend 3

## Writing Directions For Hermes
- Direction A
- Direction B
- Direction C
```

## When To Read References

- Read [references/platforms.md](references/platforms.md) when you need platform coverage, audience assumptions, or source priority.
- Read [references/analysis-framework.md](references/analysis-framework.md) when you need a repeatable method for translating chart data into writing decisions.

## Script Outputs

When using the bundled scripts:

- raw HTML and parsed snapshots land in `data/raw/YYYY-MM-DD/<platform>/<capture_time>/`
- normalized rows land in `data/normalized/rankings.jsonl`
- persistent history lands in `data/novel_rank_data.sqlite`
- market brief lands in `reports/market_brief.md`
- day-over-day delta report lands in `reports/market_delta.md`
- Hermes-ready prompt inputs can be exported with:

```bash
python3 scripts/export_prompt_inputs.py --platform qidian
```

## Runtime Notes

- `scripts/` and `src/novel_rank_data/` are part of the skill and should be installed together.
- `起点中文网` works best when local browser automation is available.
- Browser automation is optional. If `node` or `playwright-core` is unavailable, the scripts still run and will collect the other supported platforms through plain HTTP.
- If a platform returns anti-bot pages or empty results, include that limitation in the brief instead of inventing missing data.

## Handoff To Writing

If the next step is fiction generation, pass forward:

- chosen platform
- target reader segment
- 3 to 5 hot trope signals
- 2 anti-cliche warnings
- preferred opening style
- monetization logic and likely chapter rhythm

Then switch to `novel-de-ai-writing`.
