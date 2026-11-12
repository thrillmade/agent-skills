---
version: "1.0.1"
digest: "ce439283491f"  # is your copy current? github.com/thrillmade/thrill-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/thrill-skills"
name: conventions-template
description: Template for a "review like me" skill - captures one maintainer's review conventions (formatting, what to flag, what to ignore). Copy + customize, setting applies_to.author to your GitHub login.
kind: rule
applies_to:
  author: _REPLACE_ME_
---

# Conventions: <YOUR NAME>

This skill captures how I review pull requests when they're opened by
me. The bot loads this skill ONLY on my PRs (the `applies_to.author`
filter above matches the PR author's GitHub login, ignoring case). Other PRs
go through the org defaults without my personal preferences applied.

## How to use this template

1. **Rename the directory**: `.claude/skills/conventions-<your-gh-login>/SKILL.md`
2. **Set `applies_to.author`** to your GitHub login (replace `_REPLACE_ME_`).
   The placeholder matches no GitHub login on purpose — if you forget
   this step, the skill never loads.
3. **Fill in the sections below** with YOUR actual preferences
4. **Commit + push** — the bot picks up the skill on its next review of your PR

The bot still applies the org-wide review-discipline skills
(`critical-issues-only`, `evidence-based-review`, etc.) on top — your
conventions skill LAYERS on, not replaces.

## What I always flag

Replace this section with what YOU want the bot to flag on YOUR PRs.
Examples:

- Functions over ~50 lines — split or justify
- Missing error handling on async/await
- New dependencies without a one-line "why" in the PR description
- Magic numbers without a named constant
- `any` type in TypeScript (use `unknown` + narrow)

## What I always ignore

What the bot should NOT flag on your PRs (overrides any default
behavior that bothers you). Examples:

- Formatting nits — Prettier handles those
- JSDoc requirements — I don't use JSDoc, don't ask for it
- Test coverage on trivial internal helpers
- "Consider using a more functional approach" suggestions

## Structural preferences

Higher-level patterns the bot should respect. Examples:

- Prefer pure functions over class hierarchies
- Co-locate tests with source (NOT `__tests__/` dirs)
- One concept per file; files <300 LOC
- Comments explain WHY, not WHAT (skip comments that restate the code)

## How I want findings formatted

Structural rules for how the bot composes findings on your PRs.
(Tone — the prose register the bot uses when writing — belongs in
a separate `voice-<your-gh-login>` skill, not here.) Examples:

- Always cite the specific line + quote the offending snippet
- Always include a concrete suggested fix, not just "consider X"
- Never bundle multiple unrelated issues into one finding
- One finding per file region; merge near-identical findings
