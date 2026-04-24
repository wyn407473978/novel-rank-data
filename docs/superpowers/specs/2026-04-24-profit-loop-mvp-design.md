# Profit Loop MVP Design

## Goal

Build a first useful loop from market ranking data to Hermes-ready writing direction to manual publishing feedback.

## Scope

This MVP adds five capabilities:

- score market opportunities by platform, genre, and hook
- generate a Markdown opportunity report
- export a Hermes writing brief for a selected platform or opportunity
- record manual publishing feedback as JSONL
- summarize feedback by platform and opportunity signals

The MVP does not automate publishing, scrape private author dashboards, or claim true platform revenue data that is not present in the dataset.

## Architecture

`src/novel_rank_data/opportunities.py` owns scoring and report data models. It consumes normalized records from `analysis.py` and optionally compares the latest two capture days when available.

Small scripts in `scripts/` expose the workflow:

- `build_opportunity_report.py` writes `reports/opportunities.md`
- `export_hermes_brief.py` writes `reports/hermes_brief_<platform>.md`
- `record_feedback.py` appends one work-performance row to `data/feedback/works.jsonl`
- `build_feedback_report.py` writes `reports/feedback_report.md`

## Scoring

Each opportunity is grouped by `(platform, genre, hook)`.

- heat: record count in that group
- growth: change from previous capture day when a previous day exists
- saturation risk: repeated title terms and crowded groups reduce confidence
- platform fit: rule-based fit between platform audience and hook family
- actionability: opportunities with a concrete genre and hook score higher

The report must label all scores as directional, not as revenue predictions.

## Hermes Brief

The Hermes brief should contain:

- target platform and reader segment
- selected genre and hook
- market evidence from observed records
- opening strategy
- chapter rhythm
- anti-AI and anti-copycat constraints
- a ready-to-paste prompt

## Feedback

Feedback is manually recorded with fields such as title, platform, genre, hook, chapters, words, views, favorites, comments, revenue, and notes. Reports should compute simple totals and rates without pretending to know unavailable platform internals.

## Testing

Tests cover opportunity scoring, Hermes brief content, feedback append behavior, and feedback summary calculations.
