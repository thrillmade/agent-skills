---
name: oklch-color-space
description: Use when picking color values for a design-token system, constructing a palette around a starting hue, or generating colors against an accessibility contrast target. Names the OKLCH primitive ranges, the hue-angle naming convention, the gamut-mapping rule (Display P3 for computation, sRGB for the emitted fallback), and the APCACH inverse-composition approach for guaranteed-contrast color generation. Cite when an agent reaches for "pick a color then check contrast" — the inversion is the load-bearing move.
---

# OKLCH color space

OKLCH is the canonical perceptual color space for design-token work: L (lightness 0–1), C (chroma 0–~0.4), H (hue 0–360°). Equal numeric deltas in any channel produce equal perceived deltas, unlike HSL. Chroma is independent of lightness, so two stops of a palette can share saturation without sharing brightness.

## When to use

- Picking color values for any token system that will be exported as DTCG, CSS variables, Tailwind, etc.
- Constructing or auditing a palette around a starting hue.
- Generating a foreground color that must pair against a known background at a specific APCA Lc target.
- Reviewing color-picking decisions in code review — flag pick-and-test patterns and propose inverse composition.

## When NOT to use

- Single one-off color picks that aren't entering a token catalog (a marketing landing-page splash, a one-time illustration). The convention overhead isn't earned.
- Color *spaces* (gradients, interpolation) where the design choice is the interpolation curve, not a fixed value — see the host platform's documentation for `color()` interpolation.

## Primitive ranges and naming

Every OKLCH primitive that lands in a catalog uses the hue-angle naming convention: `<name>-<angle>` (e.g. `red-30`, `teal-180`, `purple-280`). The name is mnemonic; the angle is load-bearing — adding a new hue does not renumber existing ones. Reserve generic accent labels (`accent-teal`, `primary`) for the theme layer above primitives, not the primitives themselves.

| Channel | Range | Notes |
|---|---|---|
| L | 0–1 | 0 = pure black, 1 = pure white; UDTS palette stops typically land 0.10–0.99 |
| C | 0–~0.4 | Theoretical max varies by hue; UDTS composes in **Display P3** by default (apcach's `colorSpace: 'p3'`), whose practical ceiling at moderate L is wider than sRGB's ~0.16–0.20 — the sRGB figure applies only to the emitted hex fallback, not the compute-time ceiling |
| H | 0–360° | Cyclic; 0 ≈ red, 90 ≈ yellow, 180 ≈ teal/cyan, 270 ≈ blue, 360 = 0 |

## Compose to a contrast target — don't pick L and test

The default failure mode is **pick L and C, convert to hex, run APCA, adjust, repeat**. Don't.

UDTS uses **APCACH inverse composition** (the [APCACH](https://github.com/antiflasher/apcach) library): declare the target Lc, hue, chroma cap, and background; the library binary-searches for the L that hits the target within ± 1 Lc. The output is guaranteed to satisfy the contrast obligation — without a test-and-adjust loop.

```
INPUT  target_lc=75, hue=220, chroma_cap=auto, bg=oklch(0.99 0 0)
PROCESS  binary-search L over [0, 1] for apca_contrast(oklch(L, c_max, 220), bg) ≈ 75
OUTPUT  oklch(L, c_max, 220) — hits Lc 75 against the near-white surface
```

This applies to every contrast-bound token (text, surface, border, ui). For free-class tokens (illustration, decorative, brand-spot) the contrast obligation doesn't apply — compose freely.

**REQUIRED BACKGROUND:** Use [apca-contrast](../apca-contrast/SKILL.md) for the Lc target table (Lc 90 fluent body, 75 body minimum, 60 secondary, etc.) and the WCAG 2.2 AA cross-check rule.

## Gamut mapping

The **compose space is P3-native**: chroma caps, `displayable()` checks, and APCACH composition all default to Display P3 (UDTS's compose gamut) — apcach's `apcach()`, `cssToApcach()`, and `maxChroma()` all default `colorSpace` to `'p3'`, and UDTS's wrapper never overrides that default.

sRGB legitimately enters the pipeline at exactly three points — nowhere else:

1. **Emission edge (fallback export).** Materializing the hex fallback for legacy consumers: gamut-map the OKLCH source into sRGB and clamp chroma at that narrower boundary. Emit the Display P3 (`figma-p3`) representation directly wherever the target supports it; fall back to the sRGB clamp only for the compatibility hex export.
2. **Background-anchor round-trip (apcach's own API shape).** APCACH inverse composition takes its background as a CSS color string — it has no OKLCH-object entry point for the anchor color. UDTS's compose wrapper round-trips the OKLCH background through sRGB hex on *every* compose call to satisfy that string-shaped API; apcach then converts it into P3 internally for the actual composition. This happens mid-computation, on every generated palette variant — it's correct because the library boundary forces it, not because the pipeline chose to compute in sRGB there.
3. **WCAG 2 cross-check.** WCAG 2.2 AA contrast is only defined against sRGB-space luminance, so the cross-check step is sRGB by definition, not a compromise.

**Known open gap — do not teach as fixed:** the shipped APCA *meter* still gamut-clamps both colors into sRGB before scoring, on every call path, while the *composer* (apcach) targets P3. That composer/meter mismatch is a documented, tolerated gap in the codebase today, not something later resolved — never state that the live meter measures in P3.

Practical rule for picking a chroma cap: compose against the **Display P3 ceiling** and stay ≥10% below it at your declared (L, H) — this protects the eventual sRGB-fallback materialization and display-driver quirks from pushing the color out of gamut. Use a culori/`displayable()` check against **P3** before shipping; check sRGB separately only when validating the emitted hex fallback.

**The actual doctrine:** sRGB/hex intermediates are correct only at the three points above. Anywhere else — picking L or C, doing hue math, or resolving a gamut boundary that isn't the fallback edge, the WCAG check, or apcach's background-string requirement — stay in culori-native OKLCH objects end-to-end. An 8-bit hex round-trip outside those three points quantizes precision a P3-native pipeline doesn't need, and is the pattern to flag in review.

## Cross-references

- **REQUIRED BACKGROUND:** [apca-contrast](../apca-contrast/SKILL.md) for the Lc target table, when contrast Lc applies, and the WCAG cross-check.
- **REQUIRED for multi-hue palettes:** [chroma-harmonization](../chroma-harmonization/SKILL.md) — cap chroma at the lowest-achievable value across all hues at the same stop, so no hue is a neon outlier.
- **For starting-hue palette construction:** [palette-relationships](../palette-relationships/SKILL.md) — analogous, complementary, triadic, etc., as hue-angle math.

## Verification

After picking an OKLCH value:

1. **Range check:** `0 ≤ L ≤ 1`, `0 ≤ C ≤ 0.4`, `0 ≤ H < 360`.
2. **Gamut check:** `displayable(oklch(L C H))` returns true for the target color space (**Display P3 by default** — UDTS's compute gamut; check sRGB separately only for the emitted hex fallback).
3. **Round-trip check (fallback-emission path only):** convert OKLCH → sRGB hex → OKLCH; the round-trip delta on L and C should be < 0.01. This validates the emitted hex fallback. (A different sRGB round-trip happens inside APCACH composition for the background anchor — see Gamut mapping; that one is exercised by the compose step's own Lc tolerance, not by this check.)
4. **Contrast check (contrast-bound tokens):** APCA Lc against the declared pairing background hits the target ± 1 Lc.

If any of the four fails, fix the value before emitting the token.

## Sources

- [Björn Ottosson's OKLCH spec](https://bottosson.github.io/posts/oklab/) — the math.
- [APCACH library](https://github.com/antiflasher/apcach) — inverse composition primitive.
- [oklch.com](https://oklch.com) — interactive picker for sanity-checks.
- The [apca-contrast](../apca-contrast/SKILL.md) and [chroma-harmonization](../chroma-harmonization/SKILL.md) skills in this catalog.
