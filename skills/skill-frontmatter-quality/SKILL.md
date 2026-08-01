---
name: skill-frontmatter-quality
description: Review SKILL.md frontmatter for trigger surface, specificity, voice, and completeness. Apply on PRs that add or modify a skills/*/SKILL.md file. Catches descriptions that won't be discoverable, that wave at the topic instead of naming concrete buckets, that drift from the prescriptive house voice, or that omit fields like `review_mode` that downstream tools depend on.
---

# Skill frontmatter quality

A SKILL.md `description:` field is the only thing an agent runtime sees when deciding whether to load the skill. If the description is vague, missing trigger keywords, or wanders off the house voice, the skill won't be discovered and the work that went into the body is wasted.

When reviewing a PR that adds or modifies a `skills/*/SKILL.md`, surface issues from these buckets only:

## Flag these

1. **Missing trigger surface.** The description does not name the situation, file type, or user action that should load the skill. An actionable description leads with the imperative verb ("Flag", "Review", "Use when…") and names the artifact ("PRs that change…", "frontend code with…"). Quote the offending description and propose a rewrite.

2. **Topic-not-trigger.** The description names the *topic* the skill addresses but not the *moment of use*. "Reviews code for performance issues" is topic-only; "Apply to PRs that add database queries, batch jobs, or render-blocking JS" is a trigger.

3. **Restates the name.** The description is a verbose synonym of the directory name. `name: test-discipline` + `description: "Skill for test discipline"` carries no signal an agent can search on. Demand concrete buckets.

4. **Voice drift.** The house voice in this catalog is terse, prescriptive, second-person imperative. Flag deviations: "we recommend", "you should consider", marketing copy ("supercharge your reviews"), exclamation marks, emoji in descriptions, hedging ("might want to", "could be useful").

5. **Frontmatter-body mismatch.** The frontmatter promises one thing (e.g. "flag X, Y, Z") and the body delivers a different list. Quote both. The description is the contract — fix whichever side is wrong.

6. **Missing `review_mode` on a clud-bug-routed skill.** If the skill is intended for clud-bug review (lives in or is being added to `.claude/skills/`, or referenced from `.clud-bug.json`), and its frontmatter has no `review_mode: shared` or `review_mode: dedicated` field, flag it. Default-route ambiguity drops review coverage silently.

## Do not surface

- YAML parse errors, missing required fields, missing H1, name-directory mismatch — the `validate-skills.yml` workflow already covers these mechanically. Defer.
- Description length on its own. A 60-char description with strong trigger surface is fine; a 400-char description that wanders is not. Critique substance, not character count.
- Rewriting wholesale unless the description fails multiple buckets above. A single targeted fix beats a redesign.
- Body content unrelated to what the frontmatter promises. Body-only critiques belong in a different skill.

## How to phrase findings

- Quote the offending `description:` line verbatim before critiquing it.
- Show the rewrite, not just the rule. "Replace `Helps with database stuff` with `Flag PRs that add raw SQL outside the query layer or change index definitions.`"
- One concrete issue per comment. No bundling unrelated frontmatter nits.
