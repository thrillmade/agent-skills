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

This project uses [logmind](https://logmind.dev). What counts as a decision, branch routing, `--stage scoped` for unrelated WIP, `logmind doctor`, and the required-reading list ([`docs/timeline.md`](docs/timeline.md), [`docs/decisions.md`](docs/decisions.md), [`docs/file-structure.md`](docs/file-structure.md), `docs/decisions-branches/<branch>.md`) all live in the **`logmind` agent skill** at https://github.com/thrillmade/thrill-skills/tree/main/skills/logmind.
<!-- logmind-end -->

## Project Overview

<!-- Replace with a short description of what this project does. -->

## Development Commands

```bash
python3 .github/scripts/validate_skills.py              # the skill gate — run it before you push
python3 .github/scripts/validate_agents.py              # the agent-role gate
python3 .github/scripts/gen_skill_directory.py --check  # the generated directory skill is current
python3 .github/scripts/gen_skill_versions.py --check   # every version-history row was published
python3 .github/scripts/stamp_versions.py --check       # every version/digest/origin stamp matches
python3 .github/scripts/check_prose_retention.py        # no undeclared prose removal
logmind check-links                                     # every markdown link resolves
logmind check-decisions                                 # changed code needs a decision entry (the check prints its own rule)
pytest tests/ -q                                        # the gates' own regression guard
logmind log "…" -r "…" -a "…" -i "…"                    # the commit primitive (see above)
```

The validator runs in about a second. The suite takes minutes: most of its wall clock is the
two mutation files (`test_prose_retention_mutations.py`, `test_skill_directory_mutations.py`),
which each run the real suites in a subprocess once per mutation — that is what makes "this
guard can fail" a fact rather than a claim, and it is worth the wait. Run the fast subset while
iterating —
`pytest tests/ -q --ignore=tests/test_prose_retention_mutations.py --ignore=tests/test_skill_directory_mutations.py`
— and the whole thing before you push. **Neither the validator nor the suite is optional before opening a
PR** — CI runs both, unconditionally. (No test count or duration is quoted here on purpose: a
hand-kept number with no gate reads as true until one quietly isn't. Run it and read the
output.)

Each `--check` generator has a `--write` that repairs its own staleness; never hand-edit a
stamp or the directory. `check_prose_retention.py` and `gen_skill_versions.py` read git history,
not the working tree, so an agent that may not commit runs them in a scratch clone with its changes
committed there; "0 changed" on a change that touched skills is a failed run. Locally
`logmind check-decisions` reads only staged changes; CI runs the same rule on the PR diff,
excluding `docs/` and every `*.md`.
`logmind log` commits and stages the whole tree by default; an agent that may not commit drafts
the entry with `logmind log --no-commit` and reports it.

## Changing a skill here

This catalog's own rules for writing a skill. The authoring craft lives in the `skill-smith`
agent (`.claude/agents/skill-smith.md`), which is generic and obeys whatever repo it works in;
this is what it finds here.

- **Upstream.** This repo, `thrillmade/thrill-skills`, is the origin every skill's `origin` field
  names. A change to an installed copy is made here, by PR into `dev`, with the research behind
  it in the PR body.
- **Placement.** A new skill gets its row and family in `docs/placement-map.json` before it is
  written; then `python3 .github/scripts/gen_skill_directory.py --write` regenerates
  `finding-a-catalog-skill`. The README's catalog section owns why.
- **House shape.** Re-measure it (`grep -h '^## ' skills/*/SKILL.md | sort | uniq -c | sort -rn`).
  At the time of writing: `## When to use` / `## When NOT to use` / body / `## Verification` /
  `## Cross-references` / `## Sources`, with `**REQUIRED BACKGROUND:** <skill>` marking a hard
  dependency.
- **Provenance.** Each skill's research trail is its `references/sources.md`, and `## Sources` is
  one line linking it. The catalog is mid-migration from inline citation; a planned clean-up
  converts the rest.
- **Frontmatter.** `name` equals the directory name (`^[a-z][a-z0-9-]{0,62}$`); a `description`
  saying when to reach for it; optional `kind` (`rule` | `writing` | `design`); optional
  `applies_to` with `paths` globs and `extensions`. Never `review_mode` — removed from the schema;
  only stale docs mention it. `version`, `digest` and `origin` are written by
  `stamp_versions.py --write`. `validate_skills.py` owns the contract.
- **Size.** The body cap is `SIZE_LIMIT` in `validate_skills.py`, which owns the argument; there
  is no grandfather list and no exception path. The consumer that sets it is clud-bug, which
  reads `SKILL.md` alone: `references/` appears nowhere in its source or templates, and its
  prompt does `head -c $MAX_SKILL_BYTES`. Here, moving prose to `references/` takes it out of
  review.
- **Removing prose** from a `SKILL.md` needs a row in `docs/prose-removals.md`, or the retention
  gate fails it (README, "Editing an existing skill").

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

**Every failing step is real** — including one where the check's own step never ran because a
*setup* step died. A skipped verdict is not a passing verdict. Re-run it or fix it; do not
reason your way past it.

(`check-links` and `check-derived-docs` used to check out the head branch by name, so a run
still in flight when the PR merged died at the checkout step with `A branch or tag with the
name '…' could not be found` — a red that was an artifact, not a verdict. Fixed in #223 by
checking out the SHA instead; if you see that exact message again, it's a regression, not a
known quirk.)

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

### clud-bug review coverage here is intermittent — measure it, don't assume it

The block above describes the mechanism and is regenerated by `clud-bug update` weekly, so
nothing measured belongs inside it. What is measured belongs here. The `clud-bug-review`
check on this repo has had four eras (measured 2026-11-03; probe control-tested against
the known hits below):

- Before #188, mixed — not a clean era: #187 carries a workflow-produced `success` (from
  the then-extant `clud-bug-review.yml` on its own branch) *and* an App-posted `neutral`;
  #150 is an App `failure`; #120 has no run at all.
- `neutral` *"clud-bug review unavailable"* from #188 through at least #269 — the outage era.
- `success` *"clud-bug review — clean (notarized)"* from the App on #274 and #277
  (October) — the App did produce real reviews after the outage.
- **Absent entirely** on #293–#296 (November): no check-run at all. The review *workflow*
  was removed in #117 (the App migration), so a check-run exists only when the App posts
  one — and today it posts nothing here. Strict mode cannot fail on a review that never runs.

While the check is absent, the per-change review gate above is carried entirely by local
panels. Re-check before relying on it, and control-test an empty result against #274's
head SHA (the cleanest known hit) before reading absence as fact:

```bash
gh api repos/thrillmade/thrill-skills/commits/<sha>/check-runs \
  --jq '.check_runs[] | select(.name=="clud-bug-review") | "\(.conclusion) \(.output.title)"'
```
