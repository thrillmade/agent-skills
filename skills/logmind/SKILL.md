---
name: logmind
description: |
  MUST be loaded for any task in a project that uses logmind (detect by:
  .logmind/config.yml at repo root, or AGENTS.md / CLAUDE.md mentioning
  logmind, or docs/decisions.md present). Use BEFORE writing >20 lines of
  new code, BEFORE choosing between alternatives, BEFORE adding a
  dependency, BEFORE modifying existing functionality, BEFORE making any
  security or performance trade-off, BEFORE renaming or moving any
  significant module. Logging is part of the work, not after it. Also use
  to read prior decisions before starting any task in such a project so
  you don't re-litigate something already decided.
review_mode: shared
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

### CLI (preferred)

```bash
logmind log "Use PostgreSQL for primary database" \
  -r "Need ACID compliance and complex joins" \
  -a "MongoDB" -a "SQLite" \
  -i "Connection pooling required" \
  -i "Schema migrations needed"
```

### Python

```python
from logmind import log

log("Use PostgreSQL for primary database",
    reasoning="Need ACID compliance and complex joins",
    alternatives=["MongoDB", "SQLite"],
    implications=["Connection pooling required", "Schema migrations needed"])
```

## What `logmind log` does automatically

A single `logmind log` invocation is the complete `git add` + `git commit` +
`git push` primitive — you do NOT need to follow up with any manual git
command, and you do NOT need to run `logmind timeline --write` separately:

1. **(v0.6.1+, opt-in) Auto-rebase** — if `git.auto_rebase: true` is set in
   `.logmind/config.yml`, runs `maybe_auto_rebase()` BEFORE any local state
   changes. See [Deterministic auto-rebase](#deterministic-auto-rebase-v061-opt-in) below.
2. Appends the decision entry to the active log file (default branch →
   `docs/decisions.md`; feature branch → `docs/decisions-branches/<branch>.md`).
3. Archives the oldest decision if `decisions.md` exceeds `max_recent` (rotation).
4. Regenerates `docs/file-structure.md` (default branch only — on feature
   branches the tree snapshot diverges and would conflict).
5. **Regenerates `docs/timeline.md` on every branch (v0.2.3+)** — the derived
   index that `check-derived-docs` CI verifies.
6. **`git add` every change in the working tree (default since v0.2.7)** —
   so the decision and the code that prompted it travel together in one
   commit. Override with `--stage scoped` if you have unrelated WIP.
7. **`git commit`** with message `logmind: <decision>`.
8. **`git push`** to remote (configurable via `auto_push` in
   `.logmind/config.yml`).

## `logmind log` IS the commit primitive (no manual git after it)

`logmind log` defaults to `--stage all` (since v0.2.7): every change in
the working tree gets bundled into the decision commit. No follow-up
`git add`, no follow-up `git commit`, no follow-up `git push`. One command,
one commit, working tree clean.

If you find yourself running `git add`, `git commit`, `git push`, or
`logmind timeline --write` **after** a `logmind log`, you're working
against the design. Two likely causes:

1. **Pre-v0.2.7 logmind installed** — check `logmind --version` and
   `logmind doctor`. v0.2.6 and earlier defaulted to `--stage scoped`.
2. **You actually need `--stage scoped`** — see below.

### `--stage scoped` (escape hatch)

Pass `--stage scoped` to stage only the decision file + companion files
(`file-structure.md`, archive if rotated, `timeline.md` if regenerated).
Unrelated working-tree changes stay unstaged. Use when:

- You have WIP in the working tree you don't want to commit yet.
- You're doing a multi-step refactor where the decision should be
  reviewable on its own, separately from the implementation.

Rare for automated agents — they should be working on one task at a
time and want the single-commit shape.

## Branch-aware routing (automatic)

On a feature branch the entry lands in
`docs/decisions-branches/<sanitized-branch>.md`. On PR merge a workflow
appends a one-line summary linking the PR + the per-branch file to
`docs/decisions.md`. You do not manage this — `logmind log` does.

## Deterministic auto-rebase (v0.6.1+, opt-in)

When PRs land out-of-order, a trailing branch can go DIRTY because
`main`'s `docs/timeline.md` gained new entries. Recovery is mechanical
(rebase + regen timeline + force-with-lease push). v0.6.1 automates this
behind a strong opt-in flag.

**Default: OFF.** Enable in `.logmind/config.yml`:

```yaml
git:
  auto_rebase: true
```

When enabled, `logmind log` checks **all 6 conditions** before touching
any local state:

1. `auto_rebase: true` in config
2. Branch is NOT the default branch
3. `git fetch origin <default>` succeeds
4. `origin/<default>` ref exists
5. Branch is behind `origin/<default>` (commits_behind > 0)
6. **The gap touches EXACTLY `docs/timeline.md`** — no code, no other
   derived docs, not even `docs/file-structure.md`

If all 6 hold: rebase → (on conflict only in `timeline.md`) regen +
continue → `git push --force-with-lease`. On any unexpected conflict
surface: `git rebase --abort` + bail safely (no half-applied state).

**Always `--force-with-lease`, never `--force`.** The scope is deliberately
narrow: `docs/timeline.md` is fully derived (regenerated from
`docs/decisions.md` + per-branch decision files), so conflict resolution
= re-run the generator. Other files — even `docs/file-structure.md` —
depend on broader repo state and are NOT in scope for this release.

User-visible log line when it fires:

```
↻ logmind auto-rebased 'feature' onto origin/main
  (was 2 commits behind, only docs/timeline.md affected
  — safely deterministic).
```

When enabled but conditions don't hold, logmind emits a predictive
heads-up naming the disqualifying files — no action is taken.

## Reading prior context

Before starting non-trivial work, read in order:

1. **`docs/timeline.md`** — auto-generated chronological overview across
   every branch; start here. **Since v0.5.4 the on-disk format is
   brief** (per month: header with decision count + first + last entry
   + elision line). Use `logmind timeline --full` for the legacy
   per-decision listing.
2. **`docs/decisions.md`** — direct-on-main decisions in detail (20 most
   recent).
3. **`docs/decisions-branches/<your-branch>.md`** if present — decisions
   made earlier on the same feature branch.
4. **`docs/file-structure.md`** — current project tree. **Since v0.5.0
   the on-disk tree is capped at depth 2 by default.** For a deeper
   view, run `logmind file-structure --max-depth N` (or
   `logmind tree --max-depth 0` for fully unbounded).

```bash
logmind show                       # recent decisions on the current branch
logmind show --all                 # include archive

# Agent-friendly views (v0.5.2+) — combinable.
logmind show --brief               # one line per entry: "YYYY-MM-DD HH:MM — title [source]"
logmind show --brief --limit 10    # last 10 in brief form
logmind show --json --limit 20     # parseable JSON array
logmind show --json --all          # JSON across main + archive sources

logmind search "postgres"          # full-text across both files
```

## Agent-invocation mode: `LOGMIND_QUIET=1` (v0.5.1+)

When an agent (CI script, Claude Code session, downstream tool) runs
logmind, the verbose progress chatter (`ℹ Default --stage all`,
`✓ Logged decision`, sync messages) lands in the agent's context and
burns tokens. Set `LOGMIND_QUIET=1` (or pass `--quiet` / `-q` on the
group) to suppress progress and emit a single `ok <key-value>`
summary line per command. Errors and warnings still print.

```bash
LOGMIND_QUIET=1 logmind log "..." -r "..."
# → ok logged: <commit-sha> "<title>"

LOGMIND_QUIET=1 logmind tree --write docs/file-structure.md
# → ok file-structure: docs/file-structure.md (10240 bytes, depth=2)
```

`logmind show --json` always emits parseable JSON to stdout
regardless of `--quiet` (JSON is primary output, not progress). The
`ok` summary in JSON mode goes to stderr so pipelines like
`logmind show --json | jq` stay clean. Internally v0.5.3 patched
`click.secho` so red/yellow error/warning output still prints under
`LOGMIND_QUIET=1` — only progress chatter (cyan/green) is suppressed.

## Verifying install health

`logmind doctor` (v0.2.4+) reports installed-vs-latest versions for logmind
(and clud-bug if present), flags stale workflow templates AND a stale
`AGENTS.md` block-version (v0.2.9+) against bundled markers, and exits
non-zero on drift so it's CI-pluggable.

```bash
logmind doctor             # one-shot status table
logmind doctor --json      # for scripts
logmind doctor --offline   # skip PyPI / npm probes
logmind doctor --exit-zero # always exit 0 (informational CI runs)
```

Run after `logmind init` to confirm a clean install, or any time
templates / pins / instructions might have drifted. Stale-pin drift is
auto-healed by `logmind init` itself in v0.2.5+, even when no template
body changed. **If `doctor` reports an `AGENTS.md` stale row, your repo's
embedded logmind instructions are older than what the installed logmind
would write — re-run `logmind init` to refresh in place.**

## Parallel-PR merges: timeline + file-structure merge driver (v0.3.0+)

Two PRs that both run `logmind log` no longer textually conflict on
`docs/timeline.md` or `docs/file-structure.md` on rebase. v0.3.0's
`logmind init` installs three pieces that handle this together:

- **`.gitattributes` block** (idempotent, marker-bracketed) — registers
  `merge=logmind-timeline` and `merge=logmind-file-structure` for the
  two derived files.
- **Per-clone `git config`** — defines the merge drivers themselves
  (`merge.logmind-timeline.driver = 'logmind timeline --write %A'`,
  similar for file-structure). Lives in `.git/config`, not committed
  (git refuses to auto-run a merge driver that isn't explicitly
  configured locally — security guard against untrusted repos). Fresh
  clones need `logmind init` once to pick this up.
- **`.git/hooks/post-merge`** — re-regenerates both derived files from
  the full post-merge working tree. Belt + suspenders: the driver runs
  per-file mid-merge before the other branch's `docs/decisions-branches/`
  files are checked out, so its output can miss decisions; the hook
  sweeps any incomplete regen at end-of-merge.

`logmind doctor` reports three new rows for these (v0.3.0+):
`.gitattributes (merge driver)`, `git config (merge driver)`, and
`post-merge hook`. Missing rows are not drift — they're "not yet
installed for this logmind version" — the next `logmind init` resolves
them silently.

The merge driver invokes `logmind file-structure --write <path>`
(v0.3.0+), the mirror of `logmind timeline --write`. Like the timeline
command, you should not run it by hand in the normal flow — it exists
for the merge driver and as an escape hatch (corrupted file, externally
modified tree).

## Upgrading: `logmind init` prints the changelog

When you run `pip install --upgrade logmind && logmind init` in an
already-initialized repo (v0.2.10+), refresh-mode detects the prior
pinned version from `regen-timeline.yml` and prints **every CHANGELOG
section between that version and the currently installed
`__version__`** inline:

```
📋 What's new in logmind since v0.2.6 (currently installed: v0.2.10):

## [0.2.10] - ...
### Added
- logmind init refresh-mode prints CHANGELOG sections...

## [0.2.9] - ...
### Changed
- actions/checkout@v4 → @v6 across all shipped templates...

...
```

Read it. The whole point is that your in-session memory might predate
the upgrade, and the printed sections tell you exactly what changed.
Common deltas you'll see if you're upgrading across a stretch:

- **v0.2.7**: `logmind log` defaults to `--stage all` (single
  add+commit+push primitive — stop running `git add` first).
- **v0.2.9**: `logmind log` prints a visible `--stage` notice on every
  invocation so the actual behavior is unmissable in output.
- **v0.2.9**: `logmind doctor` flags stale `AGENTS.md` block-version.
- **v0.3.0**: `logmind init` registers a git merge driver for
  `timeline.md` / `file-structure.md` so parallel-PR merges no longer
  conflict on the derived files. Doctor gains three rows tracking it.
- **v0.6.1**: `logmind log` gains opt-in deterministic auto-rebase via
  `git.auto_rebase: true` in `.logmind/config.yml`. Narrow scope: only
  fires when the gap between your branch and `origin/<default>` is
  exactly `docs/timeline.md`. Always uses `--force-with-lease`.
- **v0.6.8**: `logmind init --with-skdd` bootstraps the full SkDD
  toolchain (logmind + clud-bug) in one command. Without the flag,
  `logmind init` is unchanged.

## Setup (one-time, per project)

If the project doesn't yet have logmind:

```bash
pip install logmind
logmind init               # scaffolds docs/, AGENTS.md, GH Actions, .gitignore block, merge drivers + post-merge hook (v0.3.0+)
logmind doctor             # confirm clean install
```

### Full SkDD toolchain in one command (v0.6.8+)

If your project uses the SkDD toolchain (logmind + clud-bug), use
`--with-skdd` to bootstrap both tools in a single step:

```bash
pip install logmind
logmind init --with-skdd   # runs logmind init, then npx --yes clud-bug@latest init
logmind doctor             # confirm clean install
```

Behavior details:

- **No flag**: `logmind init` runs as always — Python-only, no change.
- **`--with-skdd` + `npx` on PATH**: after logmind setup completes,
  subprocesses to `npx --yes clud-bug@latest init` and streams its
  output to you (not silenced).
- **`--with-skdd` + no `npx`**: emits a clear warning with the manual
  recovery command (`npx --yes clud-bug@latest init`); exits 0. Logmind
  init itself still succeeds.
- **Subprocess failure** (non-zero exit or OSError): warning is surfaced
  but logmind init still succeeds — clud-bug is an additive layer.

The flag targets the bundle (the SkDD toolchain), not a specific tool,
so it stays stable as the toolchain grows. There is no mutual recursion:
`logmind init --with-skdd` calls `npx clud-bug init` (without
`--with-skdd`), going only one level deep.

## Don'ts

- **Don't run `git add`, `git commit`, or `git push` for changes that
  carry a decision.** `logmind log` is the commit primitive — it handles
  all three in one step. Running them manually either bypasses the
  logging entirely or splits the work across separate commits, both of
  which lose the value of having the reasoning attached to the code.
- **Don't run `git add` BEFORE `logmind log` either.** Default
  `--stage all` already sweeps the working tree; pre-staging is
  redundant. (Exception: if you're using `--stage scoped` and have
  extra files you specifically want included, pre-stage them and they
  carry through — but `--stage all` is the right answer 99% of the
  time for agents.)
- **Don't run `logmind timeline --write docs/timeline.md` after a `logmind
  log`** — it's already regenerated and staged. The standalone command is
  an escape hatch for unusual situations (a corrupted timeline, a tree
  someone touched outside logmind), not part of the normal flow.
- **Don't use `--force` instead of `--force-with-lease` in any git push
  associated with logmind workflows.** The auto-rebase feature (v0.6.1+)
  enforces `--force-with-lease` exclusively; never substitute `--force`.
- **Don't expect auto-rebase to handle anything beyond `docs/timeline.md`.**
  If the gap between branches includes code files, `docs/file-structure.md`,
  or any file other than `docs/timeline.md`, auto-rebase will refuse and
  emit a heads-up — handle the rebase manually.
- Don't log every tiny edit. The 20-line rule is a guideline; use judgement.
- Don't write the decision after the fact in past tense for trivial code.
- Don't reword a decision someone else already logged — link or extend it.
- Don't bypass the auto-commit (`--no-commit`) unless you know the project's
  branch protection requires it.
