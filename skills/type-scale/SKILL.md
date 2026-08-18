---
version: "92272bfa625d"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: type-scale
description: Use when designing, auditing, or extending a typography size scale built on a modular ratio. Names the canonical preset ratios (1.067 minor second → 1.618 golden), the picking heuristic by context (UI vs editorial vs marketing), the stops-up / stops-down convention (−2 to +8 default), the rounding rule (round to nearest integer px, rem derived after), and the upper-bound on ratios for product UI. Cite when an agent proposes a ratio above 1.5 for a product system or hand-picks scale steps outside a modular ratio.
---

# Type scale

A modular type scale derives every font size from a single ratio applied to a base size. The discipline is choosing the ratio for the system's *typical* surface — UI density, editorial reading, marketing impact — then committing to it across the whole scale rather than per-role.

## When to use

- Designing a new typography scale from a base font size and a context (product UI / editorial / marketing).
- Auditing an existing scale where sizes feel off-rhythm or step gaps look inconsistent.
- Extending a scale up or down (e.g. adding a display rung above the existing max).
- Code review: flag hand-picked sizes outside a modular ratio, ratios above 1.5 in product systems, or rems-as-source-of-truth (always derive rem from rounded px, not the other way around).

## When NOT to use

- Editorial-only books / long-form prose where the ratio is a typographer's pick and a modular scale would over-constrain. The discipline still applies to documenting the choices, not to forcing a ratio.
- Single-size systems (rare; usually a stopgap during initial system definition).

## Canonical preset ratios

| Ratio | Name | Best for |
|---|---|---|
| 1.067 | Minor second | Very dense UI; gaps so small that most stops feel near-identical |
| 1.125 | Major second | Dense UI (admin consoles, data-heavy tools); subtle hierarchy |
| 1.200 | Minor third | **A common default for product UI** — balanced, readable, distinct headings |
| 1.250 | Major third | Slightly more dramatic UI; comfortable for mixed product + marketing |
| 1.333 | Perfect fourth | Editorial leaning; large gap between body and H1 |
| 1.414 | Augmented fourth | Editorial; sharp hierarchy |
| 1.500 | Perfect fifth | Marketing-leaning; aggressive but still usable |
| 1.618 | Golden | Hero / display only; ratios above ~1.5 break down for product UI because step gaps grow too fast |

**Upper bound:** ratios above 1.5 rarely work for product UI — by step +5 the size is huge, and H4/H5 stop feeling distinct from body. Reserve 1.5 / 1.618 for editorial or marketing systems.

## Stops-up / stops-down

A common default range is **step −2 to step +8**. Step 0 is the base size.

```
size(n) = round(base × ratio^n)
rem(n)  = size(n) / 16
```

Typical role mapping for a 16 px base, 1.200 ratio:

| Step | px | rem | Typical role |
|---|---|---|---|
| −2 | 11 | 0.6875 | Micro, legal, fine print |
| −1 | 13 | 0.8125 | Small UI, metadata |
| 0  | 16 | 1.0000 | Body, base |
| +1 | 19 | 1.1875 | Lead paragraph, H5 |
| +2 | 23 | 1.4375 | H4 |
| +3 | 28 | 1.7500 | H3 |
| +4 | 33 | 2.0625 | H2 |
| +5 | 40 | 2.5000 | H1 |
| +6 | 48 | 3.0000 | Display |
| +7 | 57 | 3.5625 | Hero |
| +8 | 69 | 4.3125 | Marketing splash |

The range is generous so a single scale spans dense UI through marketing without per-surface forking.

## Rounding rules

Round font sizes to integer px by default:

1. Compute the raw size: `base × ratio^n`.
2. Round to the **nearest integer px**. Sub-pixel sizes render inconsistently across browsers and OS hinting.
3. If two adjacent steps would round to the same px, bump the larger one up by 1 px to preserve monotonic spacing.
4. Derive rem **from the rounded px**, not from the raw value. `rem = rounded_px / 16`. The other direction (round the rem) compounds with the px round and produces drift.

Rounding can be disabled for math-pure systems where fractional sizes are tolerated downstream. Document the choice if you turn it off.

## Cross-references

- **Routed here by:** [designing-a-design-system](../designing-a-design-system/SKILL.md) — the L1 dispatcher for building or extending a system.
- **REQUIRED BACKGROUND:** [line-height-grid](../line-height-grid/SKILL.md) — every size in the scale needs a line-height; the lh-ui (× 1.20) / lh-prose (× 1.50) tracks pair with this scale.
- **For role assignment after picking sizes:** the typography-styles spec (compound tokens combining size + lh + tracking + weight + paragraph margin).
- **For the base size choice:** 16 px is the common base; smaller bases (14 px) are valid for dense product UI but require revisiting line-heights and tap targets.

## Verification

After picking a ratio and emitting the scale:

1. **Monotonicity:** every step is strictly larger than the previous; no two adjacent steps share a px value after rounding.
2. **Round-trip:** `rem(n) × 16 = px(n)` exactly (no drift from re-rounding).
3. **Distinguishability at small sizes:** −1 and −2 are visually distinct (a ratio + base combo where they round to the same px is broken; pick a tighter ratio or larger base).
4. **Upper-bound sanity:** if the +5 step is unusable for headings in your system, the ratio is too aggressive; drop to a tighter preset.

## Sources

- [Modular Scale by Tim Brown](https://www.modularscale.com/) — interactive picker for the canonical ratios.
- [Type Scale](https://typescale.com/) — same idea with live preview.
- One worked instantiation: the UDTS typography foundations (its L2 skills are incubating in thrillmade/tokenomics).
