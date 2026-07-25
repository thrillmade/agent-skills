---
name: chroma-harmonization
description: Use when constructing or auditing a multi-hue palette where all hues should appear equally saturated at each contrast stop. Names the per-stop chroma cap rule (take the minimum achievable chroma across hues at the stop), the gamut bottleneck pattern (blue at mid-L is the classic limiter in sRGB; Display P3 — UDTS's default compose gamut — reshapes it), and the relationship to UDTS's default `harmony` palette variant. Generalizes Evil Martians' Harmony algorithm.
---

# Chroma harmonization

Multi-hue palettes look unbalanced when one hue is more saturated than the rest at the same brightness stop — a neon outlier in a calm set, a washed-out blue next to a vibrant red. Chroma harmonization is the fix: at each stop, cap every hue at the **lowest-achievable chroma** across the set so the palette reads as a coherent family.

## When to use

- Constructing a multi-hue palette (3+ hues at the same set of contrast stops).
- Auditing an existing palette where one hue looks "off" against the others.
- Generating UDTS's default `harmony` palette variant.
- Code review: flag per-hue chroma values picked independently — propose the cross-hue cap.

## When NOT to use

- Single-hue palettes (no other hues to harmonize against — chroma is unconstrained by the procedure).
- Brand-spot or accent palettes where one hue *should* dominate. Use the `max` palette variant instead — see `oklch-color-space`.
- Palettes constrained to legacy sRGB-only output, where the narrower gamut shifts the bottleneck calculus back toward the classic blue-at-~220° limiter (the procedure still applies — Display P3 is the default target space; substitute the sRGB boundary deliberately for legacy-only catalogs).

## The algorithm

For each contrast stop in the palette (each L value):

1. For each hue in the set, find the maximum in-gamut chroma at that (L, H) in the target color space (**Display P3 by default** — UDTS composes end-to-end in P3 via apcach's `colorSpace: 'p3'`; sRGB only when a catalog is deliberately constrained to legacy-only output).
2. Take the **minimum** of those per-hue maxima. This is the stop's chroma ceiling.
3. Emit every hue at the stop using that ceiling.

```
for each stop L:
  c_max_per_hue = { h: max_chroma_in_gamut(L, h)  for h in hues }
  c_ceiling = min(c_max_per_hue.values())
  for each h in hues:
    emit oklch(L, c_ceiling, h)
```

The bottleneck pattern: at moderate lightness (L ≈ 0.5), **blue (~220°)** is the classic limiter in sRGB — its gamut is narrowest there. In Display P3 (the default compose gamut) the boundary is wider and reshaped, so blue is not guaranteed to be the tightest hue — treat the bottleneck as empirical per palette rather than assuming ~220° holds. At the extremes (L near 0 or 1) the gamut shrinks for all hues in either space, so the ceiling collapses naturally.

## Why the *minimum*, not the average

Average would push half the hues out of gamut at the bottleneck. Maximum would push the bottleneck hue out of gamut. Minimum is the only value where every hue can hit the target chroma in-gamut — which is the constraint that has to hold for emission.

## Headroom rule

Stay ≥ 10% below the computed ceiling. This headroom is for the **emission edge**, not the harmonization math itself: rounding when materializing the sRGB hex fallback (the compatibility export for legacy consumers — see `oklch-color-space`) and display-driver quirks can push a borderline-in-gamut P3 value out of gamut once flattened to 8-bit sRGB. A headroom margin prevents those fallback-materialization failures; it does not change the P3-native chroma math above.

## Relationship to UDTS palette variants

- **`harmony`** (UDTS default): this algorithm exactly. Every hue capped to the cross-hue minimum.
- **`max`**: each hue uncapped at its own gamut ceiling. Useful for brand or accent palettes where consistency yields to vibrancy.
- **`muted`**: harmony or max with an additional user-supplied flat chroma cap (e.g. C ≤ 0.06) — produces tonal greys like sand, stone, slate.
- **`flat`**: a single chroma across all stops for one hue (no cross-hue constraint).
- **`grey`**: zero chroma, always generated.

A UDTS catalog can ship multiple variants per hue and bind theme roles to specific (hue, variant) pairs — see the UDTS theme docs.

## Verification

After harmonizing a stop:

1. **Gamut check:** every emitted `oklch(L, c_ceiling, h)` is `displayable()` in the target color space.
2. **Visual check:** at the same stop, all hues should report identical (or near-identical) saturation in a side-by-side swatch. Use [oklch.com](https://oklch.com) or a culori-based tool.
3. **Headroom check:** the actual ceiling sits ≥ 10% below the computed **Display P3**-gamut maximum at every (L, H) in the set (verify the sRGB-fallback headroom separately, at emission).

If any hue clips at the ceiling or visually "pops," recompute with a tighter chroma cap.

## Cross-references

- **REQUIRED BACKGROUND:** `oklch-color-space` — the OKLCH primitive, the gamut-mapping rule.
- **For the contrast targets at each stop:** `apca-contrast` — the Lc targets that fix each L value.
- **For starting-hue palette construction before harmonization:** `palette-relationships`.

## Sources

- [Evil Martians' Harmony](https://evilmartians.com/opensource/harmony) — the original algorithm + interactive demo.
- [Evil Martians' Harmonizer](https://github.com/evilmartians/harmonizer) — Figma plugin implementation.
- UDTS's `harmony` palette variant — the canonical productized form of this algorithm.
