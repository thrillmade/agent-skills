# Integrating a repo with agent-skills

Every thrillmade repo where agents work integrates with this catalog. This guide is the canonical how-to: what a new repo does, how an existing repo adjusts, which parts are automatic today, and which arrive with the steward. The normative wire-format contracts graduate to the protocol SPEC ([protocol#39](https://github.com/thrillmade/protocol/issues/39)); this doc is the operator's manual.

## The model in one minute

`thrillmade/agent-skills` is the org's **skill reservoir** and its **editor**. Relative to it, every repo holds each of its skills in exactly one **posture**:

| Posture | Meaning | Mechanism |
|---|---|---|
| **Subscribed** | Pulled from the catalog; updates flow in as PRs | `skills-lock.json` (hash-pinned, `npx skills add`) or clud-bug's pinned-ref fetch |
| **Published** | Born in your repo, promoted to the catalog | Nomination PR to agent-skills; the editor gate accepts or rejects |
| **Local** | Repo-specific; never leaves | Lives in `.claude/skills/`, marked local-only in your census |

A fourth posture exists but isn't a choice a repo makes — it's what happens when a subscribed repo **leaves the org**:

| Posture | Meaning | Mechanism |
|---|---|---|
| **Departed** | Was Subscribed; the repo has left the org (e.g. handed off to a client) and is no longer read by any org-side automation | None — `skills-lock.json` stays committed as a frozen provenance record, not a live subscription |

A departed repo is not Subscribed, Published, or Local — it was Subscribed and became a frozen copy outside the org's reach. Nothing about the repo changes at the moment it leaves; what changes is that every mechanism above assumes a listener, and this repo no longer is one:

- **No refresh PRs.** Fan-out (today's per-repo crons, and the steward's future org-wide watcher) only reaches repos the org can open PRs against.
- **No census visibility.** The weekly census reads manifests from repos the steward App is installed on; a departed repo isn't among them, so it can't appear in `gap:` / `placement:` / `demotion-candidate:` issues, for better or worse.
- **No migration window.** A deprecation's SUPERSEDED period exists so a *listening* repo has time to re-point before removal. A departed repo doesn't see the marker land and doesn't see the removal either — it just keeps whatever slug it had at handoff, forever.
- **`skills-lock.json` still commits, but changes role.** "Manifests are repo content" still holds — don't delete or gitignore it. It stops meaning "what I'm subscribed to" and starts meaning "what I was given, and at what version": provenance a future paid-subscription product would attach to, not a live pointer this repo's automation still resolves.

What a departed repo **can** still do, unaided: verify currency for itself. `computedHash` in `skills-lock.json` is a plain content hash, computable with nothing beyond the Python standard library (`hashlib`); `thrillmade/agent-skills` is a public repo, so the corresponding file is fetchable with `curl` alone, no org membership or token required. Recomputing the hash and diffing it against the catalog's current copy works from anywhere, on demand — it just never happens automatically, and nothing tells the repo when it's worth doing.

What it **cannot** do: receive a refresh PR, get flagged by the census, or see a migration window. Those all require the org to still be able to read or write the repo, and a departed repo is, by definition, a repo the org no longer touches.

Two rules make the system trustworthy:

1. **Nomination ≠ publication.** A promotion PR passes `validate-skills.yml`, the `skill-frontmatter-quality` review skill, strict-mode clud-bug review, and human approval. The editor can say no.
2. **Manifests are repo content.** Commit `skills-lock.json` and `.claude/skills/.clud-bug.json`. An invisible subscription can't be censused, refreshed, or reasoned about.

## New repo setup — today

`npx skdd init` — a single command bundling toolchain + rulesets +
subscriptions into one onboarding step — is the umbrella installer **being
built** (see [thrillmade/skdd](https://github.com/thrillmade/skdd)); it
is not available yet, and no repo should be told to run it. Until it
ships, a new repo wires in with the commands that actually work today:

```bash
# 1. logmind (decision logging) — separate install, not yet bundled:
brew install thrillmade/tap/logmind   # or: curl -fsSL https://logmind.dev/install.sh | bash
logmind init

#    clud-bug (skill-driven review) — installs the 4 baseline review
#    skills into .claude/skills/ and writes .claude/skills/.clud-bug.json.
#    Add --with-design for the design-critic lenses (installs the kit and
#    flips it to enabled — still needs a browser MCP + allowedTools wired
#    into your review workflow to actually run).
npx clud-bug init

# 2. Subscribe to the catalog skills this repo needs (per-skill opt-in):
npx skills add https://github.com/thrillmade/agent-skills --skill logmind
npx skills add https://github.com/thrillmade/agent-skills --skill brand-voice-review
# ...whatever fits the repo. Browse: https://www.skills.sh/thrillmade/agent-skills

# 3. Commit the manifests (skills-lock.json + .clud-bug.json). Do not gitignore them.

# 4. Org rules: apply the reporulez ruleset so the review gate is enforced.
#    Use the `clud-bug` variant when only the clud-bug-review check needs to
#    gate merges; use the `skdd` variant (the canonical thrillmade-toolchain
#    ruleset — clud-bug + logmind + protocol checks) for repos running the
#    full toolchain; use `baseline` when no producer needs gating at all —
#    per protocol SPEC §7, never require a check nothing produces.
#    (`external` is a deprecated alias for `baseline` — reporulez's own
#    README says so; use `baseline`.)
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

**Shipped:**

- **The registration manifest** — any org registers its own `skdd-steward` App instance from [skdd/docs/skdd-steward-app.md](https://github.com/thrillmade/skdd/blob/main/docs/skdd-steward-app.md); there is no shared, hosted steward, every adopting org runs its own.
- **The weekly editorial cycle** (skill census) runs today: [`skill-census.yml`](../.github/workflows/skill-census.yml) mints the steward App's installation token to read every subscribed repo's manifests + clud-bug's skill-usage data cross-org, an adversarial panel judges, and verdicts land as `gap:` / `placement:` / `promotion-candidate:` / `demotion-candidate:` / `revise:` issues here (top ~5 + digest, weekly). Humans decide; the steward merges nothing.

**Steward roadmap** (post-Marketplace-launch, per the locked sequencing in [protocol#8](https://github.com/thrillmade/protocol/issues/8); contracts in [protocol#39](https://github.com/thrillmade/protocol/issues/39)):

- **thrillmade's own App instance finishing its rename**: the manifest above targets the `skdd-steward` identity for new adopters, but this repo's own workflows still mint from the legacy `THRILLMADE_ORCHESTRATOR_APP_ID` / `THRILLMADE_ORCHESTRATOR_PRIVATE_KEY` secrets and post census issues under `github-actions[bot]` rather than the App's own identity (pending the App being granted Issues R/W) — the cutover for thrillmade's own instance isn't complete yet, even though the manifest and the weekly cycle both already work.
- **Auto-onboarding:** `skdd init` grows the full-magic bundle — toolchain + rulesets + subscriptions + guided App registration + an offer to scaffold an org-local skill reservoir.
- **Skill fan-out:** a catalog change opens refresh PRs on every subscribed repo under the steward's identity, replacing per-repo crons with one org-wide watcher.
- **Invokes, never bypasses:** steward changes are always PRs, always clud-bug-reviewed, always gated by reporulez rulesets, always logged per logmind conventions.

## Existing repo — adjustment checklist

For a repo that predates this system (all current thrillmade repos):

1. **Census yourself.** Inventory every skill-shaped doc (`.claude/skills/`, `.agents/skills/`, `templates/skills/`, stray `SKILL.md`s) with posture + provenance + manifest tracking. The 2026-07-16 reports in [`docs/skill-census/`](skill-census/) are the reference shape.
2. **Register untracked skills.** Anything in `.claude/skills/` absent from both manifests is invisible — add it or classify it local-only in your AGENTS.md.
3. **Commit your lock.** If `skills-lock.json` is gitignored, un-ignore and commit it.
4. **Classify what you authored:** `local-only` / `promotion-candidate` / `already-superseded`. Nominate the candidates via PR here.
5. **Subscribe deliberately.** Check the open `placement:` issues on this repo — the census may already have recommendations for you.
6. **Protect your seams:** never hand-edit subscribed copies (updaters overwrite them); publishers must never let refresh automation write their shipped source (e.g. clud-bug's `templates/skills/**` — that's an npm release, not a cron); preserve symlink topology (`.claude/skills/` → `.agents/skills/`); automation commits use `[skip-logmind]` or file a decision entry (protocol SPEC §15).

## Am I current?

Answerable from inside your own repo, with no access to this one. Until now it wasn't: `npx skills add` copies a `SKILL.md` wholesale and records a `computedHash` produced by the CLI's own normalisation, and the lock stores no version, ref, commit or date — so a subscriber holding a months-old copy had nothing to compare and nothing told them. The first run of the checker below found 21 of `arlyn-working`'s 23 subscribed skills behind, some by three versions and some since May.

Every `SKILL.md` here now opens with its own content digest:

```yaml
version: "56be4995fc2f"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
```

**The rule, in full, and it is meant to be re-derivable by hand:** normalise CRLF to LF, delete the `version:` line from the frontmatter, `sha256` the remaining bytes, take the first 12 hex characters. Deleting the line before hashing is what makes the value stable — a file's digest does not depend on what its stamp already claimed, so a wrong stamp, a malformed one and a missing one all name the same expected value. Everything else is inside the hash, `description:` included: it is the trigger surface, so a body-only digest would call a rewritten description "current".

The quotes are not decoration. Unquoted, an all-digit digest stops being a string — `766941312459` is a real historical digest of this catalog's own `frontend-a11y`, and `000000123456` parses as octal `42798` and does not round-trip.

**[`docs/skill-versions.json`](skill-versions.json)** publishes `current` plus the full history for every slug. One GET, no auth:

```bash
curl -fsSLO https://raw.githubusercontent.com/thrillmade/agent-skills/main/.github/scripts/skills_current.py
python3 skills_current.py           # run from your repo root
```

Stdlib only, one HTTPS GET, reads nothing but your own files — no git, no lock, no `npx`. It finds skills under **both** `.agents/skills` and `.claude/skills`, counting a symlink and its target once, because neither root is a safe default: across the repos here `.agents/skills` exists in three of twenty and `.claude/skills` in twelve, and where both exist the second is usually symlinks into the first.

Verdicts are `current`, `STALE n`, `DIVERGED`, `unpublished` (a version this catalog carries that isn't what `main` publishes — a branch build, so you are not behind), `mirrored` (authored elsewhere; this catalog only mirrors it and is not the authority), `retired`, and `local-skill` (not a catalog slug, so nothing is said about it). It exits `0` current, `1` stale-or-diverged, and **`2` whenever it examined nothing** — an unreadable index, an empty index, a root that isn't there. A run that looked at nothing reports success exactly as loudly as one that looked at thirty files, which is the failure this whole mechanism exists to remove.

**What is checked, and what isn't.** Each `current` is recomputed from the file on disk by `validate-skills` on every pull request, so it cannot drift from the tree. The **history** rows are derived from git, and `validate-skills.yml` checks out at depth 1, so CI cannot recompute them; nothing gates them. That is most of the index by row count, and the index carries the split — and the exact count — in its own `verification` block rather than leaving you to assume. Regenerate them in a full clone with `.github/scripts/gen_skill_versions.py --write`, which enumerates from `refs/remotes/origin/*` — exactly what a fresh clone has, so anyone can reproduce the output.

`version:` is **enforced when present, not required**, and it is not in the SPEC's frontmatter table at all. That is the sanctioned way to add one: protocol SPEC §2.1 says an unrecognised key "MUST NOT cause a failure" and MUST round-trip unchanged, "so the schema can grow without every consumer being upgraded first". Requiring it would be the unsanctioned half. The same table already marks `source` REQUIRED against **0 of 49** adopters in this catalog (control: `kind` has 5) — the catalog already diverges from the owner it cites, and declaring a second required key from inside it would widen that rather than close it. Ratification is [protocol#39](https://github.com/thrillmade/protocol/issues/39)'s to grant.

**Pinning, if you want an exact answer instead of a comparison.** `npx skills add thrillmade/agent-skills#<sha>` records the ref in your lock, so a later install is reproducible. That works today and costs this catalog nothing — but it reaches only repos that have a lock (four of the twenty here), which is why the index exists rather than a lock convention.

**This is pull-only.** It makes staleness *knowable*, not *known*: nothing here opens a PR in your repo, and this catalog still does not know who its subscribers are — [`placement-map.json`](placement-map.json) carries an empty `subscribers` list on most entries. Run the checker, or wire it into your own CI.

### The placement map

[`docs/placement-map.json`](placement-map.json) is the per-skill ground truth the census reads as **signal 1**. For every skill in `skills/`, it records `authoring_home` (`catalog` / `repo-mirrored:<repo>` / `undecided`), `distribution` (`default-on` / `opt-in` / `catalog-only`), and `subscribers` (the repos that actually pull it) — the verdicts a prior editorial round already reached, so each new census cycle starts from a baseline instead of re-litigating placement from zero.

Divergence from live state — a repo's `skills-lock.json` or `.clud-bug.json` subscribing to something the map marks `catalog-only`, or authoring a copy of something the map homes at `catalog` — isn't silently reconciled. It *files* a placement verdict: the census raises it as a `placement:` issue for a human to resolve, either by correcting the repo or by updating the map.

It also carries the two editorial fields the catalog directory is generated from: `family` (which group the skill is listed under, an id declared in the map's top-level `families` array) and `owns` (a ≤32-byte fragment naming what that skill owns, as it appears in the directory line). Both are **required on every entry**, and that is deliberate: the map is already reconciled 1:1 against `skills/`, so requiring them here means a skill cannot be added without saying where it belongs and what it is for ([#229](https://github.com/thrillmade/agent-skills/issues/229)).

That the catalog publishes a directory **at all** is owned by one test, `tests/test_gen_skill_directory.py::test_this_catalog_publishes_a_directory`, and not by the gate: `validate_skills` has to hold for any tree it is pointed at, so it tolerates a tree that publishes none. Deleting the skill alone is red at the gate (the map still has an entry for the missing dir); deleting the entry too used to be green everywhere, and is now red in the suite CI runs alongside it.

The directory itself — [`skills/finding-a-catalog-skill`](../skills/finding-a-catalog-skill/SKILL.md) — is **generated, never hand-edited**. `validate-skills` re-renders it in process and fails on any difference, so a skill added without regenerating goes red on its own PR. Regenerate with:

```bash
python3 .github/scripts/gen_skill_directory.py --write
```

Prose lives in the generator, not in the SKILL.md. No ceiling is written down anywhere: run `python3 .github/scripts/gen_skill_directory.py` with no arguments and it prints today's headroom, measured by rendering the real tree with synthetic skills appended at the catalog's own density until the reserve binds.

Two things a byte-identical re-render **cannot** catch, because both sides of the comparison agree with each other — so each has its own rule:

- **A retired skill filed as live.** A skill whose `description` opens `SUPERSEDED` (or that carries `superseded_by` / `status: superseded`) must sit in the `deprecated` family. `skillforge` did not, and the directory routed agents to guidance its own author had told them to stop following.
- **A skill missing from `README.md`.** The gate reconciles the README's `skills/<name>/SKILL.md` links 1:1 against the tree — membership only; the purpose column stays hand-written.

And one thing nothing catches, stated plainly because the directory reads as though something did: `owns` is editorial text, so a skill can be rewritten from top to bottom and its fragment will still say what it said before. The rendered header tells the reader that, rather than letting them infer a freshness guarantee nothing makes.

Editing the map is a normal PR through the same gate as any other catalog change — `validate-skills.yml`, strict-mode clud-bug review, human approval. There's no separate authority for it.

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

The authoring-home ruling for the promoted design lenses landed ([clud-bug#243](https://github.com/thrillmade/clud-bug/issues/243) Ruling 2: `catalog`, per [`docs/placement-map.json`](placement-map.json)). Still open: the steward service contract and census cadence details (protocol#39); the org-reservoir template for consumer orgs (skdd roadmap). When those land, this section shrinks further.
