---
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

If the current project contains `.logmind/config.yml` or its `AGENTS.md`
mentions logmind, this skill applies. Log a decision **before** writing
non-trivial code, not after.

## When to log

Log a decision whenever you:

- Make an architectural or design choice
- Choose between alternative approaches
- Write significant new code (> 20 lines or a new module)
- Modify existing functionality in a non-obvious way
- Add or remove a dependency
- Make a security or performance decision

When in doubt, log it. A short decision entry is cheap; recovering missing
context months later is not.

## How to log

```bash
logmind log "Use PostgreSQL for primary database" \
  -r "Need ACID compliance and complex joins" \
  -a "MongoDB" -a "SQLite" \
  -i "Connection pooling required" \
  -i "Schema migrations needed"
```

## `logmind log` IS the commit primitive — no manual git after it

A single invocation replaces `git add` + `git commit` + `git push`:

1. Appends the decision to `docs/decisions-branches/<branch>.md` — one
   file per branch, and `main` is a branch like any other. Every file is
   append-only and uncapped: nothing rotates, nothing is archived.
2. Regenerates `docs/file-structure.md` (default branch only) and
   `docs/timeline.md` (every branch), which carries the 50 most recent
   entries with `docs/timeline-archive.md` continuing it.
4. **Stages the whole working tree** (`--stage all`, the default since
   v0.2.7) — the decision and the code that prompted it land in one
   commit. Pass `--stage scoped` to stage only the decision file(s) when
   you have unrelated WIP you don't want swept in.
5. `git commit` with message `logmind: <decision>`, then `git push`
   (configurable via `auto_push`).

Don't follow up with `git add`, `git commit`, `git push`, or
`logmind timeline --write` — all three are already done, and the
timeline is already regenerated and staged.

## Enforcement: raw `git commit` is blocked

A substantive commit that bypasses `logmind log` is **blocked**, not just
discouraged — a git `commit-msg` hook, plus (inside Claude Code) a
PreToolUse hook that intercepts the `git commit` Bash call before it runs.

Escape hatches, for genuinely no-decision commits (typos, dep bumps):
- Add `[skip-logmind]` to the commit subject.
- Set `LOGMIND_ALLOW_GIT_COMMIT=1` for one command.
- `git.enforce_commits: false` in `.logmind/config.yml` disables
  enforcement repo-wide.

## Branch-aware routing (automatic)

Every entry lands in `docs/decisions-branches/<sanitized-branch>.md` — one
file per branch, and `main` is a branch like any other. The file is
permanent: when a branch lands, nothing folds it elsewhere, copies it or
deletes it. `logmind log` manages the routing; you don't.

## Reading prior context

Before starting non-trivial work, read in order:

1. **`docs/timeline.md`** — the canonical, source-derived union of
   decision entries across every branch, each led by its **headline**
   (see below). Carries the 50 most recent; `docs/timeline-archive.md`
   continues it. Start here.
2. **`docs/decisions-branches/<your-branch>.md`** if present — decisions
   made earlier on the same branch, in full.
3. **`docs/file-structure.md`** — current project tree (capped at depth 2
   by default; `logmind file-structure --max-depth N`, or
   `logmind tree --max-depth 0` for the unbounded view).
5. **The canonical spec file, if configured** — `.logmind/config.yml`'s
   `context.spec_file`; the forward-looking intended contract. Build
   toward it, don't assume it already describes the code; nothing
   regenerates it, so refine it via an ordinary PR when intent changes.

`logmind context` bundles the file structure + timeline (+ spec file, when
configured) into one cache-friendly read.

```bash
logmind show                       # recent decisions on the current branch
logmind show --brief --limit 10    # one line per entry
logmind show --json --all          # parseable JSON, main + archive
logmind search "postgres"          # full-text across both files
```

## Branch summaries (headline)

On a feature branch, set a one-sentence summary of what the **whole
branch** does — the canonical timeline shows this line for the branch.

```bash
logmind headline "Add JWT session auth with refresh-token rotation"
# or bundle into a decision commit:
logmind log "Wire refresh-token rotation" -r "..." -H "Add JWT session auth..."
```

No-op on the default branch. `logmind doctor --fix` backfills a missing
headline.

## The pulse: read the advisories after `logmind log`

After a successful commit, `logmind log` may print advisories to stderr —
a stale component (workflow/hook/AGENTS.md drift; run `logmind doctor
--fix`) or spec staleness (the spec file hasn't been touched in 20+
decisions; worth a review). These never block the commit that already
landed — act on them anyway.

## Agent-invocation mode: `LOGMIND_QUIET=1`

Set `LOGMIND_QUIET=1` (or pass `--quiet` / `-q`) so an agent session gets
terse output: progress chatter is suppressed and each command emits one
`ok <key-value>` summary line. Errors and warnings still print.

```bash
LOGMIND_QUIET=1 logmind log "..." -r "..."
# → ok logged: <commit-sha> "<title>"
```

`logmind show --json` always emits parseable JSON to stdout regardless of
`--quiet`; the `ok` summary in JSON mode goes to stderr so pipelines like
`logmind show --json | jq` stay clean.

## Verifying install health

`logmind doctor` reports installed-vs-latest versions (logmind and
clud-bug, if present) and flags stale workflow templates or an outdated
`AGENTS.md` block-version, exiting non-zero on drift so it's CI-pluggable.
Add `--json` for scripts, `--exit-zero` for informational CI runs. Run it
after `init` or whenever pins might have drifted — `init` auto-heals
stale-pin drift even when no template body changed.

### Derived docs are main-only — don't edit them on a branch

`docs/timeline.md`, `docs/timeline-archive.md` and `docs/file-structure.md`
regenerate on `main` only, straight from source (every per-branch decision
log for the history; a tree walk for file-structure). A branch's own
decisions live in `docs/decisions-branches/<branch>.md` — that file is what
you commit to.

The shipped `regen-timeline.yml` GH Action enforces this with a **blocking**
PR-time gate: if your branch's diff touches either derived doc, the check
fails with `::error title=Derived docs were edited on this branch` and
`exit 1` — editing them on a branch is exactly what causes cross-PR merge
conflicts the derived-doc design exists to eliminate. Fix by resetting your
copy to main's:

```bash
logmind warp                                    # read-only refresh
# or
git checkout origin/main -- docs/timeline.md docs/file-structure.md
```

On a push to `main`, a separate job regenerates both files for real and
pushes the update; if no `LOGMIND_AUTO_REGEN_PAT` secret is configured that
push step degrades to a non-blocking `::warning title=Derived docs stale on
main` (freshness-only — no conflict risk). Repos still on the older
fail-fast template instead block on *staleness* (missing file, fork PR, or
no PAT) rather than on branch edits — same spirit, different trigger.

### `logmind warp` — pull main's derived docs into your branch

```bash
logmind warp
# → ok warp: refreshed 2 derived doc(s) from origin/main (read-only — not committed) · main is +3 decision commit(s) ahead
```

Fetches `origin/<default-branch>` and overwrites your working copies of
`docs/timeline.md` + `docs/file-structure.md` from it. **Never stages or
commits** — it exists so your context (and the PR gate above) sees main's
current state without you hand-running `git checkout origin/main -- ...`.
Run it after pulling, or whenever the PR gate flags your branch as having
drifted derived docs.

## Parallel-PR merges: the timeline / file-structure merge driver

Two PRs that both run `logmind log` don't textually conflict on the
derived docs. `logmind init` installs three pieces — a `.gitattributes`
merge-driver block, the per-clone `git config` defining the drivers, and a
`.git/hooks/post-merge` sweep for anything the driver missed; `logmind
doctor` reports drift on all three. The driver is client-side, so it can't
help a server-side merge — which is why the main-only pin above exists.

## Authoring skills locally — `logmind skill …`

A CLI surface for authoring skills *in your own project*
(`.claude/skills/<name>/SKILL.md`). All local-only and read-only against
remotes — **except `push`, which is the one command that reaches out.**

```bash
logmind skill new <name>                # scaffold a SKILL.md
logmind skill test <name>               # frontmatter + structural validation
logmind skill bench <name>              # per-call token-cost measurement + trim suggestions
logmind skill audit                     # every local SKILL.md: bytes, decision-mentions, staleness
logmind skill suggest --since 30d       # pattern-detect candidate skills from recent decisions
logmind skill push <name> --dry-run     # preview; ALWAYS run this first (see below)
logmind skill push <name>               # opens a real PR against the catalog — no confirmation prompt
```

`bench` buckets a skill by loaded cost (tight / typical / verbose /
over-budget); `audit` flags **ghost** (loaded every context, author never
iterates) and **aging** (untouched 90+ days) skills; `suggest` scans
decision entries for repeated tokens and drafts a candidate-skill issue.
Pair with `clud-bug usage --health` (loads vs. citations on real PRs) for
the full cost-vs-value picture.

`new` / `test` / `bench` / `audit` / `suggest` never touch a remote — they
read and write local files only. **`push` is the exception: without
`--dry-run` it clones the catalog, pushes a branch, and opens a real pull
request the moment you run it — no confirmation prompt.** Preview with
`--dry-run` first, every time. Nomination still isn't publication: the
catalog's editor gate decides, and can say no.

## Setup (one-time, per project)

```bash
brew install thrillmade/tap/logmind   # macOS + Linux; or: curl -fsSL https://logmind.dev/install.sh | bash
logmind init               # scaffolds docs/, AGENTS.md, GH Actions, merge drivers + post-merge hook
logmind doctor             # confirm clean install
```

`logmind init --with-skdd` accepts the flag but currently **defers** —
it prints a note to run `npx clud-bug@latest init` yourself rather than
chaining. Run the two separately.

## Don'ts

- **Don't run `git add`, `git commit`, or `git push`** for changes that
  carry a decision — `logmind log` handles all three in one step.
- **Don't run `git add` before `logmind log`** — default `--stage all`
  already sweeps the working tree.
- **Don't run `logmind timeline --write` after a `logmind log`** — it's
  already regenerated and staged; the standalone command is an escape
  hatch for a corrupted timeline or an externally-modified tree.
- Don't log every tiny edit. The 20-line rule is a guideline; use judgement.
- Don't write the decision after the fact in past tense for trivial code.
- Don't reword a decision someone else already logged — link or extend it.
- Don't bypass the auto-commit (`--no-commit`) unless you know the
  project's branch protection requires it.
