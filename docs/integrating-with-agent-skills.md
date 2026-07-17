# Integrating a repo with agent-skills

Every thrillmade repo where agents work integrates with this catalog. This guide is the canonical how-to: what a new repo does, how an existing repo adjusts, which parts are automatic today, and which arrive with the steward. The normative wire-format contracts graduate to the protocol SPEC ([protocol#39](https://github.com/thrillmade/protocol/issues/39)); this doc is the operator's manual.

## The model in one minute

`thrillmade/agent-skills` is the org's **skill reservoir** and its **editor**. Relative to it, every repo holds each of its skills in exactly one **posture**:

| Posture | Meaning | Mechanism |
|---|---|---|
| **Subscribed** | Pulled from the catalog; updates flow in as PRs | `skills-lock.json` (hash-pinned, `npx skills add`) or clud-bug's pinned-ref fetch |
| **Published** | Born in your repo, promoted to the catalog | Nomination PR to agent-skills; the editor gate accepts or rejects |
| **Local** | Repo-specific; never leaves | Lives in `.claude/skills/`, marked local-only in your census |

Two rules make the system trustworthy:

1. **Nomination ≠ publication.** A promotion PR passes `validate-skills.yml`, the `skill-frontmatter-quality` review skill, strict-mode clud-bug review, and human approval. The editor can say no.
2. **Manifests are repo content.** Commit `skills-lock.json` and `.claude/skills/.clud-bug.json`. An invisible subscription can't be censused, refreshed, or reasoned about.

## New repo setup — today

Until the steward automates onboarding (see roadmap below), a new repo wires in with four steps:

```bash
# 1. Toolchain: logmind (decision logging) + clud-bug (skill-driven review).
#    Installs the 4 baseline review skills into .claude/skills/ and writes
#    .claude/skills/.clud-bug.json. Add --with-design for the design-critic lenses.
npx skdd init

# 2. Subscribe to the catalog skills this repo needs (per-skill opt-in):
npx skills add https://github.com/thrillmade/agent-skills --skill logmind
npx skills add https://github.com/thrillmade/agent-skills --skill brand-voice-review
# ...whatever fits the repo. Browse: https://www.skills.sh/thrillmade/agent-skills

# 3. Commit the manifests (skills-lock.json + .clud-bug.json). Do not gitignore them.

# 4. Org rules: apply the reporulez ruleset so the review gate is enforced.
#    Use the `skdd` variant when the clud-bug review check has a producer
#    (hosted App or Action); use the `external` variant when it does not —
#    per protocol SPEC §7, never require a check nothing produces.
```

Then point agents at the system: `AGENTS.md` should name logmind (decision logging is REQUIRED for substantive commits) and clud-bug (see the `clud-bug-collaboration` skill), the same shape as this repo's own `AGENTS.md`.

**Which skills should a repo subscribe to?** Start from purpose, not inventory: the three L1 dispatchers (`designing-a-design-system`, `reviewing-design-work`, `consuming-a-design-system`) route to everything design-shaped; the clud-bug baselines arrive automatically. When in doubt, subscribe to less — the weekly census recommends placements (see below).

## What's automatic today vs. what the steward adds

**Automatic today:**

- **Baseline review skills** — every `clud-bug init` installs them; `clud-bug update` refreshes them (single owner: never hand-edit a baseline).
- **Weekly self-updates** — `clud-bug-self-update.yml` + `logmind-self-update.yml` (Monday cron) open version-refresh PRs in each repo.
- **Catalog → clud-bug sync** — a baseline-skill edit on this repo's `main` opens a refresh PR on clud-bug (`notify-clud-bug.yml`), bumping its pinned fetch ref.
- **Release → catalog sync** — logmind's release workflow PRs its skill update here (the `repo-mirrored` authoring pattern).
- **The review gate** — strict-mode clud-bug review + `validate-skills.yml` on every PR touching `skills/`.

**Steward roadmap** (post-Marketplace-launch, per the locked sequencing in [protocol#8](https://github.com/thrillmade/protocol/issues/8); contracts in [protocol#39](https://github.com/thrillmade/protocol/issues/39)):

- The `thrillmade-orchestrator` App renames to **`skdd-steward`** and publishes a registration manifest so any org can run its own instance.
- **Auto-onboarding:** `skdd init` grows the full-magic bundle — toolchain + rulesets + subscriptions + guided App registration + an offer to scaffold an org-local skill reservoir.
- **Skill fan-out:** a catalog change opens refresh PRs on every subscribed repo under `skdd-steward[bot]`, replacing per-repo crons with one org-wide watcher.
- **The weekly editorial cycle** (skill census) runs under the steward: counters read every repo's manifests + clud-bug's skill-usage data → an adversarial panel judges → verdicts land as `gap:` / `placement:` / `promotion-candidate:` / `demotion-candidate:` / `revise:` issues here (top ~5 + digest). Humans decide; the steward merges nothing.
- **Invokes, never bypasses:** steward changes are always PRs, always clud-bug-reviewed, always gated by reporulez rulesets, always logged per logmind conventions.

## Existing repo — adjustment checklist

For a repo that predates this system (all current thrillmade repos):

1. **Census yourself.** Inventory every skill-shaped doc (`.claude/skills/`, `.agents/skills/`, `templates/skills/`, stray `SKILL.md`s) with posture + provenance + manifest tracking. The 2026-07-16 reports in [`docs/skill-census/`](skill-census/) are the reference shape.
2. **Register untracked skills.** Anything in `.claude/skills/` absent from both manifests is invisible — add it or classify it local-only in your AGENTS.md.
3. **Commit your lock.** If `skills-lock.json` is gitignored, un-ignore and commit it.
4. **Classify what you authored:** `local-only` / `promotion-candidate` / `already-superseded`. Nominate the candidates via PR here.
5. **Subscribe deliberately.** Check the open `placement:` issues on this repo — the census may already have recommendations for you.
6. **Protect your seams:** never hand-edit subscribed copies (updaters overwrite them); publishers must never let refresh automation write their shipped source (e.g. clud-bug's `templates/skills/**` — that's an npm release, not a cron); preserve symlink topology (`.claude/skills/` → `.agents/skills/`); automation commits use `[skip-logmind]` or file a decision entry (protocol SPEC §15).

## Publishing a skill (nomination flow)

1. Incubate in your repo's `.claude/skills/<slug>/SKILL.md` until it's stable.
2. Open a PR here adding `skills/<slug>/SKILL.md` + a README table row.
3. Frontmatter requirements: `name` exactly matches the directory; non-empty `description` (**strict YAML** — quote or block-scalar any description containing a colon); one `# Title` H1. Stay within the toolchain frontmatter surface (`name`, `description`, `source`, `review_mode`, `kind`, `voice_scope`, `applies_to{paths,extensions,author}`) — the catalog validator is a compatible superset of clud-bug's parser, so unknown keys are silently dropped by consumers.
4. Write the description for **semantic autofire**: name the concrete situations that should trigger the skill, not the topic area. `skill-frontmatter-quality` reviews this on your PR.
5. After acceptance, decide the **authoring home** with the editor: `catalog` (edits happen here; your copy mirrors) or `repo-mirrored` (you author; a release workflow PRs the catalog, like logmind's). Recorded per skill — divergence is a defect.
6. Your repo flips the skill's posture to subscribed (or keeps authoring under `repo-mirrored`).

## Deprecations and the migration window

When the catalog supersedes a skill (e.g. `design-token-naming` → `token-naming-conventions` + `udts-naming-convention`), the old skill stays with a SUPERSEDED frontmatter marker until downstream migrations land, then gets removed in a major per the catalog's own deprecation discipline (`semver-design-tokens` teaches it — warn in a minor, remove in the next major). If your repo references a deprecated slug, re-point when you see the marker; the census flags stragglers.

## Who enforces what

| Surface | Enforcer |
|---|---|
| Frontmatter validity, slug/dir match | `validate-skills.yml` (this repo's CI) |
| Skill content quality at nomination | `skill-frontmatter-quality` + strict-mode clud-bug review + human editor |
| Merge gates in every repo | reporulez rulesets (required checks; admin bypass is the SPEC-sanctioned escape when a check has no producer) |
| Decision logging on substantive commits | logmind hooks (`[skip-logmind]` escape for trivial/automation commits) |
| Review discipline | clud-bug (hosted App, Action, or local max mode) applying the subscribed review skills |
| Wire formats binding all of the above | the protocol SPEC (`thrillmade/protocol`) |

## Questions this guide will absorb answers to

Authoring-home ruling for the promoted design lenses ([clud-bug#235](https://github.com/thrillmade/clud-bug/issues/235)); the steward service contract and census cadence details (protocol#39); the org-reservoir template for consumer orgs (skdd roadmap). When those land, this section shrinks.
