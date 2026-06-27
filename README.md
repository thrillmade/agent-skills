# thrillmade/agent-skills

A collection of [skills.sh](https://www.skills.sh)-compatible agent skills published by [thrillmot](https://thrillmot.com).

These skills run inside any agent that loads skills.sh — Claude Code, Cursor, Codex, Cline, Continue, Aider, Windsurf, and others. Each skill is a single `SKILL.md` file with YAML frontmatter declaring when and how the agent should load it.

## Skills in this collection

| Skill | Purpose |
|---|---|
| [`logmind`](skills/logmind/SKILL.md) | Teach agents when and how to log architectural decisions in projects using [logmind](https://logmind.dev). Activates whenever an agent works in a project with `.logmind/config.yml` or an `AGENTS.md`/`CLAUDE.md` mentioning logmind. |
| [`critical-issues-only`](skills/critical-issues-only/SKILL.md) | PR review discipline — flag only correctness, security, and performance issues. Skip style nits and naming preferences. Ships as a baseline with [clud-bug](https://github.com/thrillmade/clud-bug). |
| [`evidence-based-review`](skills/evidence-based-review/SKILL.md) | Every PR review claim must quote the specific code being criticized. No hand-waving, no vague "might cause issues." Cite or delete. Ships as a baseline with clud-bug. |
| [`respect-existing-conventions`](skills/respect-existing-conventions/SKILL.md) | A code review is not a redesign. Don't suggest changes that fight the codebase's established patterns. Match what's already there. Ships as a baseline with clud-bug. |
| [`clud-bug-collaboration`](skills/clud-bug-collaboration/SKILL.md) | How Claude Code agents working in a clud-bug-installed repo coexist with the bot's review threads, strict-mode gate, and skill set. Activates in any repo with a `clud-bug-review` workflow installed — even if the user didn't mention clud-bug by name. |
| [`skill-frontmatter-quality`](skills/skill-frontmatter-quality/SKILL.md) | Review SKILL.md frontmatter for trigger surface, specificity, voice, and `review_mode` completeness. Apply on PRs that add or modify a `skills/*/SKILL.md`. Layers above `validate-skills.yml`'s mechanical checks. Pair with clud-bug as a dedicated-mode skill. |
| [`brand-voice-review`](skills/brand-voice-review/SKILL.md) | Review user-facing strings for brand voice — kill "click here", strip "just"/"simply", catch accidental shouting and title-case drift. Applies to button labels, headings, error messages, marketing copy. Pair with clud-bug as a dedicated-mode skill: each PR gets a brand review alongside the code review. |
| [`api-contract-enforcement`](skills/api-contract-enforcement/SKILL.md) | Flag PRs that change the shape, semantics, or error behavior of a public API without versioning or a migration path. Catches removed fields, renamed parameters, changed status codes, broken pagination, silent enum drift across HTTP/gRPC/GraphQL/SDK/CLI surfaces. |
| [`pii-and-compliance`](skills/pii-and-compliance/SKILL.md) | Catch PII and auth material leaking into logs, error traces, analytics events, URLs, or third-party SDKs. Apply to logging calls, telemetry, error handlers, debug statements, and committed test fixtures. |
| [`test-discipline`](skills/test-discipline/SKILL.md) | Flag the test-edit patterns that hollow out a suite over time: deleted assertions without replacement, mocks that hide the thing being tested, snapshot churn, `.skip`/`.only` left in the diff, time-dependent assertions without frozen time, assertions on internal state instead of observable behavior. |
| [`skillforge`](skills/skillforge/SKILL.md) ✨ | Create or update a reusable agent skill. Use when you notice a repeated pattern, when a workflow should be persisted for future sessions, or when asked to forge/create/scaffold a new skill. **Vendored from [zakelfassi/skills-driven-development](https://github.com/zakelfassi/skills-driven-development) with attribution** — the canonical SkDD meta-skill (the skill that creates skills). MIT, Zak El Fassi. |
| [`conventions-template`](skills/conventions-template/SKILL.md) | Template for a "review like me" skill — captures one maintainer's review conventions (formatting, what to flag, what to ignore). Copy + customize per SPEC v0.5.1 `applies_to.author`: drop into `.claude/skills/conventions-<your-gh-login>/`, set the `author` frontmatter to your login, and clud-bug applies your conventions ONLY to PRs you open. Layers on top of org-wide review-discipline skills. |

## Install

Pick a single skill:

```bash
npx skills add https://github.com/thrillmade/agent-skills --skill logmind
```

Or install the whole collection:

```bash
npx skills add https://github.com/thrillmade/agent-skills
```

Browse on skills.sh: <https://www.skills.sh/thrillmade/agent-skills>

## Consumer patterns — using these skills from your tool

There are two distinct ways a tool can consume a SKILL.md:

**1. Install-pointer (e.g. [logmind](https://logmind.dev)).** The tool ships an `AGENTS.md` that points at the install URL. The *agent runtime* (Claude Code, Cursor, Codex…) installs the skill via `npx skills add`. The tool itself never reads `SKILL.md` — the skill is consumed by the agent, not by the tool. Lightest integration, no runtime fetch.

**2. Fetch + cache + bundled fallback (e.g. [clud-bug](https://github.com/thrillmade/clud-bug)).** The tool itself loads the SKILL.md text into a prompt at runtime — e.g. a bot reviewer needs the skill contents as context for the LLM call. The recommended shape:

```text
1. Try fetching from https://raw.githubusercontent.com/thrillmade/agent-skills/main/skills/<name>/SKILL.md
2. On any failure (network, 404, timeout, non-200) fall back to the bundled copy
   shipped inside the tool's npm/PyPI/etc. package
3. Cache successful fetches to ~/.cache/<tool>/skills/<sha-of-source>.md
4. A scheduled CI job in your tool's repo pulls the bundled copies from
   agent-skills periodically so the offline fallback doesn't drift
```

The bundled copies are the source of truth for the offline path; this repo is the source of truth for the canonical content. Both stay in sync via the scheduled refresh.

Whichever pattern applies, prefer the **collection layout** (`skills/<name>/SKILL.md`) over flat top-level files — that's what skills.sh requires to render the rich page (install count, related skills, security audits).

## Adding a new skill to this collection

1. Create `skills/<name>/SKILL.md` with frontmatter (`name`, `description`).
2. Add a row to the table above.
3. Open a PR.

## Vendored skills (✨ in the table above)

Skills marked with ✨ are **vendored verbatim from upstream authors** — kept here so they install alongside the thrillmade catalog and stay reachable from the same `npx skills add` command, but with original author + spec metadata preserved in the SKILL.md frontmatter.

Current vendored skills:
- `skillforge` — from Zak El Fassi's [skills-driven-development](https://github.com/zakelfassi/skills-driven-development) repo. The canonical SkDD meta-skill (the skill that creates skills). MIT licensed. Vendored at v2.0; we'll sync on his releases.

**Why vendor:** the upstream skill is canonical for its methodology; reimplementing would fragment. Vendoring with attribution keeps users on the canonical artifact + makes it installable through the same channel as the rest of our catalog. Both source-of-truth (upstream) and local-copy (here) stay in sync via periodic refresh PRs.

## License

MIT.

---

## Part of the thrillmade SkDD toolchain

[Skills-Driven Development](https://zakelfassi.com/skdd-skills-driven-development) (Zak Elfassi's methodology) gives you the loop; the thrillmade toolchain ships the parts:

- **[logmind](https://github.com/thrillmade/logmind)** — the *why* behind every change (decision logging as commit primitive); skill-creation + testing + auditing
- **[clud-bug](https://github.com/thrillmade/clud-bug)** — skill-driven PR review at gate time; every finding cites the skill that motivated it
- **[agent-skills](https://github.com/thrillmade/agent-skills)** — public catalog of reusable skills (this repo)
- **[skills.sh](https://skills.sh)** — skill discovery + install

End-to-end agentic auto dev: write skills first → log the *why* → run them against PRs → iterate based on usage. The tools work independently; better together.
