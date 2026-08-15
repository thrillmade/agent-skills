# AGENTS.md

This is the canonical instruction file for AI coding agents working in this
repository. Tools that understand `AGENTS.md` (Cursor, Codex, Windsurf,
Claude Code, Cline, Continue, Aider, ...) read this file directly. Per-tool
files like `CLAUDE.md` or `.cursorrules` are stubs that point here so the
guidance lives in one place.

<!-- logmind-start -->
<!-- logmind-block-version: v8-pointer -->
## Decision logging — `logmind log` is REQUIRED for substantive commits

**`logmind log` replaces `git add` + `git commit` + `git push` for any change that carries a decision** — do not run those git commands directly.

> **DO NOT run raw `git add` / `git commit` / `git push` for substantive code changes.**
> The commit-msg hook installed by `logmind init` warns when raw git is used on
> a substantive commit; the intent is to prevent the warning, not bypass it via
> `--no-verify`. Typo / whitespace / dep-bump-only commits MAY use raw git.

```bash
logmind log "summary" -r "why" -a "alternative" -i "implication"
```

This project uses [logmind](https://logmind.dev). What counts as a decision, branch routing, `--stage scoped` for unrelated WIP, `logmind doctor`, and the required-reading list ([`docs/timeline.md`](docs/timeline.md), [`docs/decisions.md`](docs/decisions.md), [`docs/file-structure.md`](docs/file-structure.md), `docs/decisions-branches/<branch>.md`) all live in the **`logmind` agent skill** at https://github.com/thrillmade/agent-skills/tree/main/skills/logmind.
<!-- logmind-end -->

## Project Overview

<!-- Replace with a short description of what this project does. -->

## Development Commands

```bash
python3 .github/scripts/validate_skills.py   # the skill gate — run it before you push
pytest tests/ -q                             # 112 tests; the gates' own regression guard
logmind log "…" -r "…" -a "…" -i "…"         # the commit primitive (see above)
```

The first two run in about a second. **Neither is optional before opening a PR** — CI runs
the same two, unconditionally.

## The `dev` branch

Work lands on `dev` first and reaches `main` in batches. `dev` is somewhere work *passes
through*, not somewhere work *lives*. The rules are the organisation's, set out in the private
`thrillmade/protocol`; this repository is public, so they are stated here, not linked to.

**Branch from `dev`, and open a pull request into `dev`** — the default branch is `main`, so
the base has to be set by hand. The five workflow checks — `test`, `validate skills`,
`check-links`, `check-decisions`, `check-derived-docs` — all run on a pull request; `test`,
`validate skills` and `check-links` also run on a push to `main`. **Nothing runs on a push to
`dev`**, so a commit pushed straight there is checked by nothing
(`gh api repos/thrillmade/agent-skills/commits/dev/check-runs --jq .total_count` → `0`; the
same call against `main` → `4` — those three plus the skipped `self-heal` job — which is that
push run).

**Into `dev`: an independent adversarial review.** A change may merge once a reviewer that
did **not** write it has reviewed it and its findings are addressed — a refute-first panel,
or clud-bug in local mode. **Independence means a different agent.** A fresh context window
on the same agent is not a different agent, and neither is the same agent asked to look again.

**Into `main`: a person.** An agent does not open or merge the `dev` → `main` promotion; it
reports the batch ready and hands off. An active org ruleset requires one approving review on
`main`, so a PR there reports `REVIEW_REQUIRED` until someone approves it, while a PR into
`dev` reports no review decision at all.

**A red check is fixed, not merged past.** Nothing here is gated on a check: `main` has **no
`required_status_checks` rule** and no classic protection either
(`gh api repos/thrillmade/agent-skills/rules/branches/main`). So red merges, and has — #188
went into `main` four days after `check-links` failed on it. The forge asks for a human
approval, not a green suite; the suite is on whoever is working.

**Read the failing step before believing a red — one *kind* of red is dismissible, and only one.**
`check-links` and `check-derived-docs` check out the head *branch by name*, and branches are
deleted on merge, so a run still in flight when a PR merges dies with `A branch or tag with
the name '…' could not be found`. That is an artifact of the merge, not a verdict on the
change. `test`, `validate skills` and `check-decisions` check out the merge ref instead and
are unaffected.

That is the **only** dismissible kind, and all three conditions must hold: the failing step is
the checkout, the message is the one above, and the head branch is gone because the PR merged.
More than one check can fail this way at once — on #216 both did. **Every other failing step is
a real red, including one where the check's own step never ran because a setup step died.** A skipped verdict is not a passing verdict. #188's red was exactly that
kind — `setup-logmind` failed, so `check-links` never evaluated a link — and it was merged
anyway. Re-run it or fix it; do not reason your way past it.

**What batching costs.**

| check | weakened by batching? |
|---|---|
| `test` · `validate skills` · `check-links` · `check-derived-docs` | **No.** Each judges the tree it is handed, so six changes checked once is the same assertion as six checked six times. |
| `check-decisions` | **Yes.** It is a *presence* check — one decision file anywhere in the diff clears the whole batch. **A batch does not inherit one change's decision.** The dilution is a property of the forge, not a permission: every change still logs its own, and the check simply stops being the thing that enforces it, so the reviewer is. |
| `clud-bug-review` | **Not applicable** — it is not producing reviews here. See [clud-bug is not reviewing here](#clud-bug-is-not-reviewing-here). |

**No forge rule protects `dev`** (`rules/branches/dev` returns `[]`), so every rule above
**about `dev`** is a convention held by whoever is working. `main` does carry forge rules —
the approving review, `deletion`, `non_fast_forward`, `required_linear_history` — but the
approving review is bypassed in practice: #209, #211 and #212 all went into `main` at
`REVIEW_REQUIRED` with **zero** reviews. Nothing in the forge distinguishes an agent from a
person either, so "a person" is a convention there too. **That the forge does not enforce a
rule is a property of the forge, not a permission** — the independent review is the only rule
applied per change rather than per batch, and it is held by whoever is working.

<!-- clud-bug-start -->
<!-- clud-bug-block-version: v2 -->
## clud-bug — Claude PR review

This repo uses [clud-bug](https://cludbug.dev) for automatic PR reviews.
Full collaboration rules — fix-push flow, skill structure, comment format,
strict-mode mechanics, workflow-edit constraint — live in the bundled
[`clud-bug-collaboration` skill](skills/clud-bug-collaboration/SKILL.md).
Read that skill before pushing fixes addressing prior review threads.

Strict mode is **on** in this repo (workflow check fails on critical findings). Toggle via `.claude/skills/.clud-bug.json`
(read from PR **base ref**, so PRs can't disable strict-mode on themselves).

For agent invocations of the `clud-bug` CLI, prefer `CLUD_BUG_QUIET=1`
(or pass `--quiet`) — suppresses progress chatter and emits a single
`ok <key-value>` summary line per command.

_Installed at clud-bug v0.7.0-rc.20._
<!-- clud-bug-end -->

### clud-bug is not reviewing here

The block above describes the mechanism and is regenerated by `clud-bug update` weekly, so
nothing measured belongs inside it. What is measured belongs here: **strict mode never fails
on anything, because no review is being produced.** On every pull request since #188 —
twelve of them — `clud-bug-review` has concluded `neutral` with the title *"clud-bug review
unavailable"*. #187 concluded `success`, so that is a real boundary and an outage, not a
configuration. Re-check before relying on it:

```bash
gh api repos/thrillmade/agent-skills/commits/<sha>/check-runs \
  --jq '.check_runs[] | select(.name=="clud-bug-review") | "\(.conclusion) \(.output.title)"'
```
