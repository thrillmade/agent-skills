---
name: design-system-consistency
description: Visual review — flag rendered UI that drifts from the design system's tokens, scale, and color discipline. Judges the screenshot, not just the code.
kind: design
review_mode: dedicated
applies_to:
  paths: ["site/**", "app/**", "**/components/**", "**/ui/**"]
  extensions: [".tsx", ".jsx", ".css", ".scss", ".vue", ".svelte"]
---

# Design-system consistency

You are reviewing the **rendered** change (screenshots, light and dark) against the
project's design system. Cite the specific element you see in the screenshot — name it
and where it is — not just the source line.

## Flag

1. **Off-token values.** A hardcoded color, spacing, radius, shadow, or font-size where a
   design token / CSS variable already exists for that role. Quote the value and name the
   token it should use.
2. **Color discipline.** Fills should be cool/neutral; strokes and text are the warm/ink
   layer; a saturated red (or the system's "danger" hue) is reserved for destructive or
   critical states. Flag a red used for a non-critical accent, or a one-off accent hue that
   isn't in the palette. Prefer perceptually-uniform color (OKLCH/LCH) over ad-hoc hex when
   the system uses it.
3. **Off-scale spacing.** Margins/padding/gaps that don't land on the spacing scale (e.g. a
   `13px` gap in a 4-/8-pt system). Rhythm should be consistent between sibling elements.
4. **Type ramp drift.** A font-size/weight/line-height combination outside the defined type
   scale, or the same semantic level rendered at two different sizes across the view.
5. **Re-implementation.** A button/card/input hand-rolled inline when a system component
   exists — visible as subtly different padding, radius, or hover from its siblings.

## How to judge

- Compare the new surface against an existing, known-good surface in the same product.
- "It renders" is not the bar — **token-correct** is the bar. Flag a value that looks fine
  but bypasses the system; say which token restores consistency.
- One concrete drift per finding, with the rendered element quoted and the fix named.

If the rendered change is token-clean and on-scale in both themes, say so in one line.
