---
version: "1.0.0"
digest: "7c3fe31c3949"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: https://github.com/thrillmade/agent-skills
name: logmind
description: |
  MUST be loaded for any task in a project that uses logmind (detect by:
  .logmind/config.yml at repo root, or AGENTS.md / CLAUDE.md mentioning
  logmind, or docs/decisions-branches/ present). Use BEFORE writing >20 lines of
  new code, BEFORE choosing between alternatives, BEFORE adding a
  dependency, BEFORE modifying existing functionality, BEFORE making any
  security or performance trade-off, BEFORE renaming or moving any
  significant module. Logging is part of the work, not after it. Also use
  to read prior decisions before starting any task in such a project so
  you don't re-litigate something already decided.
---

# logmind: log decisions as you work

Applies when the project has `.logmind/config.yml` or an `AGENTS.md`
mentioning logmind. Log a decision **before** writing non-trivial code.

## When to log

- An architectural or design choice
- A choice between alternatives
- Significant new code (> 20 lines or a new module)
- A non-obvious change to existing functionality
- Adding or removing a dependency
- A security or performance decision

When in doubt, log it — an entry is cheap; recovering the context later is
not. But don't log every tiny edit: the 20-line rule is a guideline;
use judgement.

```bash
logmind log "Use PostgreSQL" -r "Need ACID + joins" -a "MongoDB" -a "SQLite" -i "Pooling"
```

## `logmind log` IS the commit primitive — no manual git around it

One invocation replaces `git add` + `git commit` + `git push`.

1. Appends to `docs/decisions-branches/<sanitized-branch>.md` — one file
   per branch, `main` included, append-only and uncapped. Nothing rotates,
   archives, folds, copies or deletes it when a branch lands; `logmind log`
   routes this, you don't.
2. Regenerates the derived docs **on the default branch only** — a branch
   MUST NOT modify them (SPEC §3.3).
3. **Stages the whole working tree** (`--stage all`, default since v0.2.7)
   so the decision and its code land in one commit — **don't `git add`
   first**. `--stage scoped` stages only the decision file(s) when you have
   unrelated WIP you don't want swept in.
4. `git commit` with message `logmind: <decision>`, then `git push`
   (configurable via `auto_push`).

**Nothing follows it** — no `git add` / `git commit` / `git push` /
`logmind timeline --write`; all already done and staged. `logmind timeline
--write` is an escape hatch for a corrupted timeline or an
externally-modified tree only.

## Enforcement: raw `git commit` is blocked

A substantive commit bypassing `logmind log` is **blocked**, not merely
discouraged — a git `commit-msg` hook, plus (inside Claude Code) a
PreToolUse hook intercepting the `git commit` Bash call.
Escape hatches for genuinely no-decision commits (typos, dep bumps):
`[skip-logmind]` in the commit subject; `LOGMIND_ALLOW_GIT_COMMIT=1` for
one command; `git.enforce_commits: false` in `.logmind/config.yml`
repo-wide.

## Reading prior context

Before non-trivial work, read in order:

1. **`docs/timeline.md`** — the canonical, source-derived union of decision
   entries across every branch, each led by its **headline** (below); 50
   most recent, `docs/timeline-archive.md` continues it.
2. **`docs/decisions-branches/<your-branch>.md`** if present — earlier
   decisions on this branch, in full.
3. **`docs/file-structure.md`** — project tree, capped at depth 2 by
   default (`--max-depth N` on `logmind file-structure` / `logmind tree`;
   `0` = unbounded).
4. **The canonical spec file, if configured** (`.logmind/config.yml`'s
   `context.spec_file`) — the forward-looking intended contract. Build
   toward it; don't assume it describes the code. Nothing regenerates it —
   refine it via an ordinary PR.

`logmind context` bundles file structure + timeline (+ spec) in one
cache-friendly read. `logmind show` lists recent decisions on this branch
(`--brief`, `--limit N`, `--json`, `--all`); `logmind search <term>` is
full-text across main + archive.

## Branch summaries (headline)

On a feature branch, set a one-sentence summary of what the **whole branch**
does — the canonical timeline shows this line for the branch. `logmind
headline "<summary>"`, or bundle `-H "<summary>"` into a `logmind log`.
No-op on the default branch; `logmind doctor --fix` backfills a missing one.

## The pulse: advisories after `logmind log`

After a successful commit, `logmind log` may print advisories to stderr — a
stale component (workflow/hook/AGENTS.md drift; run `logmind doctor --fix`)
or spec staleness (spec file untouched for 20+ decisions). They never block
the commit that landed — act on them anyway.

## Agent-invocation mode: `LOGMIND_QUIET=1`

Set `LOGMIND_QUIET=1` (or `--quiet` / `-q`) so an agent session gets one
`ok <key-value>` line per command instead of progress chatter; errors and
warnings still print. `logmind show --json` always emits parseable JSON to
stdout regardless of `--quiet`, with `ok` on stderr so `| jq` stays clean.

## Derived docs are main-only — don't edit them on a branch

`docs/timeline.md`, `docs/timeline-archive.md` and `docs/file-structure.md`
regenerate on `main` only, straight from source. Commit to
`docs/decisions-branches/<branch>.md` instead.

`regen-timeline.yml` enforces this with a **blocking** PR-time gate: a
branch diff touching either derived doc fails with
`::error title=Derived docs were edited on this branch` and `exit 1` —
branch edits cause exactly the cross-PR conflicts this design eliminates.
Fix by resetting to main's copy: `logmind warp`, or
`git checkout origin/main -- docs/timeline.md docs/file-structure.md`.

On a push to `main` a job regenerates both files and pushes; with no
`LOGMIND_AUTO_REGEN_PAT` secret it degrades to a non-blocking
`::warning title=Derived docs stale on main` (freshness-only — no conflict
risk). Repos on the older fail-fast template block on *staleness* (missing
file, fork PR, no PAT) instead of branch edits.

**`logmind warp`** fetches `origin/<default-branch>` and overwrites your
local `docs/timeline.md` + `docs/file-structure.md`. **Never stages or
commits.** Run it after pulling, or whenever the gate flags drift.

## Parallel-PR merges

Two PRs that both run `logmind log` don't conflict on the derived docs:
`logmind init` installs a `.gitattributes` merge-driver block, the
per-clone `git config` defining the drivers, and a `.git/hooks/post-merge`
sweep for what the driver missed; `logmind doctor` reports drift on all
three. Client-side only — it can't help a server-side merge, which is why
the main-only pin exists.

## Authoring skills — `logmind skill …`

For skills in your own project (`.claude/skills/<name>/SKILL.md`): `new`
scaffolds; `test` validates frontmatter + structure; `bench` measures
per-call token cost, suggests trims, buckets by loaded cost (tight /
typical / verbose / over-budget); `audit` reports each local SKILL.md's
bytes, decision-mentions and staleness, flagging **ghost** (loaded every
context, author never iterates) and **aging** (untouched 90+ days) skills;
`suggest --since 30d` drafts a candidate-skill issue from tokens repeated
across decisions. Pair with `clud-bug usage --health` (loads vs. citations
on real PRs).

All local and read-only against remotes **except `push`: without
`--dry-run` it clones the catalog, pushes a branch, and opens a real pull
request the moment you run it — no confirmation prompt.** Run `logmind
skill push <name> --dry-run` first, every time. Nomination isn't
publication: the catalog's editor gate decides, and can say no.

## Setup and health

```bash
brew install thrillmade/tap/logmind # or: curl -fsSL https://logmind.dev/install.sh | bash
logmind init   # scaffolds docs/, AGENTS.md, workflows, merge drivers, hooks
logmind doctor # confirm clean install
```

`logmind init --with-skdd` accepts the flag but currently **defers** — it
prints a note to run `npx clud-bug@latest init` yourself. Run them
separately.

`logmind doctor` reports installed-vs-latest versions (logmind,
clud-bug if present) and flags stale workflow templates or an outdated
`AGENTS.md` block-version, exiting non-zero on drift so it's CI-pluggable
(`--json` for scripts, `--exit-zero` for informational runs). Run it
whenever pins might have drifted — `init` auto-heals stale-pin drift even
when no template body changed.

## Don'ts

- Don't write the decision after the fact in past tense for trivial code.
- Don't reword a decision someone else already logged — link or extend it.
- Don't bypass the auto-commit (`--no-commit`) unless the project's branch
  protection requires it.

## Cross-references

- [token-frugal-tooling](../token-frugal-tooling/SKILL.md) — agent-mode flags.
- [clud-bug-collaboration](../clud-bug-collaboration/SKILL.md) — the review half.
