---
name: novel-de-ai-writing
description: Write Chinese web fiction with lower AI flavor by adapting prompt strategy to platform norms, reader expectations, and scene-level storytelling. Use when Hermes Agent needs platform-specific novel prompts, anti-cliche prose guidance, revision passes to reduce AI voice, or fiction generation that sounds more like a human commercial web novelist.
---

# Novel De-AI Writing

Use this skill when the task is to draft or revise fiction so it reads less like generic AI output and more like a platform-native web novel.

This skill is not about hiding model use. It is about changing process so the prose has stronger intent, scene pressure, and human-like variation.

## Inputs You Should Prefer

Before drafting, collect:

- target platform
- target reader segment
- commercial goal: paid-serial, free-traffic, short-premise, long-arc
- 3 to 5 current hot trope signals from `novel-market-intel`
- protagonist profile
- relationship map if relevant
- first-20-chapter promise

If market input is missing, ask for it or make a conservative assumption and state it.

If the repo contains `scripts/export_prompt_inputs.py`, prefer generating a structured input pack first:

```bash
python3 scripts/export_prompt_inputs.py --platform qidian
```

Then read the exported JSON and use it as the draft constraint pack.

## Why AI Flavor Appears

The most common causes are:

- every paragraph explains instead of dramatizes
- dialogue is too uniformly polished
- scenes end in mini-summaries
- metaphors are generic and evenly distributed
- character emotion is stated before behavior proves it
- openings start broad instead of with pressure
- all sentences are medium length and rhythmically flat

## Practical Style Standard

Treat "less AI flavor" as:

- chapter-level plotting can be ambitious, but sentence-level writing should stay mass-readable
- prose should feel like a skilled commercial web novelist, not a school essay and not a deliberately "bad" draft
- default to colloquial written Chinese, short-to-medium sentences, and dialogue that usually stands in its own paragraph
- use plain, vivid wording instead of decorative adjectives and floating atmosphere
- obey provided hard constraints, facts, kinship terms, and voice rules; do not invent new setting rules just to sound clever

Do not confuse low AI flavor with:

- intentionally lowering grammar quality
- mechanically imitating a "bottom-of-society" stereotype
- stuffing vulgarity or internet slang into every scene
- banning all figurative language regardless of usefulness

## Core Drafting Workflow

1. Lock the platform lane.
Use [references/platform-prompting.md](references/platform-prompting.md) to choose the right commercial style.

2. Draft in scene goals, not chapter summaries.
Every scene should have:
- immediate objective
- friction
- reversal or escalation
- residue for the next scene

3. Force specificity.
Prefer concrete sensory detail, social detail, or power-detail over abstract mood language.

4. Hold back explanation.
Do not explain the theme, relationship, or world rule before the reader has seen it generate consequence.

5. Revise for voice asymmetry.
Different characters should not speak with the same sentence length, politeness, or emotional clarity.

6. Run the anti-AI pass.
Use [references/anti-ai-checklist.md](references/anti-ai-checklist.md) after each chapter or opening sample.

7. Keep execution constraints visible.
Unless the user asked otherwise:
- output only novel正文, not explanation or summary
- do not repeat the provided chapter title
- when there is an obvious scene break, separate with exactly three blank lines
- keep dialogue purposeful: it must reveal conflict, information asymmetry, emotion, or decision pressure

## Platform Strategy

Do not use one generic prompt for all platforms.

- For `起点 / 纵横 / 17K`:
  favor premise clarity, progression, capability display, and sustainable arc momentum
- For `番茄 / 七猫 / 书旗`:
  favor immediate hook, low-friction readability, rapid payoff, and cliff cadence
- For `晋江 / 红袖 / 潇湘`:
  favor emotional voltage, relational subtext, viewpoint intimacy, and scene chemistry
- For `飞卢`:
  favor aggressive premise expression, high hook density, and compressed escalation, but avoid pure imitation

## Prompt Design Rules

- Ask for scenes, not essays.
- Ask the model to omit moralizing and end-of-scene summaries.
- Require character-specific diction differences.
- Require at least one awkward, indirect, or interrupted line in dialogue when appropriate.
- Tell the model what to avoid, not only what to include.
- Ask for one or two surprising but plausible details per scene.
- Prefer plainspoken mass readability over polished literary correctness.
- Tell the model to reduce ornamental similes and atmosphere-only description.
- Allow colloquial emphasis or mild profanity only when it fits character, platform, and scene pressure.
- Tell the model not to force memes or hot slang unless the viewpoint character would naturally say them.
- For non-cyberpunk lanes, explicitly avoid cold-tech jargon, faux-cyber diction, and "edgy" sci-fi decoration.

## Safer Prompt Skeleton

```text
You are writing a commercially viable Chinese web novel chapter for [platform].

Target readers: [reader segment]
Genre lane: [genre + subgenre]
Current market signals to absorb: [3-5 signals]
Do not copy any existing book, but inherit the market's pacing and reader promise.

Write only one chapter-opening scene of 1200-1800 Chinese characters.

Scene objective:
- protagonist wants:
- obstacle:
- emotional contradiction:
- end beat:

Style constraints:
- begin with pressure, not summary
- keep exposition under 15%
- dialogue must carry conflict, not explain theme
- each speaking character needs distinct diction
- avoid empty intensifiers, symmetrical paragraphs, and essay-like reflection
- add 1 concrete social or physical detail that feels observed rather than generated
- prefer short-to-medium sentences and clean paragraph rhythm
- avoid overusing similes, ornate adjectives, and atmosphere-only description
- keep the language colloquial and readable, not showy
- do not invent facts outside the provided setup
- output only the scene text

After writing, silently revise once to remove AI-flavored wording, repeated sentence patterns, and generic emotional labels.
Output only the final scene.
```

## When To Read References

- Read [references/platform-prompting.md](references/platform-prompting.md) for platform-specific prompting and examples.
- Read [references/anti-ai-checklist.md](references/anti-ai-checklist.md) for revision rules that reduce AI flavor.

## Revision Standard

The chapter is not ready if:

- the first 200 characters do not contain pressure
- the reader can delete 20% of explanation without losing meaning
- multiple characters sound equally articulate
- the prose sounds uniformly "correct" but emotionally unmessy
- the scene could belong to any platform without change
