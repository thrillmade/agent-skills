---
name: finding-a-catalog-skill
description: >-
  The directory of the thrillmade/agent-skills catalog — that catalog only,
  not the wider skills.sh ecosystem — naming every skill in it, what each one
  owns, and what it deliberately does not cover. Load it BEFORE authoring any
  rule, convention, checklist, standard, guideline or house style, and before
  saying "there is no skill for this" / "nothing covers X" / "I'll write the
  guidance" — including when the task looks too specific for an existing skill
  to exist, because a repo installs only the subset it subscribed to and
  absence from `.claude/skills/` is not absence from the catalog. Also load
  when choosing which sibling skill to open, when a skill routes you somewhere
  by name, when judging whether a proposed new skill duplicates one that
  exists, and when deciding what a repo is missing.
source: manual
---
# Finding a catalog skill

Every skill in the **thrillmade/agent-skills** catalog, grouped by what it
owns. Generated from `docs/placement-map.json` and gated: add, rename or
delete a skill without regenerating and `validate-skills` fails, so this list
cannot go quietly incomplete the way a hand-kept table does.

**Read it before you write a rule.** Before authoring a convention, a
checklist, a house standard or a "how we do X" doc -- and before saying
"nothing covers this". The catalog is bigger than the set installed in any one
repo, so *not seeing* a skill is not evidence that none exists. Check here
first; that check is one read, and writing the guidance again is not.

**What a line is.** The fragment after each name says what that skill *owns*,
not what it says -- editorial text, gated for presence and length but not for
freshness against that skill's own body. Enough to shortlist two or three;
then open them. A skill you do not have yet:

```
npx skills add https://github.com/thrillmade/agent-skills --skill <name>
```

**What this is not.** Not a listing of your `.claude/skills/` -- a repo holds
only what it subscribed to, plus anything it authored locally -- and not a
view of the wider skills.sh ecosystem. This indexes one catalog.

## Reviewing a pull request
What a review flags, what it lets go, and what a claim has to cite.

- `api-contract-enforcement` — public API shape changes
- `brand-voice-review` — voice in user-facing strings
- `clud-bug-collaboration` — living with the review bot
- `critical-issues-only` — correctness, security, perf only
- `evidence-based-review` — quote the code or cut the claim
- `pii-and-compliance` — PII and secrets in logs
- `respect-existing-conventions` — a review is not a redesign
- `skill-frontmatter-quality` — judging a SKILL.md's frontmatter
- `test-discipline` — test edits that hollow a suite

## Running agents
Handing work out, gating what comes back, surviving a long session.

- `orchestrating-a-multi-agent-run` — start here: the four obligations
- `orchestrating-agent-delegation` — the brief, model tiering, verify
- `orchestrating-elite-agent-qa` — the panel and design-critic gate
- `session-heartbeat` — beats, checkpoints, resuming
- `unattended-operation` — what a handover permits

## The catalog itself
Finding, censusing and authoring skills; decision logging; CLI conventions.

- `curating-a-skill-catalog` — the census rubric and verdicts
- `finding-a-catalog-skill` — this directory
- `logmind` — when and how to log a decision
- `token-frugal-tooling` — quiet flags for the org's CLIs

## Design: start here (L1)
Three entry points. Each routes to the primitives below in work order.

- `composing-a-screen` — laying out a screen
- `consuming-a-design-system` — using a system in a product
- `designing-a-design-system` — building or extending a system
- `reviewing-design-work` — critiquing design output

## Design primitives (L0)
Math and standards any design system can build on. No product opinions.

- `apca-contrast` — Lc targets, the primary model
- `chroma-harmonization` — per-stop cross-hue chroma caps
- `component-sizing-principles` — curated height and icon ladders
- `dtcg-format` — the W3C DTCG interchange file
- `line-height-grid` — two-track line height on grid
- `oklch-color-space` — OKLCH ranges and gamut mapping
- `palette-relationships` — hue-angle palette relationships
- `semver-design-tokens` — SemVer from the value diff
- `spacing-system` — minor+major units, 24px floor
- `token-naming-conventions` — what belongs in a token name
- `type-scale` — modular ratios and rounding
- `wcag-contrast` — ratios, the legal cross-check

## Design review lenses (L0)
Judging the rendered surface -- and the standard it is judged against.

- `design-system-consistency` — rendered drift from the tokens
- `designing-elite-ui` — the visual standard to build to
- `frontend-a11y` — contrast, focus, targets, motion
- `visual-polish` — the fine-but-not-elite lens
- `web-interface-guidelines-review` — the code and markup lens

## UDTS stances (L2)
Parity stubs for skills being authored in tokenomics. Not guidance yet.

- `udts-component-sizing-ladders` — per-density size ladders
- `udts-dtcg-extensions` — namespaced DTCG extensions
- `udts-linter-rules` — machine-enforceable lint rules
- `udts-naming-convention` — the concrete naming convention
- `udts-review` — the system-specific lens
- `udts-semver-defaults` — SemVer policy choices
- `udts-spacing-defaults` — density-mode spacing units
- `udts-token-model` — taxonomy and resolution

## Deprecated (migration window)
Superseded. Each one names its successors; load those, not these.

- `component-sizing` — use component-sizing-principles
- `design-token-naming` — use token-naming-conventions
- `skillforge` — use skill-creator / skill-smith

## Templates
Copy-and-edit scaffolds. They fail the slug check until you customise.

- `conventions-template` — a review-like-me scaffold

## Deliberately not here

A map showing only what is inside teaches you the outside does not exist,
which is the same mistake inverted. These are gaps this catalog knows it has.
Each count is re-measured whenever this file is generated, over every skill's
name and frontmatter description -- the surface that decides whether an agent
finds it. A gap that had since been filled would refuse to render rather than
go on advertising itself:

- **TDD mechanics** -- red before green, one failing test at a time. In the `superpowers` plugin, not here -- `red before green` matches **0** skills.
- **The same discipline under its other name** -- `test-driven` matches **0** skills.
- **Norman's design primitives** -- forcing functions, mapping, the two gulfs -- `forcing function` matches **0** skills.

(Control: `APCA` matches 8, so the probe finds what is there.)

Not being named above is not evidence of absence either. Search `skills/`
before concluding a second time -- and control the search against a term you
know is there, the way the counts above are controlled.

## Sources

- Published by [thrillmot](https://thrillmot.com)
- The catalog: <https://github.com/thrillmade/agent-skills>
- Placement, distribution and subscribers per skill: `docs/placement-map.json`
- The census that promotes, revises and retires these:
  <https://github.com/thrillmade/agent-skills/tree/main/skills/curating-a-skill-catalog>
