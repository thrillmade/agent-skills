---
name: clud-bug-collaboration
description: How Claude Code agents working in a clud-bug-installed repo should interact with the bot's review threads, strict-mode gate, and skill set. Use this skill whenever you're about to push a commit, address a clud-bug PR review comment, edit anything under .claude/skills/, modify .github/workflows/clud-bug-*.yml, or wonder why a PR check is red. Also use when planning work in a repo that has a `clud-bug-review` workflow installed — even if the user didn't mention clud-bug by name.
---

# Working in a clud-bug-installed repo

Clud Bug reviews every PR via `anthropics/claude-code-action`.

## Pushing fixes to a clud-bug-reviewed PR

The bot reviews on `pull_request: synchronize` (every push). After a push
addressing a prior finding it re-reviews within ~2 minutes and **resolves
its own unresolved inline review threads** where the flagged issue is
verifiably fixed in the current diff — you don't resolve threads manually.
A thread
that stays open means the bot judged the issue still open (read its latest
comment) or the resolution call hit a transient API issue (re-push).

Don't resolve clud-bug threads on its behalf.
`required_conversation_resolution` branch protection blocks merge while
unresolved threads remain, and the fix is "fix the issue and re-push," not
"mark the conversation resolved."

## Reading the `clud-bug-review` check status

- **Green** = it ran, found no critical issues, and a notary certified the
  review happened. A green with no certification is not conformant
  (SPEC §4.5).
- **Red** = strict mode is on and Clud Bug flagged a critical issue.
- **Grey (neutral)** = the review could not verify what it examined, strict
  mode is off, or it could not run — commonly a **fork** PR. Grey never
  blocks and never claims the change was checked, so **review the diff
  manually**. Per SPEC §6.5 a fork check is neutral, never green: a green
  there is a false clean on the one class of change nothing reviewed.
- A **same-repo bot PR** (Dependabot, Renovate) is **not** skipped: the
  hosted App has its own credentials and reviews it normally on a cheaper
  model — a green there means a real review ran; read it.

## Strict mode

Read `.claude/skills/.clud-bug.json`. `review.strict_mode: true` fails the
check on critical findings. It is read from the **base ref**, so a PR cannot
disable the gate judging it; a change takes effect for PRs opened after it
merges to base.

**An agent MUST NOT change this setting** — not via the config command, not
by editing the file. Strict mode decides whether something blocks, and
SPEC §1.6 makes that class of setting a person's to set. Ask; don't switch
it off to get unblocked. A person runs
`clud-bug config set review.strict_mode false`.

## Modifying a clud-bug skill

Skills live in `.claude/skills/<slug>/SKILL.md`. Three groups:

- **Baseline** (`critical-issues-only`, `evidence-based-review`,
  `respect-existing-conventions`) — managed by clud-bug; in-place edits are
  overwritten on the next `clud-bug update`. To customize this repo, write a
  NEW skill rather than mutating a baseline.
- **From skills.sh** — `clud-bug add <source/name>`, tracked in
  `.claude/skills/.clud-bug.json`; `clud-bug refresh` syncs them.
- **Custom** (anything not in the manifest) — yours, never touched by any
  clud-bug command; a new `.md` here auto-loads next PR.

A custom skill needs SKILL.md frontmatter (`name`, `description`; see
[skill-frontmatter-quality](../skill-frontmatter-quality/SKILL.md)) and
evidence-anchored guidance. Generic prose ("be careful with database code")
gets ignored: name the exact path (e.g. `lib/db/queries.ts`), the exact
pattern to flag, what to quote, and pair each rule with a bad/good snippet:

```ts
// BAD — interpolated SQL: db.query(`SELECT * FROM u WHERE id = ${id}`)
// GOOD — parameterized:   db.query('SELECT * FROM u WHERE id = ?', [id])
```

## Editing `.github/workflows/clud-bug-*.yml`

`anthropics/claude-code-action` **refuses to run on PRs that modify its own
workflow file** (App token exchange fails with 401, "Workflow validation
failed") — a security guard against PRs that try to neuter the reviewer or
exfiltrate secrets. Bundling a workflow tweak with other work therefore
fails the check *and* leaves your other changes unreviewed.

Split workflow edits into their own PR: `clud-bug edit-workflow` refuses if
the working tree has non-workflow changes, and branches from `origin/main`,
not HEAD, so unrelated commits can't leak in.

## When the secret is missing

`ANTHROPIC_API_KEY` must be in the repo's Actions secrets. Without it the
guard step fails loudly with an `::error::` annotation explaining how to set
it — except on bot/fork PRs where the secret legitimately isn't passed:
there it posts a one-line advisory comment and exits 0 instead of red.

## Reading review comments (v0.6.5+)

Every summary comment opens with a triage line, `Found: N 🔴 / N 🟡 / N 🟣`.
Severity is an emoji prefix per finding:

- **🔴 important** — bug, security, performance, missing test coverage.
  These fail the check in strict-mode repos.
- **🟡 nit** — style, naming, micro-optimization. Advisory.
- **🟣 pre-existing** — pre-dates this PR. Don't fix here unless the user
  asks; flag a follow-up issue.

Finding shape:

```
🔴 [skill-name]: One-line claim anchored to file:line.
<details><summary>Reasoning</summary>

Explanation with quoted evidence.

</details>
```

On a re-read trust the headline and skip the collapsed `Reasoning`; expand
only when chasing a finding. A review with **zero findings** is that triage
line (all zeros) plus the standard summary header — no per-finding bullets.

## Agent invocation: `CLUD_BUG_QUIET=1` (v0.6.7+)

From an agent session, not interactively, set `CLUD_BUG_QUIET=1` or pass
`--quiet` / `-q`: each command emits one `ok <key-value>` line (e.g.
`ok updated: @v0.6.11, N changed`) instead of progress chatter. Errors
still hit stderr.

## Cost-control wiring

Wired into every template — you don't invoke it. Override per-repo (e.g.
`MAX_DIFF_BYTES=999999`) with an env var in `clud-bug-review.yml`.

- **Prompt caching** (v0.6.3): the stable prefix (review-prompt, skill
  catalog, base-ref AGENTS.md) is auto-cached by the CLI. Cached input bills
  at 10% of standard within a 5-minute window; the first review in a fresh
  window writes at 1.25×. Check `cache_read_input_tokens` in the result JSON
  (`show_full_output: true`).
- **Byte budgets** per run on diff / prior-comment / skill-content:
  `MAX_COMMENT_BYTES=20000`, `MAX_SKILL_BYTES=4000`,
  **`MAX_DIFF_BYTES=5000000`** (above any realistic PR diff, below OOM). Too
  low and that section is silently truncated into a **half-review**; on a cap
  hit a truncation marker appears and the bot is told to request the omitted
  hunks.
- **`MAX_THINKING_TOKENS=8000`** (v0.6.8) per turn.
- **Incremental diff** (v0.6.10): a re-review reads only
  `git diff <prior_sha>..HEAD`, located via `<!-- last-reviewed-sha: <sha> -->`
  in the prior summary comment. Force-push or rebase invalidates the
  ancestry check → falls back to full `gh pr diff`. ~67% fewer bytes.
- **Two independent fast paths — don't conflate them.** *Workflow-only PRs*
  (workflow file + an allowlist like `AGENTS.md` / baseline skills) skip
  review: classify emits `model=$MODEL` then `exit 0` — **no `max_turns` at
  all** — and the job is gated
  `if: needs.paths-check.outputs.is_workflow_only != 'true'`. *Trivial PRs*
  (dependency-bump bot authors, or a <2KB diff touching only
  dependency-manifest files) get flat `max-turns=10` on Haiku 4.5
  (`claude-haiku-4-5-20251001`, pinned), ~⅓ of Sonnet's per-input-token
  cost. *Everything else*: classify estimates turns from PR size
  (files/lines/prior threads) → `max(estimated × 1.2, 15)`, capped at 60, on
  `claude-sonnet-4-6` — not Opus, per Anthropic docs, "Sonnet handles most
  coding tasks well and costs less than Opus".

## Updating clud-bug

`clud-bug-self-update.yml` runs weekly (Mondays 12:00 UTC), opening a PR
when a newer version hits npm; pin one with `pinVersion: "x.y.z"` in
`.claude/skills/.clud-bug.json`. `clud-bug update` runs it on demand:
re-renders workflow templates, refreshes baseline skills from the installed
version, leaves custom and skills.sh skills untouched.

## Cross-references

- [token-frugal-tooling](../token-frugal-tooling/SKILL.md) — for repos that
  also have logmind.
- [skill-frontmatter-quality](../skill-frontmatter-quality/SKILL.md) —
  frontmatter contract for a custom skill.
- https://cludbug.dev · https://github.com/thrillmade/clud-bug ·
  https://github.com/thrillmade/agent-skills
