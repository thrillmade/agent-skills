---
version: "be3f7dadd266"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: reviewing-design-work
description: |
  Entry-point dispatcher for REVIEWING or CRITIQUING design work — a PR that touches UI code, a rendered surface or screenshot, a Figma handoff, or a design spec. Routes the review through ordered lenses: code and markup rules first (web-interface-guidelines-review), then rendered-surface lenses (design-system-consistency, frontend-a11y, visual-polish), then the opinionated bar (designing-elite-ui) — with routing rules for when the browser-driven design-critic pass fires (per orchestrating-elite-agent-qa). Use when the task is judging existing design output; for building a system load designing-a-design-system; for consuming one load consuming-a-design-system.
---

# Reviewing design work

You are judging **existing** design output — a PR diff, a rendered surface, a
screenshot, a Figma handoff, or a spec — not building a system and not consuming one.
This is an L1 dispatcher: it orients you, orders the lenses, and points at the skill
that carries each lens's rules. Run the lenses in the order below so objective rule
violations surface before subjective bar judgments, and cheap code reads run before
expensive browser-driving passes. Each station gets a pointer, not a re-teaching — load
the station's own skill to actually run it.

## When to use

- Reviewing a PR that adds or changes UI code, styles, tokens, or theme.
- Critiquing a rendered surface or screenshot (light and dark).
- Reviewing a design spec or a Figma → code handoff before the build lands.
- Running the design-critic gate on a slice (see [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md)).

## When NOT to use

- **Building a design system** (tokens, scales, palettes, naming) — load
  [designing-a-design-system](../designing-a-design-system/SKILL.md), not this dispatcher.
- **Consuming a design system** (wiring an existing token set into a product) — load
  [consuming-a-design-system](../consuming-a-design-system/SKILL.md).
- Pure logic / backend review with no design surface — this dispatcher adds nothing.

## Lens order

Run the lenses in this order **within a review session**. (In clud-bug's pipeline the
code lens and the design lenses are two *orthogonal, independently gated passes* —
SPEC §2.2 — so this ordering governs how a reviewer or orchestrator sequences
the work and prioritizes findings, not a cross-pass scheduling constraint; the
elite-bar-last placement is this dispatcher's guidance.)

1. **Code + markup lens — [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md).** The opinionated rule set
   (WIG, Material 3, Radix) plus token-driven contrast/typography/spacing rules: APCA-preferred
   contrast cross-checked with WCAG 2.2 AA, atomic typography class, token-not-raw-hex,
   verb-noun labels, the focus-ring contract, the 24 CSS px interactive floor. Findings
   cite rules, not vibes. **REQUIRED BACKGROUND:** [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md).
2. **Rendered-surface lenses — on screenshots in light AND dark.** Three lenses judge the
   render itself:
   - **[design-system-consistency](../design-system-consistency/SKILL.md)** — token / scale / color-discipline drift visible on
     the render, not just the source line.
   - **[frontend-a11y](../frontend-a11y/SKILL.md)** — contrast ratios, focus visibility, tap targets, semantics, and
     motion on the rendered surface, in both themes.
   - **[visual-polish](../visual-polish/SKILL.md)** — alignment, optical centering, spacing rhythm, glyph/pattern
     quality, state coverage, theme parity ("fine but not elite" counts).

   **REQUIRED BACKGROUND:** [design-system-consistency](../design-system-consistency/SKILL.md), [frontend-a11y](../frontend-a11y/SKILL.md), [visual-polish](../visual-polish/SKILL.md).
3. **Opinion lens last — [designing-elite-ui](../designing-elite-ui/SKILL.md).** The concrete elite / Figma-grade bar
   (one-axis color, APCA-gated contrast, floating stable chrome, dark verified). It runs
   last because it is the subjective bar; the objective violations should already be
   caught. **REQUIRED BACKGROUND:** [designing-elite-ui](../designing-elite-ui/SKILL.md).

**Rationale:** objective rule violations before subjective bar judgments, so findings land
in severity order — and the cheap code lens runs before the browser-driving rendered
passes.

Each lens judges against the L0 primitives it does not re-derive — the color / type /
spacing math: [oklch-color-space](../oklch-color-space/SKILL.md), [apca-contrast](../apca-contrast/SKILL.md), [wcag-contrast](../wcag-contrast/SKILL.md),
[palette-relationships](../palette-relationships/SKILL.md), [chroma-harmonization](../chroma-harmonization/SKILL.md), [type-scale](../type-scale/SKILL.md), [line-height-grid](../line-height-grid/SKILL.md),
[token-naming-conventions](../token-naming-conventions/SKILL.md), [component-sizing-principles](../component-sizing-principles/SKILL.md).

A finding justified by a **named principle** rather than by what was observed has two more
L0 primitives behind it: [empirical-design-principles](../empirical-design-principles/SKILL.md)
for the falsifiable ones — Gestalt proximity (it carries the ratio a grouping claim must
clear, which the polish lens defers to), Fitts, Hick, Miller, von Restorff — and
[usability-heuristics](../usability-heuristics/SKILL.md) for Nielsen, Norman and
Shneiderman, where the gate is source and edition rather than prediction.

## What fires when

| Situation | What fires |
|---|---|
| PR touches UI code, **no** visual surface change (routing, state wiring, refactor) | Code lens only; the rendered lenses stay silent. |
| PR changes a visual surface (component, layout, styles, theme) | Code lens **and** rendered lenses, with [designing-elite-ui](../designing-elite-ui/SKILL.md) running last after the objective lenses; the rendered pass is browser-driven — screenshots light + dark, states exercised — per [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) (**REQUIRED BACKGROUND** for orchestrating that gate). |
| Design spec / Figma handoff, **no code yet** | [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md) applies to the spec; [designing-elite-ui](../designing-elite-ui/SKILL.md) sets the bar the build must hit; the rendered lenses defer to post-build review. |
| clud-bug-installed repo | The 4 dedicated design lenses ([design-system-consistency](../design-system-consistency/SKILL.md), [frontend-a11y](../frontend-a11y/SKILL.md), [visual-polish](../visual-polish/SKILL.md), [designing-elite-ui](../designing-elite-ui/SKILL.md)) are `kind: design` — they run as the separate **design pass** (SPEC §4.8), never inline with the code review, and **only when the repo opts in**: the design pass is listed in `review.passes` in `.clud-bug.json`, at least one design skill applies to the diff, and the trigger is a pull request. Installation alone never fires the pass, and design findings are advisory unless the repo marks that pass blocking. |

## System-specific layers

These lenses are generic — they compose with a system's own opinionated stance rather than
replacing it. [udts-review](../udts-review/SKILL.md) is one system's worked instantiation (incubating): the
UDTS-specific rules a reviewer checks *on top of* this dispatcher. Treat it as a parity
marker pointing at tokenomics, not as loadable guidance yet.

## Cross-references

- **L0 primitives:** [oklch-color-space](../oklch-color-space/SKILL.md), [apca-contrast](../apca-contrast/SKILL.md), [wcag-contrast](../wcag-contrast/SKILL.md),
  [palette-relationships](../palette-relationships/SKILL.md), [chroma-harmonization](../chroma-harmonization/SKILL.md), [type-scale](../type-scale/SKILL.md), [line-height-grid](../line-height-grid/SKILL.md),
  [token-naming-conventions](../token-naming-conventions/SKILL.md), [component-sizing-principles](../component-sizing-principles/SKILL.md),
  [empirical-design-principles](../empirical-design-principles/SKILL.md), [usability-heuristics](../usability-heuristics/SKILL.md).
- **L0 critic lenses:** [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md), [design-system-consistency](../design-system-consistency/SKILL.md),
  [frontend-a11y](../frontend-a11y/SKILL.md), [visual-polish](../visual-polish/SKILL.md), [designing-elite-ui](../designing-elite-ui/SKILL.md); and [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md)
  (the QA gate that drives the browser-driven rendered pass).
- **L1 sibling dispatchers:** [designing-a-design-system](../designing-a-design-system/SKILL.md), [consuming-a-design-system](../consuming-a-design-system/SKILL.md).
- **L2 stances (incubating):** [udts-review](../udts-review/SKILL.md).
