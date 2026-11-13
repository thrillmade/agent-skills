---
version: "1.2.3"
digest: "25c17cc88e7b"  # is your copy current? github.com/thrillmade/thrill-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/thrill-skills"
name: reviewing-design-work
description: |
  Entry-point dispatcher for REVIEWING or CRITIQUING design work — a PR that touches UI code, a rendered surface or screenshot, a Figma handoff, or a design spec. Routes the review through ordered lenses: code and markup rules first (web-interface-guidelines-review), then rendered-surface lenses (design-system-consistency, frontend-a11y, visual-polish), then the opinionated bar (designing-elite-ui), then the house stance (thrill-design) when the work is that house's, and the copy lens (writing-interface-copy, writing-marketing-copy and defining-a-voice, in the prose pass) — with routing rules for when the browser-driven design-critic pass fires (per orchestrating-elite-agent-qa). Use when the task is judging existing design output; for building a system load designing-a-design-system; for consuming one load consuming-a-design-system.
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
- Critiquing a rendered surface or screenshot (every theme and mode).
- Reviewing a design spec or a Figma → code handoff before the build lands.
- Running the design-critic gate on a slice (see [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md)).

## When NOT to use

- **Building a design system** (tokens, scales, palettes, naming) — load
  [designing-a-design-system](../designing-a-design-system/SKILL.md), not this dispatcher.
- **Consuming a design system** (wiring an existing token set into a product) — load
  [consuming-a-design-system](../consuming-a-design-system/SKILL.md).
- Pure logic / backend review with no design surface.

## Lens order

Run the lenses in this order **within a review session**. (In clud-bug's pipeline the
code and design lenses are *independently gated passes*, so this order
sequences a reviewer's work and findings, not the passes.)

1. **Code + markup lens — [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md).** The opinionated rule set
   (WIG, Material 3, Radix) plus token-driven contrast/typography/spacing rules: APCA-preferred
   contrast cross-checked with WCAG 2.2 AA, atomic typography class, token-not-raw-hex,
   labels per writing-interface-copy, the focus-ring contract, the 24 CSS px interactive floor. Findings
   cite rules, not vibes. **REQUIRED BACKGROUND:** [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md).
2. **Rendered-surface lenses — on screenshots and capture in every theme and mode.** Four lenses judge the
   render itself:
   - **[design-system-consistency](../design-system-consistency/SKILL.md)** — token / scale / color-discipline drift visible on
     the render, not just the source line.
   - **[frontend-a11y](../frontend-a11y/SKILL.md)** — contrast ratios, focus visibility, tap targets, semantics, and
     motion on the rendered surface, in every mode.
   - **[visual-polish](../visual-polish/SKILL.md)** — alignment, optical centering, spacing rhythm, glyph/pattern
     quality, state coverage, theme parity ("fine but not elite" counts).
   - **[motion-continuity](../motion-continuity/SKILL.md)** — state changes, judged in motion, never from stills.

   **REQUIRED BACKGROUND:** the four above.
3. **Opinion lens — [designing-elite-ui](../designing-elite-ui/SKILL.md).** The concrete elite / Figma-grade bar
   (one-axis color, gated contrast, subtraction, on-grid sizes, every mode), after the
   objective lenses. **REQUIRED BACKGROUND:** [designing-elite-ui](../designing-elite-ui/SKILL.md).
4. **House stance last — when the work is that house's.** Apply the L2 stance the
   work belongs to — [thrill-design](../thrill-design/SKILL.md) for Thrill's; it leans
   on the bar where the bar leaves room and never overrides an objective finding.
   Skip for anyone else's work.
5. **Copy lens — [writing-interface-copy](../writing-interface-copy/SKILL.md) for interface strings, [writing-marketing-copy](../writing-marketing-copy/SKILL.md) for page copy, both under [defining-a-voice](../defining-a-voice/SKILL.md)**; never the design pass (table below).

Each lens judges against the color / type / spacing math in Cross-references' L0 primitives, which it does not re-derive.

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
| PR changes a visual surface (component, layout, styles, theme) | Code lens **and** rendered lenses, with [designing-elite-ui](../designing-elite-ui/SKILL.md), then any house stance, after the objective lenses; the rendered pass is browser-driven — screenshots in every mode, states exercised — per [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) (**REQUIRED BACKGROUND** for orchestrating that gate). |
| Design spec / Figma handoff, **no code yet** | [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md) applies to the spec; [designing-elite-ui](../designing-elite-ui/SKILL.md) sets the bar the build must hit; the rendered lenses defer to post-build review. |
| PR ships user-facing strings | The copy lens. In clud-bug all three are `kind: writing`, so they run in the **prose pass**, which always runs, and never in the design pass. |
| clud-bug-installed repo | The 5 `kind: design` skills (four lenses and the house stance: [design-system-consistency](../design-system-consistency/SKILL.md), [frontend-a11y](../frontend-a11y/SKILL.md), [visual-polish](../visual-polish/SKILL.md), [designing-elite-ui](../designing-elite-ui/SKILL.md), [thrill-design](../thrill-design/SKILL.md)) run as the separate **design pass**, never inline with the code review, and **only when the repo opts in**: the design pass is listed in `review.passes` in `.clud-bug.json`, at least one design skill applies to the diff, and the trigger is a pull request. Installation alone never fires the pass, and design findings are advisory unless the repo marks that pass blocking. |

## System-specific layers

These lenses are generic; an L2 stance composes on top rather than replacing them.
[thrill-design](../thrill-design/SKILL.md) is one house's (lens 4). [udts-review](../udts-review/SKILL.md) is one
system's (incubating): a parity marker pointing at udts, not loadable guidance yet.

## Cross-references

- **L0 primitives:** [oklch-color-space](../oklch-color-space/SKILL.md), [apca-contrast](../apca-contrast/SKILL.md), [wcag-contrast](../wcag-contrast/SKILL.md),
  [palette-relationships](../palette-relationships/SKILL.md), [chroma-harmonization](../chroma-harmonization/SKILL.md), [type-scale](../type-scale/SKILL.md), [line-height-grid](../line-height-grid/SKILL.md),
  [token-naming-conventions](../token-naming-conventions/SKILL.md), [component-sizing-principles](../component-sizing-principles/SKILL.md),
  [empirical-design-principles](../empirical-design-principles/SKILL.md), [usability-heuristics](../usability-heuristics/SKILL.md), [motion-continuity](../motion-continuity/SKILL.md).
- **L0 critic lenses:** the copy lens's three, [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md), [design-system-consistency](../design-system-consistency/SKILL.md),
  [frontend-a11y](../frontend-a11y/SKILL.md), [visual-polish](../visual-polish/SKILL.md), [designing-elite-ui](../designing-elite-ui/SKILL.md); and [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md)
  (rendered-pass gate).
- **L1 siblings:** [designing-a-design-system](../designing-a-design-system/SKILL.md), [consuming-a-design-system](../consuming-a-design-system/SKILL.md).
- **L2 stances:** [udts-review](../udts-review/SKILL.md) (incubating), [thrill-design](../thrill-design/SKILL.md).
