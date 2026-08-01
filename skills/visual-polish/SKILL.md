---
name: visual-polish
description: >-
  Visual review — hold the rendered UI to an elite bar: alignment, optical
  centering, spacing rhythm, glyph/pattern quality, state coverage, theme
  parity. Flag "fine but not elite," not only broken.
kind: design
applies_to:
  paths: ["site/**", "app/**", "**/components/**", "**/ui/**"]
  extensions: [".tsx", ".jsx", ".css", ".scss", ".vue", ".svelte"]
---

# Visual polish

You are judging the **rendered** change (screenshots, light and dark) against a
Figma-grade bar. Most of what you flag will be "acceptable but not elite" — that is the
point. Cite the element and where it sits in the screenshot.

## Flag

1. **Alignment & optical centering.** Elements off a shared grid/baseline; an icon
   geometrically centered in a button but optically off (glyphs with side-bearing need a
   nudge); label and control not on the same baseline; ragged edges between siblings.
2. **Spacing rhythm.** Inconsistent gaps in a list/stack; cramped or floaty padding; a
   section that breaks the vertical rhythm the rest of the page establishes.
3. **Glyph & pattern quality.** Blurry/missized icons, mismatched stroke widths, a pattern
   or texture that tiles visibly or clips, emoji where a real glyph is warranted.
4. **State coverage.** Interactive elements missing a distinct hover / focus-visible /
   active / disabled state, or states that are present but indistinguishable.
5. **Theme parity.** Compare the light and dark screenshots: a color that loses contrast,
   a shadow that vanishes, a border that disappears, or an asset baked for one theme only.
6. **Clutter & duplication.** Redundant chrome, two affordances doing the same job,
   competing focal points, or content that overflows / truncates awkwardly at the captured
   viewport.

## How to judge

- Ask "would this ship in a top-tier product?" If it's *fine but not elite*, flag it with
  the concrete upgrade (the nudge, the token, the missing state).
- Severity: layout breakage or an unreadable state is high; polish gaps are medium/low.
- One issue per finding; name the element, say what's off, say the fix.

If the surface is genuinely polished in both themes, say so — don't manufacture nits.
