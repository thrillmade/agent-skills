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

Both run in about a second. **Neither is optional before opening a PR** — CI runs the
same two, unconditionally.

## The `dev` branch

Work lands on `dev` first and reaches `main` in batches. The bar into `dev` is an
**independent adversarial review** by an agent that did not write the change; the bar into
`main` is a person. The convention is stated once, in
[protocol's `docs/the-dev-branch.md`](https://github.com/thrillmade/protocol/blob/main/docs/the-dev-branch.md) —
this section records only what differs here.

**Batching costs less in this repo than in protocol**, because more of the gates are
per-tree:

| check | weakened by batching? |
|---|---|
| `test` · `validate skills` · `check-links` | **No.** Each judges the tree it is handed, so six changes checked once is the same assertion as six checked six times. |
| `check-derived-docs` | **No.** This repo runs template `v4`, which regenerates and auto-fixes rather than asking who touched what. |
| `check-decisions` | **Yes**, the same way as protocol: `:51-57` sets `decision_touched` as a *presence* flag, so one entry satisfies a whole batch. It also only fires above **20 non-docs lines**, so a docs-only batch never trips it at all. |
| `clud-bug-review` | **Not applicable** — returns `NEUTRAL` here, so there is nothing for batching to dilute. |

So four checks hold at full strength, one is diluted in a named way, and one does not run.
**The independent review is what covers the `check-decisions` gap** — it is the only thing
applied per change rather than per batch.

**No forge rule protects `dev`** (`gh api repos/thrillmade/agent-skills/rules/branches/dev`
returns `[]`), so every rule above is a convention held by whoever is working. That is
acceptable while `dev` is somewhere work *passes through*, and stops being acceptable the
moment it becomes somewhere work *lives*.

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
