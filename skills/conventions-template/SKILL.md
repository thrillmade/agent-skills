---
name: conventions-template
description: Template for a "review like me" skill - captures one maintainer's review conventions (formatting, what to flag, what to ignore). Copy + customize per SPEC v0.5.1 applies_to.author.
kind: rule
review_mode: shared
applies_to:
  author: REPLACE_WITH_YOUR_GH_LOGIN
---

# Conventions: <YOUR NAME>

This skill captures how I review pull requests when they're opened by
me. The bot loads this skill ONLY on my PRs (per the
`applies_to.author` filter above — SPEC v0.5.1 §1.10.1). Other PRs
go through the org defaults without my personal preferences applied.

## How to use this template

1. **Rename the directory**: `.claude/skills/conventions-<your-gh-login>/SKILL.md`
2. **Set `applies_to.author`** to your GitHub login (replace `REPLACE_WITH_YOUR_GH_LOGIN`)
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

## How I phrase findings

Tone guidance for when the bot generates review prose on your PRs
(layers on top of the org `voice-<your-org>` if installed).
Examples:

- Direct, no preamble — lead with the issue
- Cite the specific line + quote the offending snippet
- Suggest a concrete fix, not just "consider X"
- No emoji decoration; the severity icons are the only emoji
