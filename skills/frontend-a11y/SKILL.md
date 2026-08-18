---
version: "56be4995fc2f"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: frontend-a11y
description: >-
  Use when judging accessibility on a RENDERED surface — screenshots or a live
  page, in light, dark, forced-colors and reduced-motion, at real zoom — as the
  a11y lens of a design review. Owns what only the render shows: contrast
  measured on the composited pixel rather than the token, focus rings that
  survive forced-colors and are not covered by sticky chrome (SC 2.4.11), hit
  areas measured as laid out including the 2.5.8 spacing exception, meaning
  carried by colour / gradient / shadow, and motion that actually plays.
  Thresholds are NOT restated here — contrast belongs to apca-contrast and
  wcag-contrast, target size to component-sizing-principles. Cite when a review
  calls contrast "low" with no measured pair, checks light mode only, reports an
  AAA criterion as an AA failure, or infers accessibility from source alone.
kind: design
applies_to:
  paths: ["site/**", "app/**", "**/site/**", "**/app/**", "**/components/**", "**/ui/**", "**/styles/**"]
  extensions: [".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".css", ".scss"]
---

# Frontend accessibility

The a11y lens on the **rendered** surface. The code lens already read the source, so a
finding here should be one a source read could not produce — naming the element, the
mode, the measured value, the fix.

**Measure the composited pixel, not the token.** Opacity, overlays, `backdrop-filter`, a
photo behind text and antialiasing on thin weights all change the pair the eye receives,
so a token that passes in the palette can fail where it landed. House convention, and the
commonest false pass here.

## When to use

- Judging a screenshot set or live page for accessibility inside a design review.
- A visual surface changed and renders exist in more than one mode.
- Auditing a shipped surface for failures that appear only once composited.

## When NOT to use

- **No render.** Labels, input types, tab order and `aria-*` read off the diff belong to
  [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md).
- **Setting a threshold.** [apca-contrast](../apca-contrast/SKILL.md) and
  [wcag-contrast](../wcag-contrast/SKILL.md) own contrast;
  [component-sizing-principles](../component-sizing-principles/SKILL.md) owns the height
  ladder. Cite them, never re-derive them — this lens measures what the render gives the
  pointer, not what the ladder should have been.
- Non-visual diffs — routing, state wiring, backend. Nothing renders; stay silent.

## What only the render shows

1. **Composited contrast.** Report the sampled pair and value, then cite the owner:
   [apca-contrast](../apca-contrast/SKILL.md) for Lc targets and the primary-model policy,
   [wcag-contrast](../wcag-contrast/SKILL.md) for the 2.2 thresholds and the
   points-not-pixels rule. Obey the system's declared primary model and name it; absent
   one, the pairing fails if either model fails.
2. **Focus rings, in place.** Source shows a ring exists; only the render shows it
   survives — clipped by an ancestor `overflow: hidden`, drowned against the *actual*
   adjacent surface, or gone in forced-colors. **SC 2.4.11 Focus Not Obscured (Minimum),
   AA in 2.2** is separate: sticky chrome hiding the focused control *entirely* fails even
   with a perfect ring, so capture the row scrolling under it. Partial occlusion is 2.4.12,
   AAA. Ring contrast is SC 1.4.11;
   **SC 2.4.13 Focus Appearance is AAA** — an enhancement, never an AA failure. Tooltips
   and hover cards have their own rule: hoverable, dismissible without moving the pointer,
   persistent (**SC 1.4.13, AA**).
3. **Hit area, as laid out.** **SC 2.5.8, AA — 24 by 24 CSS px**, then the spacing
   exception: a 24 px circle on each **undersized** target must miss **another target's
   box** — not its circle — and another undersized target's circle. So a 20 px button 1 px
   from a 40 px one fails. Dense icon toolbars fail on spacing more than size; measure the
   gap. Touch surfaces have a higher
   platform floor; read that platform's HIG. The ladder behind the height is
   [component-sizing-principles](../component-sizing-principles/SKILL.md).
4. **Meaning that can vanish.** **SC 1.4.1 Use of Color, A** — status as red/green with
   no icon, text or shape; and on a render, meaning carried by a gradient or a shadow,
   which forced-colors removes outright.
5. **Names, as exposed.** A control that renders as a bare glyph must still expose a
   name, so read the accessibility tree rather than `aria-*` in the source — `aria-label`
   on a role-less element is never exposed (**SC 4.1.2, A**), and visual structure the
   markup does not carry is **SC 1.3.1, A**.

## The modes you must actually look at

A mode not captured is not checked — name the ones you saw.

| Mode | What fails first |
|---|---|
| **Light and dark**, both primary | Borders, disabled text, shadow-drawn separators |
| **`forced-colors: active`** | `box-shadow` and `text-shadow` compute to `none`, `background-image` to `none` without a `url()` — anything drawn as a shadow or gradient is gone. System colours come from **native semantics, not ARIA roles** |
| **`prefers-contrast: more`** | Deliberately subtle borders; placeholder text already near the floor |
| **`prefers-reduced-motion`** | CSS transitions usually honour it; JS/WAAPI animation, autoplaying video and carousels usually do not |
| **Reflow — SC 1.4.10, AA** | 320 CSS px wide (≈ 400% zoom at 1280), no two-dimensional scrolling; 256 CSS px tall when scrolling horizontally |
| **Text spacing — SC 1.4.12, AA** | No loss of content at line-height 1.5×, paragraph 2×, letter-spacing 0.12em, word-spacing 0.16em: fixed-height buttons, single-line chips |

Motion has two obligations: auto-starting motion over five seconds must be pausable
(**SC 2.2.2, A**); disabling interaction-triggered motion is **SC 2.3.3, AAA**.
`prefers-reduced-motion` is the mechanism, not the criterion.

## Silent failures

- **A `box-shadow` focus ring.** Passes source review and both theme screenshots, gone in
  forced-colors. Fix: `outline` + `outline-offset` (only its colour is forced), or a
  `@media (forced-colors: active)` rule.
- **Reduced motion honoured in CSS only.** The `@media` block exists, the JS animation
  ignores it, and screenshots are static so this lens never sees it. Check the JS/WAAPI
  path, `<video autoplay>`, library defaults.
- **A clean automated run read as a pass.** A checker reports what it can compute — not a
  ring lost under sticky chrome, meaning in a gradient, or text over a photo.

## Verification

1. Every finding names element + mode + measured value + the SC with its level, or the
   skill owning it. No bare "low contrast".
2. Contrast findings cite [apca-contrast](../apca-contrast/SKILL.md) /
   [wcag-contrast](../wcag-contrast/SKILL.md), name the system's primary model, and quote
   a value sampled from the composited render rather than read off a token.
3. No AAA criterion (2.4.13, 2.3.3) is reported as an AA failure, and focus was exercised
   by tabbing rather than inferred from a `:focus-visible` rule.
4. Every mode in the table is reported as checked or as not captured — including on a
   clean surface, whose one-line pass **names the modes checked**. A clean report not
   naming its modes is not evidence.

## Sources

- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) — every SC above carries its published level
  ([2.5.8](https://www.w3.org/TR/WCAG22/#target-size-minimum),
  [2.4.11](https://www.w3.org/TR/WCAG22/#focus-not-obscured-minimum)). 2.4.13 and 2.4.12
  are **AAA** there, not AA.
- [CSS Color Adjust 1](https://www.w3.org/TR/css-color-adjust-1/#forced) is normative for
  the forced-colors `box-shadow` / `text-shadow` / `background-image` behaviour;
  [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/forced-colors) adds that
  system colours come from native semantics, not ARIA roles.
  [Media Queries 5](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion) defines
  the preference queries.
- **House convention, not a standard:** sampling the composited pixel; "a mode not
  captured is not checked".

## Cross-references

- **REQUIRED BACKGROUND:** [apca-contrast](../apca-contrast/SKILL.md) — Lc targets and
  which model is primary; [wcag-contrast](../wcag-contrast/SKILL.md) — the 2.2 thresholds
  and the points-not-pixels rule. This lens measures; they own the numbers.
- **Target size:** [component-sizing-principles](../component-sizing-principles/SKILL.md)
  and [spacing-system](../spacing-system/SKILL.md). **Code side:**
  [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md) — a
  finding makeable from the diff alone is theirs.
- **Siblings:** [design-system-consistency](../design-system-consistency/SKILL.md)
  (off-system, not inaccessible) · [visual-polish](../visual-polish/SKILL.md) (passes but
  reads dull) · [designing-elite-ui](../designing-elite-ui/SKILL.md) (the bar).
  [reviewing-design-work](../reviewing-design-work/SKILL.md) orders all four, and
  [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) drives the
  browser pass producing these renders.
