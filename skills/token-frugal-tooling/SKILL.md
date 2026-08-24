---
version: "1.0.1"
digest: "d04f5bfcbcfe"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: token-frugal-tooling
description: |
  Use in any project that has BOTH logmind (`.logmind/config.yml` or
  `docs/decisions.md`) AND clud-bug (`.github/workflows/clud-bug-review.yml`)
  installed. Quick-reference for the org's token-frugal conventions: env vars,
  artifact defaults, and the "agent mode" flags both CLIs accept. Detail lives
  in the per-tool skills — load `logmind` and `clud-bug-collaboration`
  alongside this one when you actually need to invoke them.
---

# Token-frugal tooling — quick reference

This project uses logmind + clud-bug, both engineered for token frugality.
The defaults below land automatically; this skill is just so you don't
re-learn them every session.

## Agent-mode env vars (set once per command or session)

| Var | Tool | Effect |
|---|---|---|
| `LOGMIND_QUIET=1` | logmind ≥ v0.5.1 | Suppresses progress chatter; emits one `ok <key-value>` line per command. v0.5.3 patched `click.secho` so error/warning output (red/yellow) still prints. `--quiet` / `-q` on the group is equivalent. |
| `CLUD_BUG_QUIET=1` | clud-bug ≥ v0.6.7 | Same pattern for clud-bug CLI (`init` / `update` / `add` / `refresh` / `edit-workflow` / `review-mode`). `--quiet` / `-q` is equivalent. |

Prefer these for agent invocations even when chaining commands — every
command emits a single parseable line, so the next step can grep/parse
without re-running.

```bash
LOGMIND_QUIET=1 logmind log "..." -r "..." --no-push
# → ok logged: <sha> "<title>"

CLUD_BUG_QUIET=1 clud-bug update
# → ok updated: @v0.6.11, N changed, M unchanged
```

## On-disk artifacts default to brief

When you read these files, expect compact format — the legacy verbose
view is opt-in. Both apply org-wide on next regen after a logmind upgrade.

| File | Default since | Shape |
|---|---|---|
| `docs/file-structure.md` | logmind v0.5.0 | Tree capped at **depth 2**. Override per-invocation: `logmind file-structure --max-depth N` or `logmind tree --max-depth 0` for unbounded. |
| `docs/timeline.md` | logmind v0.5.4 | Per month: header with `(N decisions)`, newest entry + `... N-2 more decisions ...` elision + oldest entry. ≤2-entry months show all entries. `logmind timeline --full` recovers the legacy per-decision listing. |

## Reading clud-bug review comments (v0.6.5+)

Every Clud Bug summary comment leads with `Found: N 🔴 / N 🟡 / N 🟣` —
read this line first to triage.

- 🔴 important — bug / security / performance / missing test coverage
- 🟡 nit — style / naming / micro-optimization (advisory)
- 🟣 pre-existing — issue that pre-dates this PR; don't fix here unless asked

Per-finding shape:

```
🔴 [skill-name]: One-line claim anchored to file:line.
<details><summary>Reasoning</summary>

…

</details>
```

On a re-read, you can usually trust the headline and skip the collapsed
`Reasoning`. Expand only when the headline is ambiguous or you want the
evidence trail.

If you see a `### Diagnostics` block before the Skills-referenced footer
(clud-bug v0.6.18+ / 0.0.T): a `head -c` cap fired during the review.
The block names which section truncated and the recovery outcome (e.g.
"recovered with 2x cap", "still truncated"). Treat it as confidence
calibration — if a finding's section was deferred, the verdict on that
section is partial.

## Show + search are agent-friendly (v0.5.2+)

`logmind show` carries three combinable flags for fast scans:

```bash
logmind show --brief --limit 10      # last 10 in one-line form
logmind show --json --limit 20       # parseable JSON
logmind show --json --all            # JSON across main + archive
```

`--json` stdout stays pipeline-clean regardless of `--quiet` — the `ok`
summary line goes to stderr in JSON mode so `logmind show --json | jq`
works without extra plumbing.

## What you don't need to do

- **Don't override clud-bug budgets** (`MAX_DIFF_BYTES`, etc.) unless
  you have a documented reason. Defaults cover 95%+ of real PRs.
- **Don't worry about caching** — clud-bug v0.6.3+ writes its stable
  prefix into the Claude Code CLI's auto-cached system layer. Cached
  input is billed at 10% of standard. Visible via
  `cache_read_input_tokens` in the run JSON.
- **Don't worry about the model** — pinned to `claude-sonnet-4-6`
  (v0.6.11). PR review fits Sonnet's profile; Opus would be ~5× the
  cost per the Anthropic pricing table.
- **Don't worry about fix-push diff cost** — clud-bug v0.6.10 reads
  only the delta since its prior review (handshake via
  `<!-- last-reviewed-sha: <sha> -->` marker in the prior summary
  comment).
- **Don't worry about workflow-only PRs** (clud-bug v0.6.14 / 0.0.W) —
  PRs touching only `clud-bug-*.yml` or `strict-mode-gate/**` skip the
  LLM review entirely. The composite-pin lock-step propagation PRs
  that used to require admin-bypass are now normal merges.
- **Don't worry about dep-bump PRs** (clud-bug v0.6.15 / 0.0.R) —
  dependabot/renovate authors AND small-diff dep-manifest-only PRs
  route to Haiku ($0.80/MTok vs Sonnet's $3) for another ~75%
  reduction on that class.
- **Don't worry about review output length** (clud-bug v0.6.16 / 0.0.X)
  — the prompt has a brevity directive ("Keep total output under
  ~600 tokens"). Per-finding 1-sentence claim + collapsible reasoning
  is the shape; you don't need to ask for short output.
- **Don't worry about prompt drift** (clud-bug v0.6.17 / 0.0.E) — the
  CI golden gate (`test/golden/{must-contain,must-not-contain,byte-budget}.json`)
  fails any PR that drops a load-bearing prompt instruction or
  re-introduces filler patterns. The byte-budget cap is intentionally
  low post-0.0.P (v0.6.20).

## Cross-references

- [logmind](../logmind/SKILL.md) — when / how to log decisions; reading
  prior context; agent-invocation flags.
- [clud-bug-collaboration](../clud-bug-collaboration/SKILL.md) — fix-push
  flow, strict mode, modifying skills, editing the workflow, full comment
  format, full cost-control wiring.
