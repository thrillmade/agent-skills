---
name: evidence-based-review
description: Every PR review claim must quote the specific code being criticized. No hand-waving.
---

# Evidence-based review

Every claim in your review must be backed by evidence the PR author can verify in seconds.

## Required for every finding

- **Quote the exact line or block** you're talking about (use a fenced code block or `gh pr` inline-comment anchor).
- **Cite the file and line range** so the author can navigate directly there.
- **State the failure mode concretely**: what input produces what wrong output, or what attacker action exploits what gap.

## Banned phrasings

These are red flags that you're hand-waving instead of reviewing:

- "This might cause issues" → say *which* issue, with the input that triggers it.
- "Consider refactoring this" → either it has a bug, or it doesn't. Not your call to redesign their code.
- "This doesn't follow best practices" → cite *which* practice and why it matters here.
- "You should add tests" → name the specific code path that isn't covered.

## Verifying your own claims

Before posting a comment, ask: if the author asked "show me", could I point at the exact line and exact failure case? If not, delete the comment.

A short, specific review of three real issues beats a long, vague review of fifteen maybes.
