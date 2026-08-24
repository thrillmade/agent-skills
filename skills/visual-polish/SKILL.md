---
version: "1.0.0"
digest: "b470bbfb49da"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: visual-polish
description: >-
  Use when judging execution craft on a RENDERED surface — screenshots or a live
  page — as the polish lens of a design review: optical versus metric alignment,
  hairlines and half-pixel blur, whether spacing reads as grouping, the full
  state and content matrix, theme parity beyond colour, RTL and long-locale
  mirroring, clutter. Flags "fine but not elite", not only broken. Judges craft,
  not values — whether a chosen step is on the system's scale belongs to
  design-system-consistency, whether a pairing is legible to frontend-a11y, and
  what the bar is to designing-elite-ui. Cite when a review passes a surface off
  one light-mode screenshot at seed content, when a nit arrives without the
  concrete upgrade, or when a polish fix is proposed as a magic pixel value.
kind: design
applies_to:
  paths: ["site/**", "app/**", "**/site/**", "**/app/**", "**/components/**", "**/ui/**", "**/styles/**"]
  extensions: [".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".css", ".scss"]
---

# Visual polish

The craft lens on the **rendered** surface: whether what shipped is *executed* well, not
whether its values are on-system or its pairings legible. Most of what you flag will be
"acceptable but not elite" — that is the job, and every finding carries the concrete
upgrade (the trim, the token, the missing cell), never just the verdict.

## When to use

- Judging a rendered surface against a Figma-grade bar inside a design review.
- A component or layout changed and renders exist across themes and states.
- Comparing a build against the design file — what differs is usually craft, not intent.

## When NOT to use

- **No render.** This lens has nothing to read.
- **The value is off-system** — [design-system-consistency](../design-system-consistency/SKILL.md).
  "That gap is 13 px in a 4/8 system" is drift; "those two gaps read identical and should
  not" is polish.
- **The pairing is illegible, or the target too small** —
  [frontend-a11y](../frontend-a11y/SKILL.md). A polish nit never outranks a measured
  success-criterion failure, and never gets filed as one.
- **Deciding what the bar *is*** — [designing-elite-ui](../designing-elite-ui/SKILL.md).
  This lens applies a bar; it does not set one.

## What to look at

1. **Optical vs metric alignment.** Glyphs carry side bearings and asymmetric mass, so a
   box-centred element is not eye-centred: a play triangle in a round button reads
   left-heavy, and a cap-height label metric-centred in a pill sits low because the empty
   descender space counts. Fix by trimming the text box (`text-box-trim` / `text-box`,
   where supported) rather than hand-tuning `line-height`, and nudge a glyph *toward its
   optical centroid* — give the direction and the reason, not a magic pixel count.
2. **Hairlines and half-pixel blur.** A border landing on a fractional device pixel
   renders grey and soft. Usual causes: an odd container height with a centred child,
   `translate(-50%)` on an odd width, a fractional `scale` on an ancestor, a 1 px rule
   inside a transformed parent. Recognise it as a divider crisp on one side and mushy on
   the other, or one that vanishes at a particular zoom. Fix the geometry — even
   dimensions, integer offsets — not the colour.
3. **Rhythm has to read as grouping.** Grouping is perceived from *relative* distance, so
   the gap inside a group must be visibly smaller than the gap between groups. When both
   land on the *same* legal step, every value passes and the hierarchy is gone — a form
   where each label looks equidistant from its own field and the next one. Fix: two
   distinct steps, far enough apart to read — the ratio they must clear is
   [empirical-design-principles](../empirical-design-principles/SKILL.md)'s, not this
   lens's. [spacing-system](../spacing-system/SKILL.md) owns the scale; this lens
   owns whether the chosen steps read.
4. **The state and content matrix.** Two axes, both usually under-covered. States: rest,
   hover, focus-visible, active, disabled, loading, error. Content: empty, one item, long
   string, overflow, slow network. Flag cells that are *missing* and cells that are
   *present but indistinguishable* — hover and active rendering identically is the same
   defect as no hover at all. A disabled state built from opacity alone often drops its
   label under the contrast floor; that half is [frontend-a11y](../frontend-a11y/SKILL.md)'s.
5. **Theme parity beyond colour.** Dark is not light inverted. A drop shadow is a
   light-surface device — over near-black there is little left to darken, so elevation has
   to come from surface lightness, which is why Material's dark guidance makes higher
   surfaces *lighter* rather than shadowing them harder. Low-alpha borders that read on
   white disappear on near-black, and assets bake the assumption in: a raster logo with a
   white matte, an SVG with a hardcoded fill where `currentColor` belongs.
6. **Direction and locale.** In RTL the layout mirrors, and so do direction-encoding
   icons (back, next, indentation); icons depicting real objects — a clock, a printer — do
   not, and a blanket `scaleX(-1)` over the icon set is the usual bug. Long-locale strings
   are the honest test of a fixed-width label.
7. **Clutter and duplication.** Two affordances doing one job, competing focal points,
   chrome restating what the content already says, decoration carrying no meaning.

## Silent failures

- **Captured at one DPR.** Hairline blur and antialiasing differences only show at 1×;
  a 2× capture flatters the surface. Say which DPR the evidence came from.
- **Captured at seed content.** "Jane Doe" and three rows hide every truncation and every
  empty state. Re-capture with real strings, one item, and none.
- **The fix landed as a magic number.** A 2 px optical nudge hardcoded is drift the moment
  density or type changes — it is a finding for
  [design-system-consistency](../design-system-consistency/SKILL.md) on the next pass. The
  fix is a trim, a token, or a geometry change.
- **Motion judged from stills.** A transition that jumps, a hover that shifts layout, an
  entrance animation replaying on every re-render: none of it is in a screenshot.
- **Nits manufactured to look thorough.** A polished surface reported as polished is a
  valid output; padding the list costs the reviewer's credibility on the findings that
  matter.

## Verification

1. Every finding names the element, where it sits in the capture, what is off, and the
   concrete upgrade. A verdict without an upgrade is not a finding.
2. No finding proposes a raw value as the fix where a token, a trim or a geometry change
   is available.
3. Both themes were compared, and the DPR and content state of the evidence are stated.
4. Findings that are really drift or really a11y were routed, not re-filed here — severity
   never ranks a polish nit above a measured failure.
5. A genuinely polished surface gets one line saying so, naming what was exercised.

## Sources

- [CSS Inline Layout 3 — `text-box-trim`](https://drafts.csswg.org/css-inline-3/#text-box-trim)
  and [MDN `text-box`](https://developer.mozilla.org/en-US/docs/Web/CSS/text-box) — the
  standards-track replacement for hand-tuned `line-height` centring, plus its support.
- [MDN `devicePixelRatio`](https://developer.mozilla.org/en-US/docs/Web/API/Window/devicePixelRatio)
  — why a 1 px rule is not one device pixel.
- [Material 3 — elevation](https://m3.material.io/styles/elevation/overview): higher
  surfaces are expressed lighter, which is why shadow-only elevation fails on dark.
- [Apple HIG — right to left](https://developer.apple.com/design/human-interface-guidelines/right-to-left)
  for which glyphs mirror.
- **Design principle, not a spec:** grouping read from relative distance (Gestalt
  proximity). **House convention:** "fine but not elite" is a legitimate finding, and so
  is a clean verdict.

## Cross-references

- **REQUIRED BACKGROUND:** [designing-elite-ui](../designing-elite-ui/SKILL.md) — the bar
  this lens applies, including the one-role-one-axis rule behind clutter findings. A critic
  with no encoded bar finds nothing.
- **Siblings, and the boundary with each:**
  [design-system-consistency](../design-system-consistency/SKILL.md) — off-system values ·
  [frontend-a11y](../frontend-a11y/SKILL.md) — measured contrast, focus, target failures.
- **Scales these judgements sit on:** [spacing-system](../spacing-system/SKILL.md) (rhythm
  steps) · [type-scale](../type-scale/SKILL.md) and
  [line-height-grid](../line-height-grid/SKILL.md) (why a label sits low in its box) ·
  [component-sizing-principles](../component-sizing-principles/SKILL.md) (siblings sharing
  a rung).
- **Code side:**
  [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md) — state
  and transition rules readable from the diff. **Above:**
  [reviewing-design-work](../reviewing-design-work/SKILL.md) orders the lenses and
  [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) drives the
  browser pass producing the states and themes this lens needs.
