---
version: "1.0.2"
digest: "fc49f8cc5029"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: clud-bug-collaboration
description: How Claude Code agents working in a clud-bug-installed repo should interact with the bot's review threads, strict-mode gate, and skill set. Use this skill whenever you're about to push a commit, address a clud-bug PR review comment, edit anything under .claude/skills/, modify .github/workflows/clud-bug-*.yml, or wonder why a PR check is red. Also use when planning work in a repo that has a `clud-bug-review` workflow installed — even if the user didn't mention clud-bug by name.
---

# Working in a clud-bug-installed repo

Clud Bug reviews every PR via `anthropics/claude-code-action`.

## When to use

About to push a commit, address a clud-bug PR review comment, edit anything
under `.claude/skills/`, modify `.github/workflows/clud-bug-*.yml`, or the
`clud-bug-review` check is red and you need to know why.

## When NOT to use

The review already ran clean and neither skills nor the workflow are being
touched. For the org-wide env vars and artifact defaults this skill shares
with logmind, see [token-frugal-tooling](../token-frugal-tooling/SKILL.md).

## Pushing fixes to a clud-bug-reviewed PR

The bot re-reviews within ~2 minutes of a push (`pull_request: synchronize`)
and **resolves its own inline review threads** once the flagged issue is
verifiably fixed in the diff — don't resolve them yourself. A thread that
stays open means the bot judged the issue still open (read its latest
comment) or the resolution call hit a transient API error (re-push).
`required_conversation_resolution` branch protection blocks merge on any
unresolved thread: fix the issue and re-push, never mark it resolved by hand.

## Strict mode

Read `.claude/skills/.clud-bug.json`. `review.strict_mode: true` fails the
check on critical findings, read from the **base ref** so a PR cannot disable
the gate judging it — a change takes effect for PRs opened after it merges to
base.

**An agent MUST NOT change this setting** — not via the config command, not
by editing the file. SPEC §1.6 makes that class of setting a person's to set.
Ask; don't switch it off to get unblocked. A person runs
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
evidence-anchored guidance — name the exact path, the exact pattern to flag,
what to quote, and pair each rule with a bad/good snippet:

```ts
// BAD — interpolated SQL: db.query(`SELECT * FROM u WHERE id = ${id}`)
// GOOD — parameterized:   db.query('SELECT * FROM u WHERE id = ?', [id])
```

## Editing `.github/workflows/clud-bug-*.yml`

`anthropics/claude-code-action` **refuses to run on PRs that modify its own
workflow file** (App token exchange fails with 401) — a guard against PRs
that try to neuter the reviewer or exfiltrate secrets. Bundling a workflow
tweak with other work fails the check *and* leaves your other changes
unreviewed.

Split workflow edits into their own PR: `clud-bug edit-workflow` refuses if
the working tree has non-workflow changes, and branches from `origin/main`,
not HEAD, so unrelated commits can't leak in.

## When the secret is missing

`ANTHROPIC_API_KEY` must be in the repo's Actions secrets. Without it the
guard step fails loudly with an `::error::` annotation — except on bot/fork
PRs where the secret legitimately isn't passed: there it posts a one-line
advisory comment and exits 0 instead of red.

## Reading review comments (v0.6.5+)

Every summary comment opens with a triage line, `Found: N 🔴 / N 🟡 / N 🟣`.
Severity is an emoji prefix per finding:

- **🔴 important** — bug, security, performance, missing test coverage.
  Fails the check in strict-mode repos.
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

Trust the headline on a re-read and skip the collapsed `Reasoning`; expand
only when chasing a finding. Zero findings is the triage line (all zeros)
plus the standard header — no per-finding bullets.

## Agent invocation: `CLUD_BUG_QUIET=1` (v0.6.7+)

From an agent session, set `CLUD_BUG_QUIET=1` or pass `--quiet` / `-q`: each
command emits one `ok <key-value>` line (e.g. `ok updated: @v0.6.11, N
changed`) instead of progress chatter. Errors still hit stderr.

## Cost-control wiring

Wired into every template — you don't invoke it. Override per-repo (e.g.
`MAX_DIFF_BYTES=999999`) with an env var in `clud-bug-review.yml`.

- **Prompt caching** (v0.6.3): the stable prefix (review-prompt, skill
  catalog, base-ref AGENTS.md) auto-caches. Cached input bills at 10% of
  standard within a 5-minute window; the first review in a fresh window
  writes at 1.25×. Check `cache_read_input_tokens` in the result JSON
  (`show_full_output: true`).
- **Byte budgets**: `MAX_COMMENT_BYTES=20000`, `MAX_SKILL_BYTES=4000`,
  `MAX_DIFF_BYTES=5000000`. Too low and that section is silently truncated
  into a **half-review**; a cap hit shows a truncation marker and the bot is
  told to request the omitted hunks.
- **`MAX_THINKING_TOKENS=8000`** (v0.6.8) per turn.
- **Incremental diff** (v0.6.10): a re-review reads only
  `git diff <prior_sha>..HEAD`, located via `<!-- last-reviewed-sha: <sha> -->`
  in the prior comment. Force-push or rebase falls back to full `gh pr diff`.
  ~67% fewer bytes.
- **Two fast paths.** *Workflow-only* PRs (workflow file + an allowlist like
  `AGENTS.md` / baseline skills) skip review entirely — no `max_turns` at
  all. *Trivial* PRs (dependency-bump bot authors, or a <2KB diff touching
  only manifest files) get flat `max-turns=10` on Haiku 4.5, ~⅓ of Sonnet's
  per-token cost. Everything else: classify estimates turns from PR size →
  `max(estimated × 1.2, 15)`, capped at 60, on `claude-sonnet-4-6`.

## Updating clud-bug

`clud-bug-self-update.yml` runs weekly (Mondays 12:00 UTC), opening a PR
when a newer version hits npm; pin one with `pinVersion: "x.y.z"` in
`.claude/skills/.clud-bug.json`. `clud-bug update` runs it on demand:
re-renders workflow templates, refreshes baseline skills from the installed
version, leaves custom and skills.sh skills untouched.

## Verification

The `clud-bug-review` check status is how you know the flow worked — read
its color, don't just push and move on.

- **Green** = ran, found no critical issues, notary-certified (SPEC §4.5); a
  green with no certification is not conformant.
- **Red** = strict mode is on and a critical issue was flagged.
- **Grey (neutral)** = it could not verify what it examined, strict mode is
  off, or it could not run — commonly a fork PR (SPEC §6.5: a fork check is
  neutral, never green). Grey never blocks and never claims a real review —
  read the diff yourself.
- A same-repo bot PR (Dependabot, Renovate) is reviewed too, on a cheaper
  model — a green there is real; read it.
- After a fix push, an inline thread still open past ~2 minutes means the
  bot judged the issue unresolved, not a sync delay.

## Cross-references

- [token-frugal-tooling](../token-frugal-tooling/SKILL.md) — for repos that
  also have logmind.
- [skill-frontmatter-quality](../skill-frontmatter-quality/SKILL.md) —
  frontmatter contract for a custom skill.

## Sources

- https://cludbug.dev
- https://github.com/thrillmade/clud-bug
- https://github.com/thrillmade/agent-skills
