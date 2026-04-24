# Profit Loop MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a market-to-Hermes-to-feedback MVP for Chinese web novel opportunity selection.

**Architecture:** Add a focused opportunities module for scoring and formatting data, then expose it through small scripts. Keep all generated outputs in `reports/` and feedback rows in `data/feedback/works.jsonl`.

**Tech Stack:** Python 3.11+, stdlib JSON/argparse/dataclasses, pytest.

---

### Task 1: Opportunity Scoring

**Files:**
- Create: `src/novel_rank_data/opportunities.py`
- Test: `tests/test_opportunities.py`

- [ ] Write tests for grouping, heat, growth, and platform fit.
- [ ] Run `python3 -m pytest tests/test_opportunities.py -v` and confirm failures.
- [ ] Implement opportunity scoring.
- [ ] Run the test again and confirm pass.

### Task 2: Reports And Hermes Briefs

**Files:**
- Create: `scripts/build_opportunity_report.py`
- Create: `scripts/export_hermes_brief.py`
- Test: `tests/test_opportunity_reports.py`

- [ ] Write tests for report text and brief text.
- [ ] Run targeted tests and confirm failures.
- [ ] Implement scripts using `novel_rank_data.opportunities`.
- [ ] Run targeted tests and confirm pass.

### Task 3: Feedback Loop

**Files:**
- Create: `src/novel_rank_data/feedback.py`
- Create: `scripts/record_feedback.py`
- Create: `scripts/build_feedback_report.py`
- Test: `tests/test_feedback.py`

- [ ] Write tests for feedback row append and summary metrics.
- [ ] Run tests and confirm failures.
- [ ] Implement feedback module and scripts.
- [ ] Run tests and confirm pass.

### Task 4: Package Commands And Verification

**Files:**
- Modify: `package.json`

- [ ] Add `opportunities`, `hermes`, `feedback:add`, and `feedback:report` scripts.
- [ ] Run `python3 -m pytest -v`.
- [ ] Run opportunity and Hermes scripts against existing data.
