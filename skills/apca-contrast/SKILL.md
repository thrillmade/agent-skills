---
version: "c894961136c7"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: apca-contrast
description: Use when picking text-on-surface contrast, auditing an accessibility budget, or generating a color against a specific contrast target. Names the APCA Lc target table (Lc 90 fluent body, 75 body minimum, 60 secondary, 45 large, 30 spot, 15 non-text), the APCACH inverse-composition rule, the Display-P3 meter rule (score on the same gamut the composer targeted, never sRGB-clamped), and WCAG 2.2 AA as an optional, off-by-default cross-check. Cite when an agent reaches for WCAG 2.x as the primary or required contrast model, or scores Lc through an sRGB-clamped meter — APCA is UDTS's required perceptual gate; WCAG is optional and advisory.
---

# APCA contrast

APCA (Accessible Perceptual Contrast Algorithm) is UDTS's primary contrast model. It reports contrast as **Lc** (lightness contrast) on a 0–105+ scale and is perceptually uniform across light and dark modes — unlike WCAG 2.x's luminance-ratio model, which over-reports contrast for dark colors and under-reports for light ones.

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

Source: APCA spec at [git.apcacontrast.com](https://git.apcacontrast.com/documentation/README). The table maps directly to UDTS's default 11-stop palette ladder (see [foundations/color.md in token.design / UDTS docs](https://token.design)).

## Use APCACH inverse composition — don't pick a color and test

The default failure mode is **pick L and C, convert to hex, run APCA, eyeball Lc, adjust**. Don't.

UDTS uses the [APCACH](https://github.com/antiflasher/apcach) library, which inverts the APCA problem: declare the target Lc, hue, chroma cap, and background; the library binary-searches for the OKLCH lightness that hits the target. The output is guaranteed to satisfy the contrast obligation within ± 1 Lc — no test-and-adjust loop.

```
INPUT  target_lc=75, hue=220, chroma_cap=auto, bg=oklch(0.99 0 0)
OUTPUT oklch(L, c_max, 220) — hits Lc 75 against the near-white surface
```

## Measure Lc on the composer's gamut, not sRGB

Score contrast on **Display P3 luminance** — apca-w3's `displayP3toY()`, not the default `sRGBtoY()` — matching the gamut the composer (apcach) targeted when it built the color. Clamping into sRGB before scoring a P3-composed color makes the meter disagree with the composer by several Lc, purely from the gamut mismatch, not from a real contrast problem. Use the SAME meter the composer verifies against, or exactness is unachievable by construction. (See [oklch-color-space](../oklch-color-space/SKILL.md)'s "Known open gap" note: the shipped meter doesn't do this yet — that's a defect to fix, not a reason to teach sRGB-clamped scoring as correct.)

## WCAG 2.2 AA cross-check (optional, off by default)

APCA is the native gate: a token that hits its declared Lc target ships. WCAG 2.2 AA is an **optional, off-by-default** cross-check, not a second required gate:

- **4.5:1** for normal text (< 18 px or < 14 px bold)
- **3:1** for large text (≥ 18 px or ≥ 14 px bold) and non-text UI

When the cross-check is enabled and disagrees with APCA, treat it as a flag for review, not an automatic reject — see [wcag-contrast](../wcag-contrast/SKILL.md) for the disagreement table. APCA is exploratory at W3C (removed from the WCAG 3.0 Working Draft in 2023) but is UDTS's required perceptual model; WCAG 2.2 remains the operative legal standard until WCAG 3 ships (≥ 2029), which is why the optional check exists at all.

## Verification

After composing a contrast-bound color:

1. **APCA check:** `apca_contrast(fg, bg) ≈ declared_lc_target` within ± 1 Lc, measured via `displayP3toY` (or whatever gamut the composer targeted) — not sRGB-clamped.
2. **Direction check:** UDTS Lc is unsigned and direction-aware; ensure the polarity matches the declared role (light text on dark surface vs dark text on light surface use the same Lc magnitude).
3. **WCAG cross-check (if enabled):** `wcag_ratio(fg, bg) ≥ declared_role_threshold` (4.5:1 or 3:1) — advisory, not gating.

If the APCA check fails, recompose. A failing optional WCAG cross-check is a review flag, not a reject.

## Cross-references

- **Routed here by:** [designing-a-design-system](../designing-a-design-system/SKILL.md) — the L1 dispatcher for building or extending a system.
- **REQUIRED BACKGROUND:** [oklch-color-space](../oklch-color-space/SKILL.md) for the underlying perceptual model and the APCACH library context.
- **For multi-hue palette generation:** [chroma-harmonization](../chroma-harmonization/SKILL.md) (the chroma cap at each Lc target is the cross-hue minimum).
- **For the WCAG side:** [wcag-contrast](../wcag-contrast/SKILL.md) for the cross-check thresholds and large-text rules.

## Sources

- [APCA spec and Lc tables](https://git.apcacontrast.com/documentation/README) — the canonical reference.
- [APCACH library](https://github.com/antiflasher/apcach) — inverse-composition primitive.
- [Myndex APCA discussion](https://github.com/Myndex/apca-w3) — historical context for WCAG 3 removal.
