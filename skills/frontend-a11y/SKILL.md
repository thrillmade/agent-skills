---
name: frontend-a11y
description: >-
  Visual review — accessibility on the rendered surface: contrast, focus
  visibility, tap targets, semantics, motion. Cite the element and the
  failing ratio or state.
kind: design
review_mode: dedicated
applies_to:
  paths: ["site/**", "app/**", "**/components/**", "**/ui/**"]
  extensions: [".tsx", ".jsx", ".css", ".scss", ".vue", ".svelte"]
---

# Frontend accessibility

You are reviewing the **rendered** change (screenshots, light and dark) plus the markup for
accessibility. Cite the element and the concrete failure (the measured ratio, the missing
state, the tag).

## Flag

1. **Contrast.** Body text below WCAG AA 4.5:1, or large text / UI borders below 3:1 — in
   **either** theme (check both screenshots; dark mode is where contrast quietly fails).
   Name the foreground/background and the approximate ratio.
2. **Focus visibility.** Any interactive element with no visible focus indicator, or a focus
   ring removed (`outline: none`) without a replacement. Keyboard users must see focus.
3. **Tap / click targets.** Controls smaller than ~24x24 CSS px (44px on touch surfaces),
   or targets packed too tightly to hit reliably.
4. **Semantics.** Icon-only buttons without an accessible name (`aria-label`/visually-hidden
   text); headings that skip levels; a `<div>` with a click handler where a `<button>`/`<a>`
   belongs; images conveying meaning without alt text.
5. **Color-only signaling.** State or meaning carried by color alone (e.g. red/green status
   with no icon or label).
6. **Motion.** Auto-playing or large motion that doesn't honor `prefers-reduced-motion`.

## How to judge

- Prefer findings you can see or measure in the screenshot/markup; estimate the contrast
  ratio rather than hand-waving "low contrast."
- A genuine WCAG-AA failure on interactive/text content is high severity; a borderline ratio
  or a nice-to-have is medium/low.
- One issue per finding: element, the failure, the fix.

If the surface is clean on these checks in both themes, say so in one line.
