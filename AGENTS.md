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
pytest tests/ -q                             # the gates' own regression guard
logmind log "…" -r "…" -a "…" -i "…"         # the commit primitive (see above)
```

The validator runs in about a second. The suite takes minutes: most of its wall clock is the
two mutation files (`test_prose_retention_mutations.py`, `test_skill_directory_mutations.py`),
which each run the real suites in a subprocess once per mutation — that is what makes "this
guard can fail" a fact rather than a claim, and it is worth the wait. Run the fast subset while
iterating —
`pytest tests/ -q --ignore=tests/test_prose_retention_mutations.py --ignore=tests/test_skill_directory_mutations.py`
— and the whole thing before you push. **Neither command is optional before opening a PR** — CI
runs the same two, unconditionally. (No test count or duration is quoted here on purpose: a
hand-kept number with no gate reads as true until one quietly isn't. Run it and read the
output.)

## The `dev` branch

Work lands on `dev` first and reaches `main` in batches. `dev` is somewhere work *passes
through*, not somewhere work *lives*. These are the organisation's rules, not this repo's;
changing them is not a local decision.

**Branch from `dev`, and open the pull request into `dev`.** The default base is `main`, so set
it by hand. Never push straight to `dev` — no workflow runs on a push there, so the commit is
checked by nothing.

**Into `dev`: an independent adversarial review.** A change may merge once a reviewer that did
**not** write it has reviewed it and its findings are addressed — a refute-first panel, or
clud-bug in local mode. **Independence means a different agent.** A fresh context window on the
same agent is not a different agent, and neither is the same agent asked to look again. The
review is a panel, not a GitHub approval; a PR into `dev` reports no review decision at all.
This is the only rule applied per change rather than per batch, so it carries the weight.

**Into `main`: a person.** An agent does not open or merge the `dev` → `main` promotion; it
reports the batch ready and hands off.

**A red check is fixed, not merged past.** Read the failing step first.

One *kind* of red is an artifact rather than a verdict, and only one. `check-links` and
`check-derived-docs` check out the head branch **by name**, so a run still in flight when the
PR merges dies at the checkout step with `A branch or tag with the name '…' could not be
found`. Both can fail this way at once.

**Every other failing step is real** — including one where the check's own step never ran
because a *setup* step died. A skipped verdict is not a passing verdict. Re-run it or fix it;
do not reason your way past it.

**Batching dilutes exactly one check.** `check-decisions` asks only whether *some* decision file
is in the diff, so one entry clears a whole batch. Every change still logs its own regardless.

**Nothing in the forge enforces any of the above.** No rule protects `dev`; `main`'s
approving-review rule is bypassed in practice; nothing there tells an agent from a person. That
a rule is not enforced is a property of the forge, not a permission.

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
on anything, because no review is being produced.** On every pull request since #188,
`clud-bug-review` has concluded `neutral` with the title *"clud-bug review
unavailable"*. #187 concluded `success`, so that is a real boundary and an outage, not a
configuration. Re-check before relying on it:

```bash
gh api repos/thrillmade/agent-skills/commits/<sha>/check-runs \
  --jq '.check_runs[] | select(.name=="clud-bug-review") | "\(.conclusion) \(.output.title)"'
```
