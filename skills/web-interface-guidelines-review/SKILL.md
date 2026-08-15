---
name: web-interface-guidelines-review
description: |
  Use when reviewing UI code or design output (React, Vue, Svelte, Astro, plain HTML, design specs) for adherence to web-interface guidelines — Vercel's WIG, Material 3, Radix patterns, and similar opinionated rule sets — extended with token-driven contrast, typography-scale, and spacing-system rules. Names the APCA-preferred contrast stance (cross-check WCAG 2.2 AA, never WCAG-only), the atomic typography class convention (one class binds font + size + lh + tracking + weight), the token-not-raw-hex rule, verb-noun action labels, the focus-ring contract (>= 2 px, 3:1 against both control and adjacent surface, never suppressed), the 24 CSS px WCAG 2.5.8 interactive floor, and the link-vs-button distinction. Cite when an agent reviews UI without checking token discipline, hardcoded values, or atomic typography compliance.
---

# Web interface guidelines review

## When to use

- Reviewing a PR that adds or modifies UI components.
- Auditing an existing UI surface for token discipline, contrast, focus handling, and a11y.
- Writing or reviewing design specs that propose new components.
- After a Figma → code handoff, before merging.

## When NOT to use

- Pure backend / non-UI PRs (skill won't fire on a server-route change).
- Marketing-only landing pages with bespoke design that intentionally lives outside the system.
- Prototype code explicitly labeled as throwaway.

## The review checklist

Apply each section in order. Stop and flag at the first failure in each section.

### 1. Contrast: APCA-preferred, WCAG cross-check

- **Primary model is APCA Lc.** Verify the foreground color hits its declared Lc target (typically 90 fluent body, 75 body minimum, 60 secondary, 45 large display, 30 spot, 15 non-text — see `apca-contrast`).
- **WCAG 2.2 AA is a cross-check, not the primary.** Verify the pair also meets 4.5:1 (normal) / 3:1 (large or non-text) per `wcag-contrast`. Sizes are in **points**, not pixels (18 pt ≈ 24 CSS px; 14 pt bold ≈ 18.67 CSS px).
- Flag any review that cites WCAG as the *only* model — APCA catches real perceptual failures WCAG misses.
- Flag hardcoded hex in source: every contrast-bound color resolves from a token (role families content / surface / border — see `token-naming-conventions`).

### 2. Typography: atomic classes from the scale

- **Atomic typography classes.** One Tailwind / utility class binds font-family + size + lh + tracking + weight — e.g. `body-md`, `heading-lg`. No à-la-carte composition (`text-sm font-medium tracking-tight`).
- **Sizes come from the type scale.** Every rendered font-size matches a step from the system's modular scale (1.067 → 1.618 family). Flag arbitrary px like `text-[13px]` — outside the scale.
- **Line-height per role.** UI text uses `lh-ui` (× 1.20 + grid snap); paragraph body uses `lh-prose` (× 1.50 + grid snap). See `line-height-grid`.
- Body text **never below 14 pt** (≈ 18.67 CSS px); UI labels usable down to 12 CSS px for non-fluent content (badges, metadata) but **never below 10 px**.

### 3. Spacing + sizing: token-driven

- Padding, gap, margin values are tokens from the spacing scale (`padding-*` / `space-*` / `gap-*`), not raw px. See `spacing-system`.
- Component heights come from the system's per-density curated ladder. See `component-sizing-principles`.
- **Interactive heights ≥ 24 CSS px** per WCAG 2.5.8 (AA, Target Size Minimum). Rungs below that floor are non-interactive only; whether a ladder's smallest rung is *additionally* reserved is owned by [component-sizing-principles](../component-sizing-principles/SKILL.md).
- Flag inconsistent rung mixing in the same UI surface (`sm` + `md` buttons side by side reads as a typo, not a hierarchy).

### 4. Action labels: verb-noun

- Buttons that perform an action use verb-noun ("Save changes", "Send invitation", "Open settings"). Never "Click here!", "Submit", or "OK" alone.
- Links that navigate use destination-descriptive text ("Browse all results", not "Click here"). WCAG 2.4.4.
- Flag tone drift: marketing exclamation marks, hedging ("might want to"), emoji in interactive labels.

### 5. Link vs button

- **Links go places. Buttons do things.** Navigating or changing the URL is an `<a>` / `<Link>`; triggering an action is a `<button>`.
- Flag `<button>` using `window.location.href = …` or `router.push(…)` — that's a link.
- Flag `<a>` with `onClick` doing in-place mutation and `href="#"` — that's a button.
- Use the framework's router (`<Link>`, `useRouter`) for SPA navigation; never raw `window.location` reassignment.

### 6. Focus + keyboard

- **Focus-visible always.** Every interactive element has a visible focus ring on `:focus-visible`. The default Tailwind reset suppresses outlines; the system must re-add them.
- **Focus ring contract:** ≥ 2 px thickness; 3:1 contrast against both the focused control's background AND the adjacent surface (WCAG 2.4.13, AA in WCAG 2.2). A well-formed system generates its focus token to satisfy this contract.
- **Keyboard reachability:** every interactive control is tabbable; tab order matches visual order.
- **Escape closes overlays:** dialogs, popovers, dropdowns close on Escape.

### 7. Forms

- Every form control has a programmatic label (`<label>`, `aria-label`, or `aria-labelledby`). Placeholders are NOT labels — they vanish on focus.
- Search inputs use `type="search"`; emails `type="email"`; numbers `type="number"` with sensible `inputmode`. Mobile keyboard semantics depend on the type.
- Forms submit on Enter (a `<form>` wrapper with a submit handler, not a `<button onClick>` that ignores Enter).
- Required fields marked both visually (asterisk + legend) and programmatically (`required` or `aria-required`).

### 8. Icons + non-text content

- Decorative icons get `aria-hidden="true"` and no accessible name.
- Functional icons (icon-only buttons) get an accessible name via `aria-label` ("Search", "Close dialog").
- Icon sizes come from the curated ladder (e.g. 12, 16, 24, 32, 40, 48), paired with the control's rung per `component-sizing-principles`. No arbitrary `size={14}`.

### 9. Motion

- Honor `prefers-reduced-motion: reduce` — reduce animation distance and easing, or remove non-essential motion entirely.
- Transitions on color, transform, and opacity only; never `width`, `height`, `top`, `left` (they trigger layout).
- Durations from a token (`duration-fast` / `duration-default` / `duration-slow`), not arbitrary `ms` values.

### 10. Token discipline

- No raw hex, no raw px, no raw rem in source. Every value resolves from a token (a text role token, `padding-md`, `radius-lg`, etc.).
- Component tokens reference semantic / color-mode tokens, never primitives directly (see `token-naming-conventions` for the two chain shapes).
- Flag inline `style={{ … }}` carrying values that should be tokens; the only exception is values genuinely computed at runtime.

## How to phrase findings

- One finding per comment. Bundling unrelated issues makes them hard to track.
- Cite the rule + the source (WCAG SC, WIG section, the relevant skill name).
- Show the fix, not just the rule. "Replace `style={{ color: '#666' }}` with `className=\"text-secondary\"`" beats "use the design tokens."
- Quote the offending line verbatim before the critique.

## Cross-references

- **REQUIRED BACKGROUND:** contrast — `apca-contrast`, `wcag-contrast`; typography — `type-scale`, `line-height-grid`; spacing — `spacing-system`, `component-sizing-principles`; tokens — `token-naming-conventions`, `dtcg-format`.
- **UI-string voice:** `brand-voice-review`.

## Verification

After completing a review:

1. **Every finding cites a rule.** No vibes-based "this feels off."
2. **Every finding has a fix.** Fixless findings get rejected.
3. **Sections applied in order.** Contrast and a11y come before token discipline; don't lead with cosmetic findings.
4. **No bundled comments.**
5. **Skills cross-referenced.** Contrast findings cite `apca-contrast` / `wcag-contrast`; size findings cite `type-scale` / `component-sizing-principles`.

## Sources

- [Vercel Web Interface Guidelines](https://vercel.com/geist/introduction) — the WIG canon.
- [Material Design 3](https://m3.material.io/) — alternate canon for cross-checks.
- [Radix UI documentation](https://www.radix-ui.com/primitives) — accessible-component reference.
- [WCAG 2.2 Recommendation](https://www.w3.org/TR/WCAG22/) — the legal baseline.
- System-specific review layers (e.g. `udts-review`, incubating) compose on top of this generic lens.
