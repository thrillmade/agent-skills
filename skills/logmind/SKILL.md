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

### PATH-resolution probe (v0.6.16+)

`logmind doctor` now also checks for version drift between the currently-
running logmind process and the `logmind` binary resolved via your shell's
`PATH`. If they differ (e.g. a pyenv shim resolves to an older version),
doctor surfaces the conflict as `stale` showing both versions + the
conflicting path, and exits non-zero (`Stack status: DRIFT`). This guards
against silent hook-body mismatch where `logmind doctor` reports `current`
but `logmind init` is actually writing stale hook bodies from an older
install.

### Derived-doc freshness check (v0.5.13+ / v0.6.9+)

Both derived docs now have CI-friendly fail-fast modes — exit non-zero
when the on-disk file differs from a fresh regen, so CI fails the build
before the auto-fix step (or pre-commit hooks can guard pushes).

```bash
# v0.5.13+:
logmind timeline --write docs/timeline.md --check
# v0.6.9+ (symmetric with timeline):
logmind file-structure --write docs/file-structure.md --check

#   → exit 0 + "✓ … is up to date"   if current
#   → exit 1 + "✗ … is stale — re-run …" if regen would change the file
#   → exit 2 + "requires --write"     if --write is missing
```

The shipped `regen-timeline.yml` GH Action uses these to gate every PR,
and (when `LOGMIND_AUTO_REGEN_PAT` secret is set) auto-regenerates and
pushes the fix back to the PR branch before failing the check.

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

## commit-msg hook: enforcement for substantive commits (v0.6.16+)

`logmind init` now installs a `commit-msg` hook (alongside `post-merge`
and `post-rewrite`) that fires whenever you run `git commit` directly.
It warns when **both** of the following are true:

1. The commit message's first line does NOT start with an exempt prefix
   (`logmind:`, `Revert `, `Merge `, `Bump version`, `chore(release):`,
   `fixup!`, `squash!`).
2. The staged diff exceeds 20 lines across code-bearing extensions
   (`.py .go .ts .tsx .js .jsx .sh .yaml .yml .toml .rs .rb`).

**Default: WARN** (prints a warning but allows the commit). **STRICT
mode** (exits 1, rejecting the commit) is enabled via `.logmind/config.yml`:

```yaml
commit_msg_hook:
  strict: true
```

The hook reads this setting at runtime — flip without re-installing.
Bypass for intentional overrides: `git commit --no-verify`.

**For agents: use `logmind log` for all substantive commits.** The hook
is a safety net, not a substitute — `logmind log` bundles reasoning +
code + push in one step, which the hook cannot replicate.

## Authoring skills locally (v0.6.0+ — `logmind skill …`)

logmind ships a CLI surface for authoring skills *in your own project*
(under `.claude/skills/<name>/SKILL.md`). The surface is deliberately
human-gated — logmind never auto-creates or auto-PRs a skill on your
behalf. Use this for project-specific skills; promote to a public
catalog like agent-skills via the new-skill issue gate when ready.

```bash
logmind skill new <name>                # scaffold .claude/skills/<name>/SKILL.md
logmind skill test <name>               # frontmatter + structural validation
logmind skill bench <name>              # per-call token-cost measurement
logmind skill audit                     # author's-side staleness read
logmind skill suggest --since 30d       # pattern-detect candidate skills
```

### `logmind skill bench <name>` (v0.6.3+) — measure the cost

Reports exactly what a skill costs when loaded: bytes, estimated tokens,
status bucket, per-section breakdown, and trim suggestions when over
budget. Every load of `SKILL.md` puts the whole file into the agent's
context, so the budget matters.

- **tight**: ≤ 2000 bytes (~500 tokens) — focused, well-trimmed
- **typical**: ≤ 6000 bytes (~1500 tokens) — most skills land here
- **verbose**: ≤ 8000 bytes (~2000 tokens) — past budget, suggestions emitted
- **over-budget**: > 8000 bytes — past hard cap, split recommended

Pair with `clud-bug usage --health` (which reports loads vs. citations
on real PR reviews) to know whether a skill EARNS its budget — bench
says what it COSTS, usage says what it RETURNS.

### `logmind skill audit` (v0.6.4+) — author's-side staleness read

One-shot table for every `.claude/skills/<name>/SKILL.md` with bytes,
decision-log mention count, last-touched (via `git log -1 --format=%cs`),
and a deterministic status:

- **ghost**: `decision_count == 0` AND `bytes > 2000` — loaded into every
  context but author never iterates; candidate for archive after
  usage-side confirmation.
- **aging**: last-modified > 90 days — was useful, hasn't been touched
  in a quarter.
- **active**: otherwise.

```bash
logmind skill audit          # human-readable, sorted by name
logmind skill audit --json   # machine-readable, status enriched
```

Pairs with `bench` (cost) and `clud-bug usage --health` (effectiveness)
for the complete skill-lifecycle picture.

### `logmind skill suggest` (v0.6.5+) — pattern-detect candidate skills

Scans recent decision-log entries for tokens that appear across many
distinct decisions — a heuristic signal that "we keep talking about X,
maybe X should have its own skill." Output is a pre-filled GH-issue
draft matching agent-skills's `new-skill.yml` template. The human reads,
decides, opens (or discards).

```bash
logmind skill suggest                       # last 30d, ≥3 decisions, top 5
logmind skill suggest --since 7d --top 10
logmind skill suggest --min-decisions 5     # tighter signal
logmind skill suggest --write-drafts /tmp/proposals/
logmind skill suggest --json                # machine-readable
```

**Never auto-PR. Never auto-create a skill.** This is intentional — the
pragmatic SkDD design (2026-05-30) gates skill lifecycle on humans, not
agents. `suggest` proposes; the human disposes.

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
- **v0.6.16**: `logmind init` installs a `commit-msg` hook that warns
  (or blocks in strict mode) raw `git commit` on substantive code
  changes. `logmind doctor` gains a PATH-resolution probe that exits
  non-zero when the shell-resolved binary version differs from the
  running version. AGENTS.md templates bumped to v6/v8 with
  strengthened "DO NOT run raw git" framing.

## Setup (one-time, per project)

If the project doesn't yet have logmind:

```bash
pip install logmind
logmind init               # scaffolds docs/, AGENTS.md, GH Actions, .gitignore block, merge drivers + post-merge hook (v0.3.0+), commit-msg hook (v0.6.16+)
logmind doctor             # confirm clean install
```

**Unified SkDD install (v0.6.8+)**: one command bootstraps logmind AND clud-bug
together via the `--with-skdd` flag:

```bash
pip install logmind
logmind init --with-skdd   # subprocesses to `npx clud-bug init` after logmind setup
```

Behavior:
- Default (no flag): logmind init unchanged — Python-only install.
- With `--with-skdd` + `npx` on PATH: subprocesses to `npx --yes clud-bug@latest init` after logmind setup completes. Streams output (not silenced).
- With `--with-skdd` + no `npx`: emits a clear warning with the recovery command, exit code 0 (logmind side succeeded).
- Subprocess failure (non-zero, OSError, 5-minute timeout): warning surfaced; logmind init still succeeds — clud-bug is an additive layer.
- **Anti-loop guarantee**: `--with-skdd` only goes one level deep. `logmind init --with-skdd` invokes `npx clud-bug init` (NOT `clud-bug init --with-skdd`), and v0.6.33's mirror in clud-bug does the reverse. No mutual recursion.

The flag name describes the BUNDLE TARGET (the SkDD toolchain), not a specific tool — so as the toolchain grows beyond logmind + clud-bug, the same flag stays.

## Don'ts

- **Don't run `git add`, `git commit`, or `git push` for changes that
  carry a decision.** `logmind log` is the commit primitive — it handles
  all three in one step. Running them manually either bypasses the
  logging entirely or splits the work across separate commits, both of
  which lose the value of having the reasoning attached to the code.
  The `commit-msg` hook (v0.6.16+) will warn (or reject in strict mode)
  substantive raw `git commit` calls as an additional guard.
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
- **Don't ignore `logmind doctor` PATH-conflict warnings (v0.6.16+).** If
  doctor exits non-zero with `Stack status: DRIFT` due to a PATH-resolution
  mismatch, the shell-resolved `logmind` binary is a different version than
  the running process — hooks written by one version may not match what the
  other expects. Fix the PATH / pyenv config before continuing.
- Don't log every tiny edit. The 20-line rule is a guideline; use judgement.
- Don't write the decision after the fact in past tense for trivial code.
- Don't reword a decision someone else already logged — link or extend it.
- Don't bypass the auto-commit (`--no-commit`) unless you know the project's
  branch protection requires it.
