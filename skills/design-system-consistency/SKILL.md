---
version: "1.0.1"
digest: "c4adcac2a7fb"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: design-system-consistency
description: >-
  Use when judging whether a RENDERED surface obeys its own design system —
  screenshots or a live page plus the computed styles behind them — as the drift
  lens of a design review. Owns: establishing what the system actually declares
  before judging anything, off-token and right-value-wrong-role values, off-scale
  spacing and type, hand-rolled re-implementations of system components, and
  whether a mode (dark, forced-colors, density, a second brand) has a token path
  at all. Judges drift, not correctness of the scales themselves — those live in
  spacing-system, type-scale, line-height-grid, token-naming-conventions,
  component-sizing-principles. Cite when a review calls a value wrong with no
  system on disk to be wrong against, or passes a hardcoded value because it
  happens to equal the token.
kind: design
applies_to:
  paths: ["site/**", "app/**", "**/site/**", "**/app/**", "**/components/**", "**/ui/**", "**/styles/**"]
  extensions: [".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".css", ".scss"]
---

# Design-system consistency

The drift lens on the **rendered** surface: does what shipped obey *this* system. Drift is
a relation, so it needs both things on disk — the render, and the system it should match.
Without the second there is no drift, only preference, and saying so is the finding.

## When to use

- Judging a rendered surface against the project's tokens, scales and declared stance.
- A PR adds or restyles UI in a codebase that already has a token layer.
- Auditing a surface that "looks right" for values that bypass the system.

## When NOT to use

- **No system on disk.** File one finding — the system is undeclared — and stop. Per-value
  opinions against nothing are taste wearing a uniform.
- **Designing the scale rather than judging against it** —
  [spacing-system](../spacing-system/SKILL.md), [type-scale](../type-scale/SKILL.md) and
  [token-naming-conventions](../token-naming-conventions/SKILL.md) own what a well-formed
  scale *is*.
- **On-system but badly executed** — [visual-polish](../visual-polish/SKILL.md). Two legal
  steps that read identically are a craft finding, not drift.
- **The pairing fails a contrast or target threshold** —
  [frontend-a11y](../frontend-a11y/SKILL.md). Token-correct and inaccessible is a real
  state, and theirs.

## Establish the reference before judging

1. **Find the token source and name it in the review** — DTCG JSON
   ([dtcg-format](../dtcg-format/SKILL.md)), custom properties on `:root` and the theme
   selectors, a Tailwind theme, a `theme.ts`. Read the computed style on the rendered
   node, not only the diff: that is where an inherited or overridden value shows.
2. **Find the declared stance** — which hue is reserved for destructive or critical, which
   dimension varies within a role, which density mode is in force.
   [designing-elite-ui](../designing-elite-ui/SKILL.md) describes a well-formed stance:
   one role, one meaning, one variation axis. **Read the stance; do not supply one.** Where
   a system never wrote one down, that is the finding, filed once — not one finding per hue
   you would have picked differently.
3. **Find a known-good sibling surface** and compare against it. A Figma frame is a
   proposal; the tokens on disk are the system, and where the two disagree that is itself
   the finding.

## What drift looks like on a render

1. **Off-token value.** A literal colour, spacing, radius, shadow or font-size where a
   role token exists. Recognise it in the computed style (a hex or px with no custom
   property behind it), in arbitrary utilities (`bg-[#f5f5f5]`, `p-[13px]`), and in inline
   `style`. The render is identical today and diverges at the first theme, density or
   brand change. Fix: name the token whose **role** matches, not the one whose value does.
2. **Right value, wrong role.** A border token used for text, a surface token on a fill
   that must invert. It looks correct until a mode flips and one element moves the wrong
   way. [token-naming-conventions](../token-naming-conventions/SKILL.md) owns the role
   families and the chain shapes a component token may take.
3. **Off-scale spacing and sizing.** A gap or height that is not a step — recognisable as
   sibling controls sitting a hair apart, or a value that is *nearly* a step.
   [spacing-system](../spacing-system/SKILL.md) owns the steps;
   [component-sizing-principles](../component-sizing-principles/SKILL.md) owns the rungs
   and the rule that siblings share one. Fix: the nearest legal step, named.
4. **Type ramp drift.** A size, weight or line-height off the ramp, or one semantic level
   rendered at two sizes in a single view — measure two same-level headings in the capture.
   [type-scale](../type-scale/SKILL.md) owns the ratio and rounding;
   [line-height-grid](../line-height-grid/SKILL.md) owns the UI-versus-prose tracks.
5. **Colour discipline — observe, then judge.** Hold the surface to the system's stance,
   not yours. Three things are universal: one role does not carry two meanings; a hue
   reserved for destructive or critical is not spent on decoration; an accent in no palette
   is drift even when it is pretty. Cite the construction skills when proposing a
   replacement — [oklch-color-space](../oklch-color-space/SKILL.md),
   [palette-relationships](../palette-relationships/SKILL.md),
   [chroma-harmonization](../chroma-harmonization/SKILL.md).
6. **Re-implementation.** A hand-rolled button, card or input — the finding stands
   whether or not a system component for it exists. Where one exists it's visible as
   subtly different padding, radius, hover or focus ring from its siblings; fix: the
   component, not corrected values. Where none exists, propose it upstream, filed once
   per missing component class — not one finding per hand-rolled instance.

## Every mode needs a token path

Light and dark are both primary and not the whole axis: forced-colors, an
increased-contrast preference, each density mode and any second brand are modes too. The
test is not "does dark look right" but **is there a path** — a mode-aware token every
surface resolves through. A theme written as a `.dark` block of literal values renders
correctly in two modes and has nowhere to put the third.

## Silent failures

- **A hardcoded value that equals its token.** Pixel-identical render, every check green,
  and it stops tracking the token at the next release. The screenshot never shows this;
  the computed style does.
- **A component token pointing straight at a primitive.** Skips the semantic layer,
  renders correctly, cannot be re-themed —
  [token-naming-conventions](../token-naming-conventions/SKILL.md).
- **A new token invented for a one-off.** On-system by construction, so nothing flags it,
  and the catalog grows a synonym for a role it had. Check for an existing role first;
  [semver-design-tokens](../semver-design-tokens/SKILL.md) owns what adding one costs.

## Verification

1. The review names the token source it judged against and quotes a computed value, not
   only a screenshot impression; every drift finding names the token that restores it,
   chosen by role rather than by matching value.
2. Colour findings quote the declared stance or state that none is declared. No finding
   prescribes a hue this lens preferred.
3. Findings belonging to the scale-owning skills, to
   [visual-polish](../visual-polish/SKILL.md) or to
   [frontend-a11y](../frontend-a11y/SKILL.md) were routed, not re-argued here.
4. Each mode the system claims to support was checked for a token *path*, not just for
   looking right in the two captured themes.
5. A token-clean surface gets one line saying so, naming what it was checked against.

## Cross-references

- **REQUIRED BACKGROUND:** [token-naming-conventions](../token-naming-conventions/SKILL.md)
  — role families and chain shapes, without which "wrong role" cannot be argued; and
  [spacing-system](../spacing-system/SKILL.md) with
  [type-scale](../type-scale/SKILL.md) — the two scales most drift lands on.
- **Also cited when proposing a fix:** [oklch-color-space](../oklch-color-space/SKILL.md) ·
  [palette-relationships](../palette-relationships/SKILL.md) ·
  [chroma-harmonization](../chroma-harmonization/SKILL.md).
- **Siblings:** [visual-polish](../visual-polish/SKILL.md) (on-system, badly executed) ·
  [frontend-a11y](../frontend-a11y/SKILL.md) (token-correct, illegible) ·
  [designing-elite-ui](../designing-elite-ui/SKILL.md) (a well-formed stance) ·
  [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md) (the same
  discipline from the diff). **Above:**
  [reviewing-design-work](../reviewing-design-work/SKILL.md) orders the lenses;
  [consuming-a-design-system](../consuming-a-design-system/SKILL.md) is where a repo with
  no token path goes.
## Sources

- [W3C Design Tokens Format Module](https://tr.designtokens.org/format/) — what a token
  file declares and what an alias is; the catalog's reading is
  [dtcg-format](../dtcg-format/SKILL.md).

