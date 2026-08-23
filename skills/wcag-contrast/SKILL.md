---
version: "c2c3bd386622"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: wcag-contrast
description: Use when verifying a color pair meets WCAG 2.2 AA contrast requirements as an optional cross-check on APCA-driven generation, or when auditing a token catalog or design for legal-baseline accessibility compliance. Names the 4.5:1 normal-text rule, the 3:1 large-text rule, the size threshold for "large" stated in points (≥ 18 pt regular ≈ 24 CSS px, OR ≥ 14 pt bold ≈ 18.67 CSS px — not pixels), the SC 1.4.11 non-text rule, SC 2.4.13 focus appearance (AAA — the AA hooks are 1.4.11 and 2.4.11), and the optional, off-by-default role this check plays alongside APCA's required gate. Cite when an agent treats WCAG as the *primary* or a *required* contrast model, or writes the large-text threshold as "14 px bold / 18 px regular" — UDTS uses WCAG only as an optional cross-check, APCA is the required gate, and WCAG sizes are in points.
---

# WCAG 2.2 AA contrast

WCAG 2.2 Level AA is the **legal-baseline** contrast standard for most jurisdictions until WCAG 3 ships (≥ 2029). UDTS uses it as an **optional, off-by-default** cross-check alongside its primary and only required model, APCA — enabling this check doesn't change what ships; APCA's Lc target is the gate.

## When to use

- Verifying a foreground / background pair after APCA composition.
- Auditing an existing token catalog or design for legal-baseline compliance.
- Code review on PRs that change color tokens, hover states, or focus indicators.

## When NOT to use

- As the *primary* contrast model when generating new colors. APCACH inverse composition against an APCA Lc target is the generator; this is the cross-check.
- For free-class tokens (illustration, decorative, brand-spot) — they carry no pairing obligation. See [apca-contrast](../apca-contrast/SKILL.md) for the class system.

## The rules

| SC | Level | Rule | Threshold | Applies to |
|---|---|---|---|---|
| 1.4.3 | AA | Normal text | **4.5:1** | Text < 18 pt (24 CSS px) regular OR < 14 pt (~18.67 CSS px) bold |
| 1.4.3 | AA | Large text | **3:1** | Text ≥ 18 pt (24 CSS px) regular OR ≥ 14 pt (~18.67 CSS px) bold |
| 1.4.11 | AA | Non-text contrast | **3:1** | UI components, focus indicators, graphical objects |
| 2.4.11 | **AA** (added in 2.2) | Focus not obscured (minimum) | n/a | The focused control must not be **entirely** hidden by author content — sticky headers, cookie bars, drawers |
| 2.4.13 | **AAA** (added in 2.2) | Focus appearance | Specific minimums | Indicator ≥ 2 px perimeter and 3:1 against unfocused. **AAA — cite as an enhancement, never as an AA failure** |
| 2.4.12 | AAA (added in 2.2) | Focus not obscured (enhanced) | n/a | Focus indicator must not be obscured **at all** by author content |

**WCAG sizes are in points, not pixels** — a frequent miss. 1 pt = 1.333 CSS px, so:

- 18 pt regular = **24 CSS px** (not 18 px)
- 14 pt bold = **~18.67 CSS px** (not 14 px)

Text at 16 CSS px is *not* "large" even when bold; it falls under the 4.5:1 normal-text rule.

## Computing the ratio

```
L = 0.2126·R_lin + 0.7152·G_lin + 0.0722·B_lin   (sRGB-linearized)
ratio = (L_lighter + 0.05) / (L_darker + 0.05)
```

Always linearize the RGB channels before computing luminance (apply the sRGB gamma reversal: `c <= 0.04045 ? c/12.92 : ((c + 0.055)/1.055)^2.4`). Skipping linearization gives wrong answers — usually undercounting contrast for mid-tones.

For OKLCH-source colors, gamut-map to sRGB first (clamp out-of-gamut chroma at the (L, H) boundary), then apply the formula.

## When WCAG and APCA disagree

WCAG's relative-luminance model over-reports contrast for dark colors and under-reports for very light ones, so APCA and WCAG diverge at the extremes (very dark + very dark, very light + very light, very saturated mid-tones). APCA is the gate; WCAG, when the cross-check is enabled, is advisory only:

- **WCAG passes, APCA fails:** the pairing meets the legal threshold but is *perceptually* hard to read. The APCA failure blocks emission regardless of WCAG. (Most common in the dark-on-dark range.)
- **APCA passes, WCAG fails:** the pairing reads fine perceptually and ships — the WCAG miss is a flag for manual legal-compliance review, not a block. (Most common in the very-light range.)
- **Both pass:** ship, no flag.

## Verification

For each contrast-bound pairing:

1. Compute the WCAG ratio with sRGB-linearized luminance.
2. Apply the role-appropriate threshold (4.5:1 normal text, 3:1 large text or non-text).
3. Confirm the bold-text size rule in **points** — 14 pt bold (~18.67 CSS px) counts as large; 14 CSS px bold does not. Same for 18 pt regular (= 24 CSS px), not 18 CSS px.
4. Cross-check the APCA Lc (see [apca-contrast](../apca-contrast/SKILL.md)) — APCA is the gate.
5. Flag (don't reject) if this WCAG check fails while APCA passes; an APCA failure is what blocks emission.

## Cross-references

- **Routed here by:** [designing-a-design-system](../designing-a-design-system/SKILL.md) — the L1 dispatcher for building or extending a system.
- **REQUIRED BACKGROUND:** [apca-contrast](../apca-contrast/SKILL.md) — the primary contrast model. WCAG is the cross-check; APCA is the generator target.
- **For the underlying color space:** [oklch-color-space](../oklch-color-space/SKILL.md) — OKLCH source values must be gamut-mapped to sRGB before applying the WCAG formula.

## Sources

- [WCAG 2.2 Recommendation — SC 1.4.3](https://www.w3.org/TR/WCAG22/#contrast-minimum) — text contrast.
- [SC 1.4.11 — non-text contrast](https://www.w3.org/TR/WCAG22/#non-text-contrast).
- [SC 2.4.11 — focus not obscured, minimum (AA, added in 2.2)](https://www.w3.org/TR/WCAG22/#focus-not-obscured-minimum) — the AA hook for a focus ring being covered.
- [SC 2.4.13 — focus appearance (**AAA**, added in 2.2)](https://www.w3.org/TR/WCAG22/#focus-appearance). Verified against the published Recommendation 2026-08-15; this skill previously said AA.
- [SC 2.4.12 — focus not obscured, enhanced (AAA, added in 2.2)](https://www.w3.org/TR/WCAG22/#focus-not-obscured-enhanced).
- [Contrast Checker, WebAIM](https://webaim.org/resources/contrastchecker/) — sanity-check tool that matches the spec.
