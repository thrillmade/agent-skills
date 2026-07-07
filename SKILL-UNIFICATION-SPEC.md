# Skill unification spec — design skills across `agent-skills` + `clud-bug` + `tokenomics`

**Status:** Handoff spec. A fresh agent picks this up and executes K0/K1a/K1b/K1c/K3 in `thrillmade/agent-skills`. Other slices (K2 UDTS-specifics, K4 tokenomics-local install, K5 sync mechanism) stay in the tokenomics repo and are NOT this agent's scope.

**Locked by the CDO on 2026-07-07 in the tokenomics session.**

---

## Context

Thrillmade currently has design-related skills scattered across three repos:

1. **`thrillmade/agent-skills`** — 14 design-adjacent skills (color mechanics, token conventions, non-color families, WIG review, brand voice). Public catalog. Source of truth for shared skills.
2. **`thrillmade/clud-bug`** — 4 `kind: design` skills under `templates/skills/design/` (`designing-elite-ui`, `design-system-consistency`, `frontend-a11y`, `visual-polish`) that ship via `clud-bug init --with-design` to power the browser-driving design-critic review pass.
3. **`thrillmade/tokenomics`** — 0 design skills today (only baseline reviewers + `logmind` + `orchestrating-elite-agent-qa`). Incubator for future `udts-*` skills describing UDTS-specific rules.

The 18 existing skills don't have a shared organization scheme, some blend universal principles with UDTS-specific opinions, no entry-point tells an agent which skills apply to which task, and the elite-UI skill's worked example is Burning-Man-specific (obscures the general principle).

This spec unifies them into a coherent three-layer set published to `agent-skills` as the single source of truth.

---

## Doctrine (locked)

**`thrillmade/agent-skills` is the canonical home** for all Thrillmade skills. Public. All design-related skills work together as one cohesive set (not siloed).

**Three-layer architecture:**

- **L0 — Universal principles / math / standards.** Not opinions. Not defaults. Facts an agent needs to reason about design without invoking any particular DS's choices. Examples: OKLCH channel ranges, APCA algorithm, WCAG 2.2 rules, chroma-harmonization algorithm, modular type-scale math, grid-snapping principle.
- **L1 — Purpose dispatchers.** Task-scoped entry points. Thin skills that route the agent to the L0 primitives and L2 stances relevant to a given mode of work. Three of them: `designing-a-design-system`, `reviewing-design-work`, `consuming-a-design-system`.
- **L2 — Opinionated stances (UDTS-specific, `udts-*`).** UDTS's specific taxonomies, defaults, and conventions. Publishes as `udts-*` slugs so consumers/agents can load them without installing UDTS itself. Parallels how WCAG and DTCG publish separately from any single product.

**Project-specific conventions (Burning-Man camp, private product conventions) do NOT publish to agent-skills** — they live in their own repos. The `designing-elite-ui` skill's Burning-Man worked example gets abstracted to a generic product example.

**Bidirectional sync doctrine:** agent-skills is the canonical home; consumers (tokenomics, any downstream repo) pull via `clud-bug add` / `clud-bug refresh` / `npx skills add`. UDTS-specific skills are born in tokenomics `.claude/skills/` for fast iteration and PR'd upstream once stable. The connection must be actively maintained; skills bit-rot fast when one side edits without the other knowing.

---

## Current state audit

### L0-clean skills (leave as-is; may need description tightening)

- `oklch-color-space` — OKLCH primitive ranges, hue-angle naming convention, gamut-mapping, APCACH inverse-composition. Universal.
- `apca-contrast` — Lc target table, algorithm reference, cross-check policy with WCAG. Universal.
- `wcag-contrast` — WCAG 2.2 AA rules, point-vs-pixel sizing, SC references. Universal.
- `chroma-harmonization` — per-stop cross-hue chroma-cap algorithm. Universal.
- `palette-relationships` — hue-angle math for monochromatic/analogous/complementary/triadic/tetradic. Universal.
- `type-scale` — modular ratio math, canonical preset ratios. Universal principle. **Note:** the "default 1.200 for product UI" recommendation is a UDTS-flavored opinion inside an otherwise-clean L0 skill — either soften to "1.200 is a common default" or extract into `udts-type-defaults` (L2).
- `line-height-grid` — two-track (`lh-ui`, `lh-prose`) snap-to-grid formulas. Universal.
- `brand-voice-review` — dead-phrase list, verb-noun rule, ALL-CAPS rule. Universal microcopy principles.

### L0-in-L2-clothing (need SPLITS — extract UDTS specifics)

- **`design-token-naming`** — reads L0 but describes UDTS's exact naming convention (`<prefix>-<role>-<modifier>-<stop>-<state>`, contrast-bound vs free class prefixes, `$extensions.udts.class` requirement). **Split into:**
  - L0: `token-naming-conventions` — general principles for a token naming scheme (kebab-case, prefix-loaded, class derivable from name). No specific convention.
  - L2: `udts-naming-convention` — UDTS's specific instantiation of the above (with the exact prefix map, `$extensions.udts.class` rule, hue-angle primitive convention).

- **`spacing-system`** — mostly universal (two-unit primitive model, minor/major, WCAG 2.5.8 floor) but the "typical values (4, 2, 4) and (8, 4, 16)" are UDTS's densities. **Split into:**
  - L0: keep `spacing-system` with the universal two-unit model + WCAG floor.
  - L2: `udts-spacing-defaults` — UDTS's specific density modes (dense 2/4, balanced 4/8, spacious 4/16) as one worked instantiation.

- **`component-sizing`** — the whole "curated 5-rung ladders (24/32/40/48/56 balanced, 24/28/36/44/52 dense, 32/48/64/80/96 spacious)" is UDTS-specific. Universal is only "curated not formula-derived" + WCAG 2.5.8 floor. **Split into:**
  - L0: `component-sizing-principles` — WCAG 2.5.8 floor + curated-not-formula-derived principle.
  - L2: `udts-component-sizing-ladders` — UDTS's specific rung sets.

- **`dtcg-format`** — mostly L0 (raw W3C DTCG spec) with a UDTS-extensions section (`$extensions.udts`). **Split into:**
  - L0: keep `dtcg-format` clean (raw DTCG only).
  - L2: `udts-dtcg-extensions` — UDTS's specific `$extensions.udts` schema.

- **`semver-design-tokens`** — describes the SemVer bump policy but the specific "pre-1.0 relaxation" is UDTS's choice. **Consider:**
  - L0: `semver-for-design-tokens` — general policy (major/minor/patch based on diff-severity).
  - L2: `udts-semver-defaults` — UDTS's specific pre-1.0 relaxation + snapshot convention.
  - **Optional split** — this one is borderline. Judgment call by the executing agent based on whether the L0/L2 split is genuinely useful.

- **`web-interface-guidelines-review`** — dispatcher-shaped (points at Vercel WIG + Material 3 + Radix + UDTS-specific rules). Mostly L0 with some UDTS naming leakage (`content-*` / `content-primary` role references). **Consider:**
  - L0: keep the dispatcher generic (Vercel WIG + Material 3 + Radix, no UDTS-specific names).
  - L1: the "reviewing-design-work" dispatcher (new — see K1b) can then compose this + the 4 design-critic lenses + UDTS's specific stances.

### To promote from clud-bug → agent-skills (K0 also handles this)

The 4 dedicated design-critic skills currently living in `clud-bug/templates/skills/design/`:

- `designing-elite-ui`
- `design-system-consistency`
- `frontend-a11y`
- `visual-polish`

They stay `kind: design`, `review_mode: dedicated`. clud-bug installs them via `clud-bug init --with-design` — post-promotion, clud-bug should either:
- Pull from agent-skills at install time (like existing `clud-bug add` mechanism), OR
- Continue to bundle its own copies for offline install + sync from agent-skills periodically (the "vendored" pattern described in agent-skills README).

Coordinate with the clud-bug maintainer (thrillmade) — that's a separate PR to `thrillmade/clud-bug` after the skills land here.

---

## Target state

After this work, `thrillmade/agent-skills/skills/` contains:

**L0 primitives (universal):**
- `oklch-color-space`
- `apca-contrast`
- `wcag-contrast`
- `chroma-harmonization`
- `palette-relationships`
- `dtcg-format` (cleaned of UDTS extensions)
- `type-scale` (softened defaults)
- `line-height-grid`
- `spacing-system` (cleaned of UDTS-specific density values)
- `component-sizing-principles` (new; replaces `component-sizing`)
- `token-naming-conventions` (new; extracted from `design-token-naming`)
- `semver-for-design-tokens` (optionally cleaned; judgment call)
- `brand-voice-review`

**L0 design-critic lenses (from clud-bug — dedicated review mode):**
- `designing-elite-ui` (abstracted from Burning-Man example — see K3)
- `design-system-consistency`
- `frontend-a11y`
- `visual-polish`

**L1 dispatchers (NEW — see K1a/b/c):**
- `designing-a-design-system` — entry point for someone building or extending a DS
- `reviewing-design-work` — entry point for review/critique work
- `consuming-a-design-system` — entry point for downstream consumers using a DS

**L2 UDTS-specifics** (NOT this agent's scope — created by tokenomics work, PR'd here later):
- `udts-token-model`
- `udts-interaction-state-recipes` (formerly "chromes")
- `udts-linter-rules`
- `udts-naming-convention` (from the split of `design-token-naming`)
- `udts-dtcg-extensions` (from the split of `dtcg-format`)
- `udts-review`
- Possibly: `udts-spacing-defaults`, `udts-component-sizing-ladders`, `udts-type-defaults`, `udts-semver-defaults`

---

## Work items

### K0 — Audit + split existing skills

1. Read every SKILL.md in `skills/`. Confirm the L0-clean vs L0-in-L2-clothing classification above; adjust if the audit reveals surprises.
2. For each skill flagged for split (see "L0-in-L2-clothing" above): create the new L0 replacement, populate with the universal content only, and remove the UDTS-specific sections. **Do NOT delete the old skill yet** — mark it deprecated in its frontmatter description ("SUPERSEDED by `<new-slug>` — see SKILL-UNIFICATION-SPEC.md") until the tokenomics repo has caught up.
3. Author the corresponding `udts-*` L2 skills as **stubs only** (frontmatter + a one-line "See tokenomics for full content, incubating"). The full content lands from tokenomics later. This is the parity marker so consumers know the L2 skill exists and where it lives during incubation.
4. Promote the 4 clud-bug design-critic skills (`designing-elite-ui`, `design-system-consistency`, `frontend-a11y`, `visual-polish`) from `thrillmade/clud-bug/templates/skills/design/` to `thrillmade/agent-skills/skills/`. Preserve frontmatter (`kind: design`, `review_mode: dedicated`, `applies_to.paths`). Update the agent-skills README table to list them.
5. Open a coordination PR / issue in `thrillmade/clud-bug` announcing the promotion + proposing the sync mechanism (either delete the templates directory and pull from agent-skills at install time, or keep as vendored fallback with periodic sync — coordinate with the clud-bug maintainer to pick).

**Done when:** every skill in `skills/` is either L0-clean or L2-stubbed; the 4 design-critic skills are promoted; the clud-bug coordination PR is open.

### K1a — `designing-a-design-system` dispatcher

**Purpose:** entry point for someone building or extending a design system.

**Content shape:** thin routing skill. Opens with "When to use / When not to use" (the standard SKILL.md shape). Body walks the reader through the pipeline they'll traverse when building a DS:

1. **Naming & taxonomy** — every token gets a stable name; class derivable from the name. `REQUIRED BACKGROUND: token-naming-conventions`. Cite `udts-naming-convention` as one worked example.
2. **Color** — pick a color space (`REQUIRED BACKGROUND: oklch-color-space`); pick contrast targets (`apca-contrast` + `wcag-contrast` cross-check); pick a palette-generation approach (`palette-relationships`, `chroma-harmonization`).
3. **Non-color families** — typography (`type-scale`, `line-height-grid`), spacing (`spacing-system`), component sizes (`component-sizing-principles`). Cite the `udts-*-defaults` skills as worked examples.
4. **Format + versioning** — DTCG interchange (`dtcg-format`), SemVer discipline (`semver-for-design-tokens`).
5. **The elite bar** — cite `designing-elite-ui` as the standard the system must clear.
6. **Testing & maintenance** — snapshot testing, contrast-floor linting, alias-cycle detection.

Frontmatter description explicitly names the mode ("for building or extending a design system") so agents auto-fire it on relevant tasks.

**Done when:** SKILL.md exists at `skills/designing-a-design-system/SKILL.md`; frontmatter passes the SPEC slug check; body ≤ ~150 lines; every REQUIRED-BACKGROUND cross-reference resolves to an existing L0 skill; the README table is updated.

### K1b — `reviewing-design-work` dispatcher

**Purpose:** entry point for someone reviewing/critiquing a design PR or design output.

**Content shape:** dispatcher that composes:
- `web-interface-guidelines-review` (cleaned) — the code+markup review lens
- `designing-elite-ui` — the elite standard the render must clear (design-critic step)
- `design-system-consistency` — token discipline, red reservation, off-scale spacing
- `frontend-a11y` — contrast, focus visibility, tap targets, semantics
- `visual-polish` — alignment, optical centering, spacing rhythm, state coverage, theme parity

Routing rules: for a PR that changes UI code but no visual surface (routing, state), the code lenses fire but not the design-critic. For a PR that changes visual surface (component, layout, styles), both fire — design-critic is browser-driven per `orchestrating-elite-agent-qa`.

Cite UDTS specifics via `udts-review` (once that L2 skill exists) as one worked example of a system-specific review layer that composes with the generic dispatchers.

**Done when:** SKILL.md exists at `skills/reviewing-design-work/SKILL.md`; explicit ordering (code lenses before visual lenses; both before opinion lenses like elite-UI); the README table is updated.

### K1c — `consuming-a-design-system` dispatcher

**Purpose:** entry point for someone using a design system in their product (installing UDTS, or any other DS).

**Content shape:**
1. **Token discipline** — reference tokens via CSS vars, never raw hex/rgb/px. `REQUIRED BACKGROUND: brand-voice-review` for consistent voice + `token-naming-conventions` for name-shape guidance.
2. **Composition rules** — semantic tokens over primitives; component tokens compose from semantic; themes swap role→palette without rewriting.
3. **Install patterns** — how to consume DTCG (`REQUIRED BACKGROUND: dtcg-format`); how tokens flow into CSS variables + framework primitives.
4. **Migration & upgrade** — reading a token-diff report, mapping deprecated tokens, honoring SemVer.
5. **Extending vs consuming** — when to author your own tokens on top vs fork the source system.

Cite `udts-token-model` and `udts-linter-rules` (once L2 stubs exist) as worked examples.

**Done when:** SKILL.md exists at `skills/consuming-a-design-system/SKILL.md`; body ≤ ~150 lines; the README table is updated.

### K3 — Abstract `designing-elite-ui` from Burning Man

The current skill has a worked example that's specific to a Burning-Man hub-editor project ("structures vary hue at locked L/C; power infrastructure is red-reserved; SimCity ghost preview..."). The principles it teaches (one-axis-per-role color, APCA-gated contrast, stable canvas + floating chrome, single type family + mono, alive-before-click interaction, light+dark verified, optical alignment) are universal — but the example makes them read like BM-project rules.

**Task:** rewrite the "Worked Example" section with a generic product example that lands the same principles.

**Suggested example replacements** (pick one; whichever demonstrates the principles cleanest):

1. **Admin dashboard for a SaaS product.** Structures = data tables + cards + tabs (fills vary hue at locked L/C for status columns); "draws" = pending/loading/warning badges (vary hue in warm band, never red); "infrastructure" = destructive-action red (delete confirmation, error banner) is red-reserved. Chrome = collapsible sidebar + top toolbar floating over a stable content canvas. Type = Geist + Geist Mono for IDs/timestamps.

2. **Data-visualization product (a BI-tool style workspace).** Series colors vary hue at locked L/C; error/warning states in the warm band; "critical" = red, reserved. Canvas = the chart surface (px-per-unit locked across selection). Chrome = floating filter panel + centered zoom toolbar. Type = one family + mono for data labels.

Either lands the same principles. Pick whichever reads cleaner in one paragraph.

**Also:** the skill currently mentions "REQUIRED COMPANION: `orchestrating-elite-agent-qa`" — verify that skill exists in agent-skills or link out to tokenomics if it's still project-local (it's in tokenomics's `.claude/skills/` today; may need to promote or reference cross-repo).

**Done when:** the Burning-Man worked example is replaced with a generic product example; the principles being taught (the 8 numbered ones) haven't changed; the "Gotchas That Quietly Break the Bar" table is preserved verbatim; the file passes `validate-skills.yml`.

---

## Out of scope for this agent

- **L2 `udts-*` skill authoring** — UDTS-specific skills (`udts-token-model`, `udts-interaction-state-recipes`, `udts-linter-rules`, `udts-review`, etc.) are born in the tokenomics repo (fast iteration next to the code) and PR'd to agent-skills once stable. This agent creates only the STUBS (frontmatter + placeholder body pointing at tokenomics).
- **K4 — installing `--with-design` on tokenomics itself.** That's a tokenomics-local action; the tokenomics maintainer handles it.
- **K5 — two-way sync mechanism.** CDO decision (manual PR / semi-auto `agent-skills publish` CLI / orchestrator-bot). Not this agent's scope; note it as open in the doctrine section of any dispatcher that touches syncing.
- **Rewriting L0 skills that are already clean.** If the audit reveals an L0 skill has good bones, don't touch it. Only split what's actually mixed.

---

## Verification

After the work lands:

1. **Every SKILL.md passes `.github/workflows/validate-skills.yml`.** Frontmatter (`name`, `description`) present; slug matches directory; no placeholder text.
2. **Every cross-reference resolves.** Grep for `[[...]]` and `REQUIRED BACKGROUND: <slug>` lines; verify each named skill exists.
3. **The 4 promoted design-critic skills work with clud-bug.** Locally: `clud-bug init --with-design` on a test repo pulls from agent-skills (once the clud-bug PR lands) or from local vendored copies.
4. **The L1 dispatchers are auto-firing-friendly.** Each frontmatter description names its mode explicitly ("for someone building..." / "for someone reviewing..." / "for someone consuming...") so an agent's semantic autofire picks the right one.
5. **The README table is up to date.** Every new/promoted skill listed with its purpose.
6. **No skill exceeds ~250 lines.** Skills that grew larger during the split should get factored (extract sections into cross-referenced skills, not inline sub-sections).

---

## Coordination

- **CDO** — final call on any content dispute + on K5 sync-mechanism decision.
- **Tokenomics session** — parallel workstream. Working on Phase X (color foundation v2), Phase U (alpha), Phase T (non-color families), Phase H (agent-substrate). Will draft the `udts-*` L2 skills as those slices land.
- **clud-bug maintainer** — coordinate the promotion + install-time pull vs vendored-fallback choice.

Open a PR against `thrillmade/agent-skills` when the work is ready. Body should reference this spec and enumerate which K-items landed. The `SKILL-UNIFICATION-SPEC.md` file can be **moved to `docs/`** or **deleted after merge** once the work is done — it's a handoff artifact, not a living doc.

---

## References

- Tokenomics plan (source doctrine): `/Users/thrillmot/.claude/plans/you-are-taking-over-nested-quilt.md` (Phase K section).
- clud-bug source of the design-critic system: `thrillmade/clud-bug/src/core/design.ts` + `templates/skills/design/`.
- Existing agent-skills catalog: this repo's `README.md`.
- Consumer patterns for skill fetch/cache/fallback: `README.md` §"Consumer patterns — using these skills from your tool".
