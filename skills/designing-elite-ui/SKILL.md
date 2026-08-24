---
version: "1.0.0"
digest: "4500a7e39f2d"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: designing-elite-ui
description: Visual review — hold the rendered UI to a concrete elite/Figma-grade bar (one-axis color, APCA-gated contrast, floating stable chrome, dark verified) instead of a vague "looks fine." The STANDARD a design-critic measures against.
kind: design
applies_to:
  paths: ["site/**", "app/**", "**/site/**", "**/app/**", "**/components/**", "**/ui/**", "**/styles/**"]
  extensions: [".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".css", ".scss"]
---

# Designing Elite UI

The design *bar* is the standard; the QA loop is the enforcement (see `orchestrating-elite-agent-qa`). A critic with no encoded bar finds nothing — "looks fine." This skill is the bar: the transferable taste an agent designs *to* and critiques *against*. **Encode it explicitly** (a tokens file + a short design-system doc) so both builders and the critic share one source of truth.

## When to use

- Before a build starts, to encode the bar (tokens file + short design-system doc) so the builder and the critic share one standard instead of "looks fine."
- As the standard a design-critic agent measures a render against inside `orchestrating-elite-agent-qa`'s browser-driving gate.
- Auditing a shipped UI end-to-end against an elite/Figma-grade bar, not one specific craft nit.

## When NOT to use

- **Judging execution on an already-built surface** — [visual-polish](../visual-polish/SKILL.md); this skill sets the bar, it does not grade a build against it.
- **Auditing whether a value is on-system** (token drift, off-scale spacing) — [design-system-consistency](../design-system-consistency/SKILL.md).
- **Measuring a contrast, focus, or target-size success criterion** — [frontend-a11y](../frontend-a11y/SKILL.md) and [apca-contrast](../apca-contrast/SKILL.md) own the pass/fail mechanics; this skill only requires that contrast be gated.

## The Principles

1. **One semantic role → one meaning → one variation axis.** Give each role a band where *exactly one* dimension varies and the rest lock; it reads deliberate, not random. **Reserve a color for ONE meaning only.** (Example below: status fills vary hue at locked L/C; pending/warning badges vary hue in a warm band, never red; destructive actions are red, reserved.)
2. **Contrast is gated, not eyeballed.** APCA-check every text-on-fill. A theme flip needs its *own* ramp (a dark draw ramp, derived dark reds) — never reuse the light values on a dark surface.
3. **Restraint beats richness.** Distinguish by hue-in-band + shape + label, not a rainbow. Plain text labels with a subtle active state, not boxy segmented controls. Tinted/outline active states over heavy solid fills. Retire decoration that doesn't carry meaning.
4. **Type: one family + its mono.** Mono for data, codes, and labels; optical centering (`text-box-trim`); restrained weights. Consistency over variety.
5. **The canvas is stable; chrome floats.** The work surface NEVER reflows or rescales on selection (lock px-per-unit). Panels float *over* it; the toolbar morphs smoothly; one icon language; a per-context accent. Infinite/dotted background beats a white card on a page.
6. **Interaction feels alive before the click.** Cursor affordances (resize cursors on handles, grab/grabbing on pan), hover highlights, valid/invalid ghost tints, smooth transitions, unmistakable active states.
7. **Light and dark are BOTH primary.** Design and verify in both; neither is an afterthought.
8. **Optical, not metric, alignment.** Center to the eye (text trim, icon nudge); balance a frame so no element reads as an afterthought; never ship a clipped focus ring.

## Gotchas That Quietly Break the Bar

| Symptom | Cause / fix |
|---|---|
| Popover text clipped / see-through | A `backdrop-filter` ancestor traps even `position:fixed` children → **portal the popover to `<body>`**; opaque frame + inner scroll owns any fade-mask. |
| Pill/toolbar drifts off-center | `left:50%` on an auto-width fixed element caps it to 50vw → wrap in a full-width flex container, center inside; recompute after layout settles. |
| Dark mode looks washed/low-contrast | Light tokens reused on dark → add explicit dark ramps; re-run APCA. |
| Two controls read "active" at once | Mode vs tool both filled with the accent → give the resting one a tinted/outline state. |
| Glyph looks wrong only when rotated | Glyph drawn fixed while footprint swapped → re-orient the silhouette with the rotation. |

## Encode the Bar (so it's enforceable)

The bar only bites if it's written down where agents read it:
- **Tokens** in one file (colors as the actual system, not ad-hoc hex), emitted to CSS vars.
- **A design-system doc** (a SPEC section / memory) stating the domains, the variation axis per role, the type rules, the chrome model.
- **Feed it to the design-critic**: "challenge the render against THIS bar in light + dark" — not "is it nice?". Vague critics pass everything.

## Worked Example (one system, fully specified)

Admin dashboard for a SaaS product, composed from an existing token-driven system — tokens and component primitives (button, input, table row, toolbar, panel) already on disk; nothing here is hand-rolled, and any gap in the kit is proposed upstream rather than built inline:
- **Color = OKLCH, three domains, one axis each.** Status fills (tables/cards/tabs) = cool band blue→purple→pink, vary **hue**, lock L≈.88/C≈.07; neutral states near-grey. Pending/loading/warning badges = warm band green→orange, vary **hue**, NO red (red must stay unambiguous). Destructive/critical (delete confirmations · error banners · failed states) = **red, reserved**; destructive intensities vary **lightness** only. Reduced-color/monochrome mode → one uniform grey for all status fills; the semantic red/badges stay. APCA-gate every metric label + status chip.
- **Type:** Geist + Geist Mono; mono for ids/timestamps/metric values; `text-box-trim` centering.
- **Chrome:** stable content canvas — the data table/chart surface never reflows or rescales on row selection (row density + px-per-unit on chart axes locked); floating collapsible sidebar + floating top toolbar are the system's own panel/toolbar components, both over the canvas (Lucide icons, per-section accent); detail panel floats *over* the canvas, never splits it.
- **Interaction:** column-resize cursors on header handles; grab/grabbing on chart pan; drag-reorder ghost row (valid/invalid tint) before drop; soft warning halos on cells needing attention, not hard error tiles, for in-progress states.

## Verification

After building or critiquing a surface against this bar:

1. **One axis per role** — exactly one of hue/lightness/chroma varies per semantic color role; the rest are locked.
2. **Every text-on-fill pairing is APCA-gated**, not eyeballed — including a dark-mode ramp derived on its own, never the light ramp reused.
3. **The canvas never reflows on selection** — anything that changes on interaction is chrome floating over it, not the surface itself.
4. **Both themes were actually rendered and compared**, not one screenshot in one theme.
5. **No focus ring is clipped**, and every control has a hover/active/disabled state distinct from its neighbors.

## Sources

- Principle 1 (one axis per role) and principle 2 (APCA-gated contrast) are grounded in the primary sources [oklch-color-space](../oklch-color-space/SKILL.md) and [apca-contrast](../apca-contrast/SKILL.md) already cite — linked rather than restated, so the two skills never disagree on what backs the claim.
- **House convention, not a spec:** the rest of the bar is this catalog's own taste standard.

## Cross-references

- **REQUIRED COMPANION:** [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) — enforces this bar per slice, including the browser-driving design-critic gate.
- **Consumed by:** [visual-polish](../visual-polish/SKILL.md) (REQUIRED BACKGROUND there) applies this bar as a craft lens; [design-system-consistency](../design-system-consistency/SKILL.md) reads principle 1 as the stance it judges color drift against.
- **Built on:** [apca-contrast](../apca-contrast/SKILL.md) and [oklch-color-space](../oklch-color-space/SKILL.md).
