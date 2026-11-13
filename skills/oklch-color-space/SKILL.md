---
version: "1.0.2"
digest: "6c044711e042"  # is your copy current? github.com/thrillmade/thrill-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/thrill-skills"
name: oklch-color-space
description: Use when picking color values for a design-token system, constructing a palette around a starting hue, or generating colors against an accessibility contrast target. Names the OKLCH primitive ranges, the hue-angle naming convention, the gamut-mapping rule (Display P3 for computation, sRGB for the emitted fallback), and the APCACH inverse-composition approach for contrast-targeted color generation. Cite when an agent reaches for "pick a color then check contrast" — the inversion is the load-bearing move.
---

# OKLCH color space

OKLCH is the canonical perceptual color space for design-token work: L (lightness 0–1), C (chroma 0–~0.4), H (hue 0–360°). Equal numeric deltas in any channel produce equal perceived deltas, unlike HSL. Chroma is independent of lightness, so two stops of a palette can share saturation without sharing brightness.

## When to use

- Picking color values for any token system that will be exported as DTCG, CSS variables, Tailwind, etc.
- Constructing or auditing a palette around a starting hue.
- Generating a foreground color that must pair against a known background at a specific APCA Lc target.
- Reviewing color-picking decisions in code review — flag pick-and-test patterns and propose inverse composition.

## When NOT to use

- No token layer on disk — no catalog for this color to enter. A marketing splash's colors, picked inside a system with a token catalog, are still in scope.
- Color *spaces* (gradients, interpolation) where the design choice is the interpolation curve, not a fixed value — see the host platform's documentation for `color()` interpolation.

## Primitive ranges and naming

Every OKLCH primitive that lands in a catalog uses the hue-angle naming convention: `<name>-<angle>` (e.g. `red-30`, `teal-180`, `purple-280`). The name is mnemonic; the angle is load-bearing — adding a new hue does not renumber existing ones. Reserve generic accent labels (`accent-teal`, `primary`) for the theme layer above primitives, not the primitives themselves.

| Channel | Range | Notes |
|---|---|---|
| L | 0–1 | 0 = pure black, 1 = pure white; palette stops sit inside the ends (UDTS's land 0.10–0.99) |
| C | 0–~0.4 | Max in-gamut chroma varies by hue and L: in sRGB at L 0.5–0.7 it runs from ~0.085 (hue ~200) to ~0.32; **Display P3** (apcach's default `colorSpace: 'p3'`) is wider at every hue. Composing in P3, the sRGB ceiling binds only the emitted hex fallback |
| H | 0–360° | Cyclic; 0 ≈ red, 90 ≈ yellow, 180 ≈ teal/cyan, 270 ≈ blue, 360 = 0 |

## Compose to a contrast target — don't pick L and test

The default failure mode is **pick L and C, convert to hex, run APCA, adjust, repeat**. Don't.

Use **APCACH inverse composition** (the [APCACH](https://github.com/antiflasher/apcach) library): declare the target Lc, hue, chroma cap, and background; the library searches for the L that meets the target, keeping the closest tested result at or above it — without a test-and-adjust loop. It states no tolerance and always returns a result, even a color that exists in no color space, so the contrast check below still runs.

```
INPUT  target_lc=75, hue=220, chroma_cap=auto, bg=oklch(0.99 0 0)
PROCESS  binary-search L over [0, 1] for apca_contrast(oklch(L, c_max, 220), bg) ≈ 75
OUTPUT  oklch(L, c_max, 220) — targets Lc 75 against the near-white surface
```

This applies to every contrast-bound token (text, surface, border, ui). For free-class tokens (illustration, decorative, brand-spot) the contrast obligation doesn't apply — compose freely.

**REQUIRED BACKGROUND:** Use [apca-contrast](../apca-contrast/SKILL.md) for the Lc target table (Lc 90 fluent body, 75 body minimum, 60 secondary, etc.) and the WCAG 2.2 AA cross-check rule.

## Gamut mapping

The **compose space is P3-native**: chroma caps, gamut checks, and APCACH composition all default to Display P3 — apcach's `apcach()` and `cssToApcach()` default `colorSpace` to `'p3'`, and `maxChroma()` searches the space `apcach()` hands it. Test P3 with culori's `inGamut('p3')`; its `displayable()` tests sRGB.

sRGB legitimately enters the pipeline at exactly two points — nowhere else:

1. **Emission edge (fallback export).** Materializing the hex fallback for legacy consumers: gamut-map the OKLCH source into sRGB and clamp chroma at that narrower boundary. Emit the Display P3 (`figma-p3`) representation directly wherever the target supports it; fall back to the sRGB clamp only for the compatibility hex export.
2. **WCAG 2 cross-check.** WCAG 2.2 AA contrast is only defined against sRGB-space luminance, so the cross-check step is sRGB by definition, not a compromise.

The background anchor is not a third point. apcach takes it as a CSS color string and accepts `oklch()` and `display-p3` as well as hex, so pass it as `oklch()`; a wrapper that converts it to sRGB hex first rounds it to 8 bits and clips anything outside sRGB, on every compose call.

**Silent failure — check the meter's gamut:** a meter that gamut-clamps both colors into sRGB before scoring disagrees with a P3 composer by up to a few Lc on saturated colors near the P3 edge, enough to fail a ± 1 Lc check, and nothing errors. Confirm which gamut your meter scores on; never assume it is P3 ([apca-contrast](../apca-contrast/SKILL.md) owns the fix).

Practical rule for picking a chroma cap: compose against the **Display P3 ceiling** and stay ≥10% below it at your declared (L, H) — this protects the eventual sRGB-fallback materialization and display-driver quirks from pushing the color out of gamut. Check against **P3** (`inGamut('p3')`) before shipping; check sRGB (`displayable()`) only when validating the emitted hex fallback.

**The actual doctrine:** sRGB/hex intermediates are correct only at the two points above. Anywhere else — picking L or C, doing hue math, passing apcach its background, or resolving a gamut boundary that isn't the fallback edge or the WCAG check — stay in OKLCH end-to-end (culori objects, or an `oklch()` string where an API takes a string). An 8-bit hex round-trip outside those two points quantizes precision a P3-native pipeline doesn't need, and is the pattern to flag in review.

## Verification

After picking an OKLCH value:

1. **Range check:** `0 ≤ L ≤ 1`, `0 ≤ C ≤ 0.4`, `0 ≤ H < 360`.
2. **Gamut check:** `inGamut('p3')(oklch(L C H))` returns true (**Display P3 by default**; `displayable()`, the sRGB test, only for the emitted hex fallback).
3. **Round-trip check (fallback-emission path only):** convert OKLCH → sRGB hex → OKLCH; the round-trip delta on L and C should be < 0.01. This validates the emitted hex fallback.
4. **Contrast check (contrast-bound tokens):** the magnitude of APCA Lc against the declared pairing background is within ± 1 Lc of the target.

If any of the four fails, fix the value before emitting the token.

## Cross-references

- **Routed here by:** [designing-a-design-system](../designing-a-design-system/SKILL.md) — the L1 dispatcher for building or extending a system.
- **REQUIRED BACKGROUND:** [apca-contrast](../apca-contrast/SKILL.md) for the Lc target table, when contrast Lc applies, and the WCAG cross-check.
- **REQUIRED for multi-hue palettes:** [chroma-harmonization](../chroma-harmonization/SKILL.md) — cap chroma at the lowest-achievable value across all hues at the same stop, so no hue is a neon outlier.
- **For starting-hue palette construction:** [palette-relationships](../palette-relationships/SKILL.md) — analogous, complementary, triadic, etc., as hue-angle math.

## Sources

- [Björn Ottosson's OKLCH spec](https://bottosson.github.io/posts/oklab/) — the math.
- [APCACH library](https://github.com/antiflasher/apcach) — inverse composition primitive; its README lists the background formats it accepts and warns it always returns a result.
- [culori API](https://culorijs.org/api/) — `displayable()` is the sRGB test; `inGamut(mode)` tests other gamuts.
- Chroma ceilings by hue and L: from practice, computed from the OKLab and CSS Color 4 matrices.
- [oklch.com](https://oklch.com) — interactive picker for sanity-checks.
- The [apca-contrast](../apca-contrast/SKILL.md) and [chroma-harmonization](../chroma-harmonization/SKILL.md) skills in this catalog.
