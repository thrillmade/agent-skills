---
name: clud-bug-collaboration
description: How Claude Code agents working in a clud-bug-installed repo should interact with the bot's review threads, strict-mode gate, and skill set. Use this skill whenever you're about to push a commit, address a clud-bug PR review comment, edit anything under .claude/skills/, modify .github/workflows/clud-bug-*.yml, or wonder why a PR check is red. Also use when planning work in a repo that has a `clud-bug-review` workflow installed — even if the user didn't mention clud-bug by name.
---

# Working in a clud-bug-installed repo

Clud Bug reviews every PR via `anthropics/claude-code-action`. As another
Claude Code agent working alongside it, here's what to know — these aren't
arbitrary rules, they're the consequences of how the gate is wired.

## When you push fixes to a clud-bug-reviewed PR

The bot reviews on `pull_request: synchronize` (every push). When you push
a commit that addresses an issue Clud Bug flagged in a prior review, the bot
will re-review the PR within ~2 minutes and **resolve its own prior
unresolved inline review threads** where the flagged issue is verifiably
fixed in the current diff. You don't have to resolve threads manually.

If a thread it left isn't auto-resolved after your fix:
- The bot judged the issue still open (read its latest comment for why).
- Or the resolution call hit a transient API issue (re-push to retry).

Don't manually resolve clud-bug threads on its behalf. The check
(`required_conversation_resolution` branch protection) will block merge if
unresolved threads remain — and the right fix is usually "fix the actual
issue and re-push," not "mark the conversation resolved."

## When you read the PR's `clud-bug-review` check status

- **Green** = Clud Bug ran and either found no critical issues OR strict
  mode is off (advisory).
- **Red** = either the action errored OR strict mode is on AND Clud Bug
  flagged a critical issue. Read the latest `## 🐛 Clud Bug review` comment
  on the PR — the body indicates "critical findings" or "clean."
- **Skipped/green-with-comment** = bot- or fork-authored PR (Dependabot,
  Renovate, fork contributor). GitHub deliberately doesn't pass repo
  secrets to those workflows. The bot posts a one-line "Clud Bug skipped"
  comment and exits 0. Review the diff manually.

## Strict mode

Read `.claude/skills/.clud-bug.json` to check this repo's setting.
`strictMode: true` means the workflow check fails on critical findings.
The setting is read from the **base ref**, so a PR cannot disable strict
mode on itself by editing the manifest. Changes take effect for PRs opened
after the change merges to the base branch.

To disable strict mode for a repo, edit the manifest on the base branch:

```json
{ "strictMode": false, ... }
```

## When you modify a clud-bug skill

Skills live in `.claude/skills/<slug>/SKILL.md`. Three groups:

- **Baseline** (`critical-issues-only`, `evidence-based-review`,
  `respect-existing-conventions`) — managed by clud-bug; if you edit them
  in-place they'll be overwritten on the next `clud-bug update`. To
  customize behavior for this repo, write a NEW skill rather than mutating
  a baseline.
- **From skills.sh** — installed via `clud-bug add <source/name>`. Tracked
  in `.claude/skills/.clud-bug.json`. Use `clud-bug refresh` to sync.
- **Custom** (anything not in the manifest) — yours, never touched by any
  clud-bug command. Drop a new `.md` here and it auto-loads on the next PR.

When you write a custom skill, follow the SKILL.md frontmatter format
(`name`, `description`) and write specific, evidence-anchored guidance.
Generic advice gets ignored; rules with examples and quoted-line evidence
move the bot's behavior.

## When you edit `.github/workflows/clud-bug-*.yml`

`anthropics/claude-code-action` **refuses to run on PRs that modify its
own workflow file** (App token exchange fails with 401, "Workflow
validation failed"). This is a security guard against PRs that try to
neuter the reviewer or exfiltrate secrets.

Consequence: if you bundle a workflow tweak with other work, the
`clud-bug-review` check on that PR will fail and not actually review your
other changes either.

The fix: split workflow edits into their own PR. The CLI helps:

```bash
# After editing .github/workflows/clud-bug-*.yml locally:
clud-bug edit-workflow
```

It refuses to run if your working tree has non-workflow changes, so the
isolation guarantee is enforced. Branches from `origin/main`, not HEAD —
unrelated commits on a feature branch can't leak in.

## When the secret is missing

`ANTHROPIC_API_KEY` must be set in the repo's Actions secrets. Without it,
the workflow's guard step fails loudly with an `::error::` annotation
explaining how to set it. (For bot/fork PRs where the secret legitimately
isn't passed, the guard posts a one-line advisory comment and exits 0
instead of failing red.)

## Updating clud-bug itself

`clud-bug-self-update.yml` runs weekly (Mondays 12:00 UTC) and opens a PR
when a newer clud-bug version is published to npm. Pin to a specific
version by adding `pinVersion: "x.y.z"` to `.claude/skills/.clud-bug.json`.

To trigger an update on demand:

```bash
clud-bug update
```

Re-renders workflow templates and refreshes baseline skills from the
currently-installed clud-bug version. Custom and skills.sh-installed
skills are left untouched.

## Where to find more

- Site: https://cludbug.dev
- Repo: https://github.com/thrillmade/clud-bug
- Skill catalog: https://github.com/thrillmade/agent-skills
