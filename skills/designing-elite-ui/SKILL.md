---
version: "1.1.3"
digest: "14e5f0314e5e"  # is your copy current? github.com/thrillmade/thrill-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/thrill-skills"
name: designing-elite-ui
description: Visual review — hold the rendered UI to a concrete elite/Figma-grade bar (one-axis color, APCA-gated contrast, subtraction with a test, one source per primitive, on-grid and derived sizes, distinct and consistent copy, floating stable chrome, every theme verified) instead of a vague "looks fine." The STANDARD a design-critic measures against, for tools and content-led pages alike.
kind: design
applies_to:
  paths: ["site/**", "app/**", "**/site/**", "**/app/**", "**/components/**", "**/ui/**", "**/styles/**"]
  extensions: [".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".css", ".scss"]
---

# Designing Elite UI

The design *bar* is the standard; the QA loop is the enforcement (see `orchestrating-elite-agent-qa`). A critic with no encoded bar finds nothing — "looks fine." This skill is the bar: the transferable taste an agent designs *to* and critiques *against*, encoded where both read it (below). **One hand draws the surface** — one `designer` agent, every screen, state and theme; the critic checks, never shapes.

## When to use

- Before a build starts, to encode the one standard builder and critic share.
- As what the design-critic measures a render against in `orchestrating-elite-agent-qa`'s gate.
- Auditing a shipped UI end-to-end against the bar, not one craft nit.

## When NOT to use

- **Judging execution on an already-built surface** — [visual-polish](../visual-polish/SKILL.md); this sets the bar, not the grade.
- **Auditing whether a value is on-system** (token drift, off-scale spacing) — [design-system-consistency](../design-system-consistency/SKILL.md).
- **Measuring a contrast, focus, or target-size success criterion** — [frontend-a11y](../frontend-a11y/SKILL.md) and [apca-contrast](../apca-contrast/SKILL.md) own the pass/fail mechanics.

## The Principles

1. **One semantic role → one meaning → one variation axis.** In each role's band *exactly one* dimension varies and the rest lock. **Reserve a color for ONE meaning only.**
2. **Contrast is gated, not eyeballed.** APCA-check every text-on-fill. Each theme gets its *own* ramp.
3. **Restraint beats richness.** Distinguish by hue-in-band + shape + label. Plain text labels with a subtle active state, not boxy segmented controls; tinted/outline active states over heavy fills.
4. **Type: one text family (plus its mono for data) unless the system pairs a display face by rule.** Mono for data, codes, labels; optical centering (`text-box-trim`); restrained weights.
5. **Tools with a work surface: the canvas is stable; chrome floats.** The surface NEVER reflows or rescales on selection (lock px-per-unit). Panels float *over* it; the toolbar morphs smoothly; a per-context accent.
6. **Interaction feels alive before the click.** Resize and grab cursors, hover highlights, valid/invalid ghost tints, unmistakable active states; state changes move as continuous motion ([motion-continuity](../motion-continuity/SKILL.md)).
7. **Every theme and mode is primary.** Design and verify light *and* dark; check increased contrast and forced colors too ([frontend-a11y](../frontend-a11y/SKILL.md)).
8. **Optical alignment inside the footprint.** Center content to the eye (text trim, icon nudge); the footprint's edge, not the ink, sits on the margin; balance a frame so nothing reads as an afterthought; never ship a clipped focus ring.
9. **Subtract until it breaks.** Retire what carries no meaning. *Test:* name what each element is for; remove it in the render — if no task, meaning or grouping is lost, it goes. Repeat.
10. **Reuse one source.** One primitive per job — one icon rule, one curve per kind of motion, one color per role; a second copy drifts the first time one is tuned. *Test:* one definition per primitive.
11. **On the grid, by rule.** Box sizes and gaps land on the spacing grid ([spacing-system](../spacing-system/SKILL.md)); type sizes come from the type scale ([type-scale](../type-scale/SKILL.md)). Fluid values snap too — `round(clamp(min, pref, max), <step>)` — or land between steps at most widths. A glyph beside text takes its size from that text by one ratio everywhere, then snaps; control heights keep their curated ladder ([component-sizing-principles](../component-sizing-principles/SKILL.md)).
12. **Copy is part of the bar.** Siblings (cards, tabs, heads) differ in first words, share one punctuation and case style, and every sentence-form line has a truthful actor, not a noun list; names, titles, labels are exempt. Copy: [UI](../writing-interface-copy/SKILL.md), [pages](../writing-marketing-copy/SKILL.md).

## Gotchas That Quietly Break the Bar

| Symptom | Cause / fix |
|---|---|
| Popover text clipped / see-through | A `backdrop-filter` ancestor traps even `position:fixed` children → **portal the popover to `<body>`**; opaque frame + inner scroll owns any fade-mask. |
| Pill/toolbar drifts off-center | `left:50%` on an auto-width fixed element caps it to 50vw → wrap in a full-width flex container, center inside. |
| Dark mode looks washed out | Light tokens reused on dark → add explicit dark ramps; re-run APCA. |
| Two controls read "active" at once | Mode and tool both filled with the accent → give the resting one a tinted/outline state. |
| Glyph looks wrong only when rotated | Glyph drawn fixed while footprint swapped → re-orient the silhouette with the rotation. |

## Encode the Bar (so it's enforceable)

**Tokens** in one file (the actual system, not ad-hoc hex), emitted to CSS vars; **a design-system doc** stating domains, axis per role, type rules, chrome model; and **the critic is fed it** ("challenge the render against THIS bar", not "is it nice?") — vague critics pass everything.

## Worked examples (one system each)

**A — a tool: SaaS admin dashboard**, composed from an existing token-driven system; kit gaps go upstream, never inline.
- **Color = OKLCH, three domains, one axis each.** Status fills = cool band, vary **hue**, lock L≈.88/C≈.07. Pending/warning badges = warm band, vary **hue**, NO red. Destructive = **red, reserved**, intensities vary **lightness** only. Monochrome mode → one grey for status fills; red and badges stay.
- **Type:** Geist + Geist Mono; mono for ids, timestamps, metrics.
- **Chrome:** the table/chart canvas never reflows on selection; sidebar, toolbar and detail panel float over it.
- **Interaction:** resize cursors; grab on pan; a ghost row tinted valid/invalid before drop; soft halos, not error tiles, for in-progress cells.

**B — content-led: an index of articles or projects and their detail pages.**
- **Subtract:** an entry is image, title and one fact — nothing the reader doesn't need to choose. Hover is a tone change on the neutral ramp.
- **Grid:** fluid headline `round(clamp(…), <the system's step>)`; entry gaps on the major unit.
- **Copy:** titles differ in their first word (12).
- **Continuity:** where an entry opens its detail in place, the entry becomes it ([motion-continuity](../motion-continuity/SKILL.md) rule 1); page navigation is fine.

## Verification

Scale it to the change: a look-and-feel tweak is checked by eye in what it touches; a new surface runs all eight.

1. **One axis per role** — one of hue/lightness/chroma varies; the rest lock.
2. **Every text-on-fill pairing is APCA-gated**, with a dark ramp derived on its own.
3. **Tools: the canvas never reflows on selection.**
4. **Every theme and mode rendered and compared** — light, dark, increased contrast, forced colors.
5. **No focus ring is clipped**; hover/active/disabled states are distinct.
6. **Each element has a purpose; each primitive one definition.**
7. **No computed size is off its scale**, fluid sizes included.
8. **Sibling copy, listed together,** is distinct and alike in punctuation.

## Cross-references

- **REQUIRED COMPANION:** [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) — enforces this bar per slice, one designer lane per surface.
- **Consumed by:** [visual-polish](../visual-polish/SKILL.md) (REQUIRED BACKGROUND there); [design-system-consistency](../design-system-consistency/SKILL.md) (principle 1); [thrill-design](../thrill-design/SKILL.md), one house's taste on this bar.
- **Built on:** [apca-contrast](../apca-contrast/SKILL.md), [oklch-color-space](../oklch-color-space/SKILL.md).

## Sources

- Principles 1–2: the primary sources [oklch-color-space](../oklch-color-space/SKILL.md) and [apca-contrast](../apca-contrast/SKILL.md) cite.
- Principle 9: Rams, "as little design as possible" ([Vitsoe](https://www.vitsoe.com/us/about/good-design)). Principle 11: `round()` ([CSS Values 4](https://www.w3.org/TR/css-values-4/#round-func); Baseline 2024).
- **House convention, not a spec:** the rest of the bar is this catalog's own taste standard.
