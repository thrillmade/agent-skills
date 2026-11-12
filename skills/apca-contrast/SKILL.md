---
version: "1.0.1"
digest: "18825ab46a63"  # is your copy current? github.com/thrillmade/thrill-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/thrill-skills"
name: apca-contrast
description: Use when picking text-on-surface contrast, auditing an accessibility budget, or generating a color against a specific contrast target. Names the APCA Lc target table (Lc 90 fluent body, 75 body minimum, 60 secondary, 45 large, 30 spot, 15 non-text), the APCACH inverse-composition rule, the Display-P3 meter rule (score on the same gamut the composer targeted, never sRGB-clamped), and WCAG 2.2 AA as an optional, off-by-default cross-check. Cite when an agent reaches for WCAG 2.x as the primary or required contrast model, or scores Lc through an sRGB-clamped meter — APCA is UDTS's required perceptual gate; WCAG is optional and advisory.
---

# APCA contrast

APCA (Accessible Perceptual Contrast Algorithm) is UDTS's primary contrast model. It reports contrast as **Lc** (lightness contrast) on a scale whose magnitude runs 0–105+ (the sign carries polarity) and is perceptually uniform across light and dark modes — unlike WCAG 2.x's luminance-ratio model, which over-reports contrast for dark colors and under-reports for light ones.

## When to use

- Picking a foreground color for a known background at a specific readability target.
- Auditing a token catalog's contrast budget.
- Generating a palette ladder where each stop targets a specific Lc band.
- Code review: flag any contrast pick that uses WCAG 2.x as the primary model instead of as a cross-check.

## When NOT to use

- Free-class tokens (illustration, decorative, brand-spot) that have no pairing obligation. APCA doesn't apply.
- Single-shot demos or one-off prototypes outside a token catalog where the result won't ship.

## Lc target table

| Lc | Role | Typical use |
|---|---|---|
| **90** | Fluent body | Body text intended for long-form reading. Preferred for paragraphs. |
| **75** | Body minimum | Smallest readable text — ≥ 24 px / 300 wt or ≥ 18 px / 400 wt. |
| **60** | Secondary content | Callouts, secondary headings, button labels at standard weights. |
| **45** | Large display | Display headings (32 px+). Quick scanning, not fluent reading. |
| **30** | Spot-readable | Placeholders, helper text, captions on dim surfaces. Absolute minimum. |
| **15** | Non-text UI | Dividers, focus rings, borders. Threshold for discernible non-text controls. |

Source: APCA spec at [git.apcacontrast.com](https://git.apcacontrast.com/documentation/README).

## Use APCACH inverse composition — don't pick a color and test

The default failure mode is **pick L and C, convert to hex, run APCA, eyeball Lc, adjust**. Don't.

The [APCACH](https://github.com/antiflasher/apcach) library inverts the APCA problem: declare the target Lc, hue, chroma cap, and background; the library searches for the OKLCH lightness that meets the target, keeping the closest tested result at or above it — no test-and-adjust loop. It states no tolerance and always returns a result, even a color that exists in no color space or misses an unattainable target, so the Verification check still runs.

```
INPUT  target_lc=75, hue=220, chroma_cap=auto, bg=oklch(0.99 0 0)
OUTPUT oklch(L, c_max, 220) — targets Lc 75 against the near-white surface
```

## Measure Lc on the composer's gamut, not sRGB

Score contrast on **Display P3 luminance** — apca-w3's `displayP3toY()`, not the default `sRGBtoY()` — matching the gamut the composer (apcach) targeted when it built the color. Clamping into sRGB before scoring a P3-composed color makes the meter disagree with the composer by up to a few Lc on saturated colors near the P3 edge, purely from the gamut mismatch, not from a real contrast problem. Use the SAME meter the composer verifies against, or exactness is unachievable by construction. Scoring a P3-composed color on a meter that clamps to sRGB is a defect to fix, not a scoring method to teach; when the composer targets sRGB (apcach's `colorSpace: 'srgb'`), the sRGB meter is the matched one.

## WCAG 2.2 AA cross-check (optional, off by default)

APCA is the native gate: a token that hits its declared Lc target ships. WCAG 2.2 AA is an **optional, off-by-default** cross-check, not a second required gate:

- **4.5:1** for normal text (< 18 pt, or < 14 pt bold: about 24 px and 18.66 px)
- **3:1** for large text (≥ 18 pt, or ≥ 14 pt bold) and non-text UI

When the cross-check is enabled and disagrees with APCA, treat it as a flag for review, not an automatic reject — see [wcag-contrast](../wcag-contrast/SKILL.md) for the disagreement table. APCA is exploratory at W3C (removed from the WCAG 3.0 Working Draft in 2023) but is UDTS's required perceptual model; WCAG 2.x is the version laws cite, and W3C does not expect WCAG 3 to be a completed standard for a few more years, which is why the optional check exists at all.

## Verification

After composing a contrast-bound color:

1. **APCA check:** `abs(apca_contrast(fg, bg))` is within ± 1 Lc of `declared_lc_target`, measured via `displayP3toY` (or whatever gamut the composer targeted) — not sRGB-clamped.
2. **Direction check:** APCA's Lc is signed by polarity (light text on a dark surface reads negative), which is why step 1 compares its magnitude; confirm the sign matches the declared role.
3. **WCAG cross-check (if enabled):** `wcag_ratio(fg, bg) ≥ declared_role_threshold` (4.5:1 or 3:1) — advisory, not gating.

If the APCA check fails, recompose. A failing optional WCAG cross-check is a review flag, not a reject.

## Cross-references

- **Routed here by:** [designing-a-design-system](../designing-a-design-system/SKILL.md) — the L1 dispatcher for building or extending a system.
- **REQUIRED BACKGROUND:** [oklch-color-space](../oklch-color-space/SKILL.md) for the underlying perceptual model and the APCACH library context.
- **For multi-hue palette generation:** [chroma-harmonization](../chroma-harmonization/SKILL.md) (the chroma cap at each Lc target is the cross-hue minimum).
- **For the WCAG side:** [wcag-contrast](../wcag-contrast/SKILL.md) for the cross-check thresholds and large-text rules.

## Sources

- [APCA spec and Lc tables](https://git.apcacontrast.com/documentation/README) — the canonical reference.
- [APCACH library](https://github.com/antiflasher/apcach) — inverse-composition primitive; its README warns that it always returns a result, even a color that does not exist.
- [apca-w3](https://github.com/Myndex/apca-w3) — the reference implementation: Lc is a signed float, negative for light text on dark, and `displayP3toY()` scores P3.
- [WCAG 3.0 Working Draft, July 2023](https://www.w3.org/TR/2023/WD-wcag-3.0-20230724/) — removed earlier material and no longer names APCA; [WCAG 3 introduction](https://www.w3.org/WAI/standards-guidelines/wcag/wcag3-intro/) — WCAG 3 not expected to be a completed standard for a few more years.
- [ADA Title II web rule](https://www.ada.gov/resources/2024-03-08-web-rule/) — one law that cites WCAG 2.x (2.1 AA).
- Gap figure for the sRGB-clamped meter: from practice, computed by scoring OKLCH colors at the P3 chroma ceiling both ways.
