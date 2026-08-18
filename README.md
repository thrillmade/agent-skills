# thrillmade/agent-skills

A collection of [skills.sh](https://www.skills.sh)-compatible agent skills published by [thrillmot](https://thrillmot.com).

These skills run inside any agent that loads skills.sh — Claude Code, Cursor, Codex, Cline, Continue, Aider, Windsurf, and others. Each skill is a single `SKILL.md` file with YAML frontmatter declaring when and how the agent should load it.

## Skills in this collection

**The catalog has a directory, and it is a skill** — the only kind of artifact that can leave this repo. [`finding-a-catalog-skill`](skills/finding-a-catalog-skill/SKILL.md) is this table's job done as a skill, so an agent in a subscriber repo can see what the catalog covers without opening fifty files. It is generated from [`docs/placement-map.json`](docs/placement-map.json) and gated: add a skill without regenerating and `validate-skills` goes red on your PR. Regenerate with `python3 .github/scripts/gen_skill_directory.py --write`.

**It does not install itself.** Measured: `npx skills update` refreshes the skills a repo already has and never adds one, so each repo opts in once —

```bash
npx skills add https://github.com/thrillmade/agent-skills --skill finding-a-catalog-skill
```

— and from then on every regeneration arrives with a plain `npx skills update`. That is the claim worth making: the one-time `add` is the whole cost, and the map cannot go stale in a repo that has it.

The table below is the same list in long form — it has no byte cap, so it can afford sentences the directory cannot. Its **membership** is gated: `validate-skills` reconciles the `skills/<name>/SKILL.md` links here 1:1 against the tree, so a skill cannot be added without a row and a row cannot outlive its skill. The purpose column is hand-written prose on purpose — [#229](https://github.com/thrillmade/agent-skills/issues/229) proposed generating the table, and generating it from a 32-byte fragment would make it worse in order to make it derived.

| Skill | Purpose |
|---|---|
| [`finding-a-catalog-skill`](skills/finding-a-catalog-skill/SKILL.md) | The generated directory of the whole catalog — every skill, grouped by family, with what each one owns, plus the gaps the catalog deliberately does not cover. Load it before authoring any rule or convention, and before concluding nothing covers something. |
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
| [`orchestrating-a-multi-agent-run`](skills/orchestrating-a-multi-agent-run/SKILL.md) | **L1 dispatcher — start here for orchestration work.** Routes the run's four obligations: hand the work out, gate what comes back, record the decision and clear the automated reviewer, survive time. Carries the four axioms every station in the family assumes, so none of them restates it. |
| [`orchestrating-agent-delegation`](skills/orchestrating-agent-delegation/SKILL.md) | The CTO-as-orchestrator discipline for handing work to subagents — model tiering, the load-bearing agent-brief shape (with a copyable skeleton), trust-but-verify every "done" against the diff, refute-first review panels, design→rule→build separation. The general delegation mechanics beneath [`orchestrating-elite-agent-qa`](skills/orchestrating-elite-agent-qa/SKILL.md)'s UI-quality pipeline. |
| [`session-heartbeat`](skills/session-heartbeat/SKILL.md) | Keeping a session working across a stretch longer than one sitting — the per-beat order (standing before spend), the largest-dispatch threshold instead of a round percentage, the checkpoint's required slots, and resume-as-survivor after a limit or compaction. The temporal-continuity layer under [`orchestrating-agent-delegation`](skills/orchestrating-agent-delegation/SKILL.md)'s dispatch mechanics. |
| [`unattended-operation`](skills/unattended-operation/SKILL.md) | Policy for a session a human explicitly handed over to run **unattended** (often called "night mode", but the trigger is the handover, never the clock) — the handover contract, the reversible-and-invisible boundary on action, "a scheduled wake is never consent", named hard stops, and the handback digest. Layers on [`session-heartbeat`](skills/session-heartbeat/SKILL.md). Not dark mode. |
| [`curating-a-skill-catalog`](skills/curating-a-skill-catalog/SKILL.md) | The skill-census rubric — lifecycle states, the five verdict kinds with evidence standards, the top-5-plus-digest noise budget, and the human-editor gate. Applied weekly by the census workflow; recursive (the rubric censuses itself). |
| [`token-frugal-tooling`](skills/token-frugal-tooling/SKILL.md) | Quick-reference for the org's token-frugal CLI conventions in repos running both logmind and clud-bug — quiet-mode env vars, artifact defaults, agent-mode flags. Detail lives in the per-tool skills. |
| [`skillforge`](skills/skillforge/SKILL.md) ✨ | **Superseded** ([#203](https://github.com/thrillmade/agent-skills/issues/203)) — skill authoring is now split three ways: `skill-creator` owns measurement, `superpowers:writing-skills` owns wording form, and the studio's `skill-smith` agent owns house rules. Kept unchanged during the migration window; new work should load the successors. **Vendored from [zakelfassi/skills-driven-development](https://github.com/zakelfassi/skills-driven-development) with attribution** — the canonical SkDD meta-skill. MIT, Zak El Fassi. |

## Design & design-system skills — three layers

The design catalog is organized in three layers (locked by the CDO; executed in [PR #136](https://github.com/thrillmade/agent-skills/pull/136), decision log: [skill-unification entry](docs/decisions-branches/feat__skill-unification-k0-k1-k3.md); the normative contracts are graduating to the protocol SPEC via [protocol#39](https://github.com/thrillmade/protocol/issues/39)):

- **L0 — universal primitives.** Math, standards, and principles any design system can build on. No product opinions.
- **L1 — purpose dispatchers.** Thin entry points that route an agent (or a human landing cold) to the right L0 primitives and L2 stances for a given mode of work. Start here.
- **L2 — system stances (`udts-*`).** UDTS's opinionated instantiations of the L0 principles. Incubating in `thrillmade/tokenomics`; published here as stubs until stable.

### L1 — start here

| Skill | Purpose |
|---|---|
| [`designing-a-design-system`](skills/designing-a-design-system/SKILL.md) | Dispatcher for **building or extending** a design system — routes through naming → color → non-color families → format/versioning → the elite bar → testing, in build order. |
| [`reviewing-design-work`](skills/reviewing-design-work/SKILL.md) | Dispatcher for **reviewing or critiquing** design output — ordered lenses (code rules → rendered-surface lenses → the opinion bar) with routing rules for when the browser-driven design-critic pass fires. |
| [`consuming-a-design-system`](skills/consuming-a-design-system/SKILL.md) | Dispatcher for **using** a design system in a product — token discipline, composition rules, DTCG install patterns, SemVer-aware upgrades, extend-vs-fork. |
| [`composing-a-screen`](skills/composing-a-screen/SKILL.md) | Entry point for **making** a screen — the composition sequence in dependency order (rank → group → encode → space → lay out → conventionalise → target → clear the floors → defer). Carries the principles nothing else owns: hierarchy, proximity as a between-to-within ratio, measure and column count, alignment axes, progressive disclosure, Jakob's and Fitts's. |

### L0 — universal primitives

| Skill | Purpose |
|---|---|
| [`oklch-color-space`](skills/oklch-color-space/SKILL.md) | OKLCH primitive ranges, hue-angle naming, gamut mapping, and APCACH inverse composition — generate colors *from* a contrast target instead of pick-then-check. |
| [`apca-contrast`](skills/apca-contrast/SKILL.md) | The APCA Lc target table and the APCA-primary / WCAG-cross-check contrast stance. |
| [`wcag-contrast`](skills/wcag-contrast/SKILL.md) | WCAG 2.2 AA rules as the legal baseline cross-check — 4.5:1 / 3:1, point-based size thresholds, focus appearance. |
| [`chroma-harmonization`](skills/chroma-harmonization/SKILL.md) | Per-stop cross-hue chroma caps so multi-hue palettes read equally saturated at every stop. |
| [`palette-relationships`](skills/palette-relationships/SKILL.md) | Hue-angle math for monochromatic → tetradic palette relationships and when each fits the brief. |
| [`type-scale`](skills/type-scale/SKILL.md) | Modular type-scale ratios, the stops-up/stops-down convention, and integer-px rounding rules. |
| [`line-height-grid`](skills/line-height-grid/SKILL.md) | Two-track line-height (`lh-ui` / `lh-prose`) snapped to the spacing grid. |
| [`spacing-system`](skills/spacing-system/SKILL.md) | The two-unit (minor + major) spacing primitive model, ladder derivation, and the WCAG 2.5.8 24 px interactive floor. |
| [`component-sizing-principles`](skills/component-sizing-principles/SKILL.md) | Why control-height and icon ladders are curated, not formula-derived; rung pairing; the WCAG 2.5.8 floor. |
| [`token-naming-conventions`](skills/token-naming-conventions/SKILL.md) | Universal token-naming principles — prefix-loaded, class-derivable names; physical primitive names; theme/density never in the name. |
| [`dtcg-format`](skills/dtcg-format/SKILL.md) | W3C DTCG interchange format — reserved keys, aliases, group inheritance, composites, namespaced extensions. |
| [`semver-design-tokens`](skills/semver-design-tokens/SKILL.md) | SemVer for token releases computed from the resolved-value diff, with snapshot and deprecation discipline. |

### L0 — design-critic lenses (pair with clud-bug's dedicated design review)

| Skill | Purpose |
|---|---|
| [`designing-elite-ui`](skills/designing-elite-ui/SKILL.md) | The elite/Figma-grade visual STANDARD a build designs to and a critic measures against — one-axis color roles, APCA-gated contrast, stable canvas + floating chrome, light and dark both primary. |
| [`design-system-consistency`](skills/design-system-consistency/SKILL.md) | Flag rendered UI drifting from the system's tokens, scale, and color discipline — judges the screenshot, not just the code. |
| [`frontend-a11y`](skills/frontend-a11y/SKILL.md) | Accessibility on the rendered surface — contrast ratios, focus visibility, tap targets, semantics, motion. |
| [`visual-polish`](skills/visual-polish/SKILL.md) | The "fine but not elite" lens — alignment, optical centering, spacing rhythm, state coverage, theme parity. |
| [`orchestrating-elite-agent-qa`](skills/orchestrating-elite-agent-qa/SKILL.md) | The multi-agent QA pipeline that enforces the bar — adversarial reviewer panels, the browser-driving design-critic gate, fresh-case realistic QA. |
| [`web-interface-guidelines-review`](skills/web-interface-guidelines-review/SKILL.md) | The code+markup review lens — WIG/Material/Radix rules plus token discipline, the APCA-primary contrast stance, focus contract, and the 24 px floor. Fires first in `reviewing-design-work`. |

### L2 — UDTS stances (incubating stubs)

Parity markers: each names a `udts-*` skill being authored in `thrillmade/tokenomics` and PR'd here once the UDTS spec stabilizes. Don't load these as guidance yet.

| Stub | Will hold |
|---|---|
| [`udts-token-model`](skills/udts-token-model/SKILL.md) | UDTS's token taxonomy and resolution model. |
| [`udts-naming-convention`](skills/udts-naming-convention/SKILL.md) | UDTS's concrete naming convention (instantiates `token-naming-conventions`). |
| [`udts-dtcg-extensions`](skills/udts-dtcg-extensions/SKILL.md) | UDTS's namespaced DTCG extension schema (extends `dtcg-format`). |
| [`udts-spacing-defaults`](skills/udts-spacing-defaults/SKILL.md) | UDTS's density-mode unit choices (instantiates `spacing-system`). |
| [`udts-component-sizing-ladders`](skills/udts-component-sizing-ladders/SKILL.md) | UDTS's per-density height + icon ladders (instantiates `component-sizing-principles`). |
| [`udts-semver-defaults`](skills/udts-semver-defaults/SKILL.md) | UDTS's SemVer policy choices (instantiates `semver-design-tokens`). |
| [`udts-review`](skills/udts-review/SKILL.md) | UDTS's system-specific review lens (composes with `reviewing-design-work`). |
| [`udts-linter-rules`](skills/udts-linter-rules/SKILL.md) | UDTS's machine-enforceable linter rules. |

### Deprecated (migration window)

| Skill | Superseded by |
|---|---|
| [`design-token-naming`](skills/design-token-naming/SKILL.md) | `token-naming-conventions` (L0) + `udts-naming-convention` (L2). Kept unchanged until tokenomics migrates. |
| [`component-sizing`](skills/component-sizing/SKILL.md) | `component-sizing-principles` (L0) + `udts-component-sizing-ladders` (L2). Kept unchanged until tokenomics migrates. |

Also design-adjacent, listed in the main table above: [`brand-voice-review`](skills/brand-voice-review/SKILL.md) (microcopy voice for user-facing strings).

### Skill census

Org-wide skill inventories feed the editorial cycle (what gets promoted, demoted, revised). Reports live in `docs/skill-census/`: [clud-bug](docs/skill-census/2026-07-16-clud-bug.md) · [logmind](docs/skill-census/2026-07-16-logmind.md) · [tokenomics](docs/skill-census/2026-07-16-tokenomics.md). The census runs weekly via [skill-census.yml](.github/workflows/skill-census.yml) — counters + an AI panel that files verdict issues for the editor; the rubric it applies is [curating-a-skill-catalog](skills/curating-a-skill-catalog/SKILL.md).

## Personalisation templates

These are **copy-and-edit starting points**, not skills you install as-is. Each ships with placeholder frontmatter that fails the SPEC slug check on purpose — copy the directory into your repo, customize, and the bot's log tells you if you forgot to replace a placeholder.

| Template | Purpose |
|---|---|
| [`conventions-template`](skills/conventions-template/SKILL.md) | Scaffold for a "review like me" skill — captures one maintainer's review conventions (what they flag, what they ignore, structural preferences). Copy into `.claude/skills/conventions-<your-gh-login>/SKILL.md`, set the `applies_to.author` frontmatter to your login (per SPEC v0.5.1), customize the body, and clud-bug applies your conventions ONLY to PRs you open. Layers on top of org-wide review-discipline skills. |

## Integrating your repo

**Full guide: [docs/integrating-with-agent-skills.md](docs/integrating-with-agent-skills.md)** — the canonical how-to for any thrillmade repo (and any org adopting the SkDD toolchain).

The short version — every repo holds each skill in one of three postures:

- **Subscribed** — pulled from this catalog (`npx skills add ...` + a committed `skills-lock.json`, or clud-bug's pinned-ref fetch). Updates arrive as reviewable PRs.
- **Published** — born in your repo, nominated here by PR. The editor gate (validate-skills CI, `skill-frontmatter-quality`, strict-mode review, human approval) accepts or rejects — nomination ≠ publication.
- **Local** — repo-specific, never syncs.

New repo, today: `brew install thrillmade/tap/logmind && logmind init` + `npx clud-bug init` (baselines), subscribe to what you need, **commit your manifests**, apply the reporulez ruleset. (`npx skdd init` — one command bundling all of this — is the umbrella installer being built; it isn't available yet.) Existing repo: run the census checklist in the guide (register untracked skills, commit your lock, classify local vs promotion-worthy). A weekly editorial cycle already audits placement, gaps, and staleness org-wide and files its verdicts as issues here; steward-run auto-onboarding and catalog fan-out are the roadmap (protocol#39).

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

## Editing an existing skill

Two gates apply on every PR, and the second one surprises people:

- **`validate-skills`** — frontmatter shape, and a hard size cap on the body with no exception path. [`.github/scripts/validate_skills.py`](.github/scripts/validate_skills.py) owns the limit and the argument for it.
- **`check-prose-retention`** — fails a change that removes content from a `SKILL.md` without saying so. Reformatting is free: rewrapping, reordering, converting `` `spacing-system` `` to a markdown link or back, and de-linking a reference that rotted all score zero. Losing words that were saying something does not. [`.github/scripts/check_prose_retention.py`](.github/scripts/check_prose_retention.py) owns the rule.

The second exists because the first pushes the other way. A catalog-wide link conversion grew three files past the size cap, and all three bought the room by deleting prose — a review rule, an agent-invocation section, and the lines routing `session-heartbeat` to `unattended-operation`. Every check went green, because deleting content is *how* they went green.

Frontmatter, prose and fenced code are scored separately, and a gain in one never pays for a loss in another — otherwise padding the `description:` buys a deleted body section for nothing, since the size cap does not measure the frontmatter at all.

To see what it will say before you push:

```sh
python .github/scripts/check_prose_retention.py
```

**Deleting prose is allowed.** Skills get trimmed, superseded and merged. Declare it: add the row the failure prints to [`docs/prose-removals.md`](docs/prose-removals.md) in the same change. That file explains the rules that keep a row a declaration rather than a standing exemption.

## Vendored skills (✨ in the table above)

Skills marked with ✨ are **vendored verbatim from upstream authors** — kept here so they install alongside the thrillmade catalog and stay reachable from the same `npx skills add` command, but with original author + spec metadata preserved in the SKILL.md frontmatter.

Current vendored skills:
- `skillforge` — from Zak El Fassi's [skills-driven-development](https://github.com/zakelfassi/skills-driven-development) repo. The canonical SkDD meta-skill (the skill that creates skills). MIT licensed. Vendored at v2.0. **Superseded here** ([#203](https://github.com/thrillmade/agent-skills/issues/203)) and filed under `deprecated` in the directory, so no listing routes work to it; the vendored copy stays for the migration window.

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
