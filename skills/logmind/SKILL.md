---
version: "1.0.2"
digest: "6ca852acf9bf"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
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

One invocation replaces `git add` + `git commit`. This skill describes
logmind v1.2.0, the latest release; `logmind version` shows yours.

1. Appends to `docs/decisions-branches/<sanitized-branch>.md` on a feature
   branch (`decisions.branch_aware`, on by default) — one file per branch,
   append-only. On the default branch, a detached HEAD or a non-git
   directory it appends to `docs/decisions.md` instead. `logmind log`
   routes this, you don't.
2. **Stages the whole working tree** (`--stage all`, the default) so the
   decision and its code land in one commit — **don't `git add` first**.
   `--stage scoped` stages only the decision file when you have unrelated
   WIP you don't want swept in.
3. `git commit` with message `logmind: <decision>`. It **does not push** —
   `git.auto_push` is in the config but v1.2.0 never reads it. Run
   `git push` yourself.
4. Link-checks the markdown. On findings it prints an advisory; in a
   terminal it offers up to three fix-and-recheck tries, and
   `--no-interactive` (or piped stdin) skips the prompt and exits 0. The
   prompt path exits 1 on `q` or after three failed rechecks. The commit
   has landed either way.

`logmind log` does not regenerate the derived docs — see below. After it
you owe only the push.

## Enforcement: a local hook and a PR gate

- The pre-commit hook (`logmind check-decisions`) **blocks** (exit 1) a
  sizeable commit with no decision-file update. It never reads
  `[skip-logmind]`; its escape is `git commit --no-verify`.
- `logmind init` also installs `check-decisions.yml`, a PR gate on 20+
  non-doc changed lines. It honors `[skip-logmind]` in the **PR title** only.
- In a commit subject, `[skip-logmind]` only makes the `commit-msg` hook
  echo a notice; nothing else reads it.

## Reading prior context

Before non-trivial work, read in order:

1. **`docs/timeline.md`** — the generated union of decision entries across
   every branch, brief by default (first and last entry per month;
   `logmind timeline --full` prints every one).
2. **`docs/decisions-branches/<your-branch>.md`** if present — earlier
   decisions on this branch, in full.
3. **`docs/decisions.md`** and `docs/decisions-archive.md` — default-branch
   decisions; grep them for a term before re-deciding it.
4. **`docs/file-structure.md`** — project tree, capped at depth 2 by
   default (`--max-depth N` on `logmind file-structure` / `logmind tree`;
   `0` = unbounded).

## Derived docs are generated — never hand-edit them

`docs/timeline.md` and `docs/file-structure.md` are computed from sources
(the decision files above; a tree walk). Edit the sources instead.

`regen-timeline.yml` regenerates both on every PR. If they are stale it
pushes the fix to the branch when `LOGMIND_AUTO_REGEN_PAT` is set; with no
PAT, or on a fork PR, it fails red with `Stale derived docs`. The fix is
regeneration, not a hand edit and not a copy from another branch:

```bash
logmind timeline --write docs/timeline.md
logmind file-structure --write docs/file-structure.md
```

Commit both. Add `--check` to either for a CI exit status without writing.
The same regeneration resolves a merge conflict in either file: re-run it,
never pick a side. It reads only your checkout's sources, so there is no
base or tip copy to choose between.

## Parallel-PR merges

Two PRs that both run `logmind log` don't conflict on the derived docs:
`logmind init` installs a `.gitattributes` merge-driver block, the
per-clone `git config` defining the drivers, and a `.git/hooks/post-merge`
sweep that regenerates what the driver missed (unstaged — the next
`logmind log` picks it up); `logmind doctor` reports drift on all three.
Client-side only — it can't help a server-side merge.

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

Local and read-only against remotes **except `push`: without
`--dry-run` it clones the catalog, pushes a branch, and opens a real pull
request the moment you run it — no confirmation prompt.** Run `logmind
skill push <name> --dry-run` first, every time. Nomination isn't
publication: the catalog's editor gate decides, and can say no. `suggest`
is also not local by default: with `ANTHROPIC_API_KEY` set it sends
pattern candidates and evidence to api.anthropic.com; pass `--no-llm`.

## Setup and health

```bash
brew install thrillmade/tap/logmind # or: curl -fsSL https://logmind.dev/install.sh | bash
logmind init   # scaffolds docs/, AGENTS.md, workflows, merge drivers, hooks
logmind doctor # confirm clean install
```

`logmind init --with-skdd` accepts the flag but currently **defers** — it
prints a note to run `npx clud-bug@latest init` yourself. Run them
separately.

`logmind doctor` flags stale workflow templates, stale hooks, merge-driver
drift and an outdated `AGENTS.md` block-version, exiting non-zero on drift
so it's CI-pluggable (`--json` for scripts, `--exit-zero` for informational
runs). It has no clud-bug probe, and its installed-vs-latest version line
is not reliable in v1.2.0 — don't read it as "up to date".

## Don'ts

- Don't write the decision after the fact in past tense for trivial code.
- Don't reword a decision someone else already logged — link or extend it.
- Don't bypass the auto-commit (`--no-commit`) unless the project's branch
  protection requires it.

## Cross-references

- [token-frugal-tooling](../token-frugal-tooling/SKILL.md) — token-frugal defaults for agent sessions.
- [clud-bug-collaboration](../clud-bug-collaboration/SKILL.md) — the review half.
