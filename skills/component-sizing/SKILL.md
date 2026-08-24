---
version: "1.0.0"
digest: "4b8024eca633"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: https://github.com/thrillmade/agent-skills
name: component-sizing
description: |
  SUPERSEDED by `component-sizing-principles` (L0) + `udts-component-sizing-ladders` (L2, incubating) — see the design-catalog section of the README; kept unchanged during the tokenomics migration window, new work should load the successors. Use when picking a button / input / chip / badge height, or proposing a component-height ladder for a density mode. Names UDTS's curated 5-rung height ladders per density — balanced (4/8 grid) at 24, 32, 40, 48, 56; dense (2/4 grid) at 24, 28, 36, 44, 52; spacious (4/16 grid) at 32, 48, 64, 80, 96. Also names the curated icon-size ladder (12, 16, 24, 32, 40, 48), the font-size pairing per rung, the rule for which rungs are interactive (≥ 24 CSS px WCAG 2.5.8 floor — but interactive rungs start at the `sm` 32 px tier; `xs` 24 px is non-interactive only), and why heights and icon sizes are curated, not formula-derived.
---

# Component sizing

Component heights and icon sizes are **curated** in UDTS, not formula-derived. The rungs are picked so each height pairs cleanly with a font from the type scale, an icon from the icon ladder, and tap-target requirements — and so each rung distinguishes visually from its neighbors at every density.

## When to use

- Picking a height for a button, input, chip, badge, dropdown, or any other rectangular interactive control.
- Proposing a control-height ladder for a new density mode.
- Auditing one-off heights (`h-7`, `h-9`, `h-11`) drifting across a codebase.
- Code review: flag heights outside the curated ladder; propose the nearest curated rung with rationale.

## When NOT to use

- One-off marketing CTAs designed for a specific page (e.g. hero buttons at 72 px). The ladder doesn't apply to single-surface designs.
- Non-rectangular controls (circular avatars, range thumbs) where the size is governed by the icon or asset, not a height token.

## The curated ladders

UDTS ships three default density modes. Each is a 5-rung ladder labeled `xs` / `sm` / `md` / `lg` / `xl` — interactive rungs start at `sm` per the WCAG 2.5.8 floor (see [spacing-system](#cross-references)).

### Balanced (UDTS default, 4/8 grid)

| Rung | Height | Font-size | Icon-size | Interactive? |
|---|---|---|---|---|
| `xs` | 24 px | 12 px | 12 | **No** — badges, read-only chips |
| `sm` | 32 px | 14 px | 16 | yes |
| `md` | 40 px | 14 px | 16 | yes (default) |
| `lg` | 48 px | 16 px | 24 | yes |
| `xl` | 56 px | 16 px | 24 | yes (CTA) |

### Dense (2/4 grid)

| Rung | Height | Font-size | Icon-size | Interactive? |
|---|---|---|---|---|
| `xs` | 24 px | 12 px | 12 | No |
| `sm` | 28 px | 12 px | 12 | yes |
| `md` | 36 px | 14 px | 16 | yes (default) |
| `lg` | 44 px | 14 px | 16 | yes |
| `xl` | 52 px | 16 px | 24 | yes (CTA) |

### Spacious (4/16 grid)

| Rung | Height | Font-size | Icon-size | Interactive? |
|---|---|---|---|---|
| `xs` | 32 px | 14 px | 16 | yes (xs floor lifts in spacious) |
| `sm` | 48 px | 16 px | 24 | yes |
| `md` | 64 px | 18 px | 24 | yes (default) |
| `lg` | 80 px | 20 px | 32 | yes |
| `xl` | 96 px | 24 px | 40 | yes (CTA) |

## The curated icon-size ladder

UDTS's canonical icon sizes: **12, 16, 24, 32, 40, 48**. Picked because:

- These are the sizes at which Material Icons, Lucide, Heroicons, and Phosphor families render cleanly without hairline glitches.
- They pair with the font-sizes from [type-scale](../type-scale/SKILL.md) naturally (icon ≥ font-size at every rung; never undersized).
- They subdivide into 4 px steps at the small end (where it matters for inline alignment) and 8 px steps at the large end (where it doesn't).

**Don't formula-derive icon sizes.** A height-to-icon ratio (e.g. `icon = height / 2`) produces sizes like 14, 18, 22, 28 — every one of which renders worse than the curated neighbor.

## Why curated, not formula-derived

A formula `(height) → font-size → icon-size` produces *mathematically clean* values that *render poorly*:

- Heights at every 4 px (24, 28, 32, 36, 40, ...) create visually indistinct rungs — `28` and `32` are hard to tell apart in a stack.
- Font sizes outside the type-scale (e.g. 13, 15, 17) clash with the rest of the typography system.
- Icon sizes outside the curated set glitch at common zoom levels.

The curated 5-rung ladders give visual distinguishability at each rung, predictable font and icon pairing, and tap-target safety. The trade-off is less flexibility — but design systems benefit from less flexibility at this layer.

## The WCAG 2.5.8 floor

Interactive control heights start at **24 CSS px** per WCAG 2.5.8 AA Target Size (added in WCAG 2.2). In practice:

- **Balanced and dense:** `xs` (24 / 24 px) is **non-interactive only**. Interactive rungs start at `sm` (32 / 28 px). The 24 px rung exists for badges, read-only chips, density tags.
- **Spacious:** `xs` lifts to 32 px, so the entire ladder is interactive-safe.

Fails of this rule are one of the most common WCAG 2.2 audit misses.

## Picking a rung

Default heuristic:

- **Default button / input:** `md`. Use the same rung for buttons and their associated inputs so they align horizontally in a form.
- **Compact density toggle (dense table cell):** `sm`.
- **Primary CTA / hero button:** `lg` or `xl` depending on prominence.
- **Density tag, badge, breadcrumb separator (non-interactive):** `xs`.

Sibling controls in the same UI surface should share a rung — mixing `sm` and `md` buttons next to each other reads as a typo, not a hierarchy.

## Cross-references

- **REQUIRED BACKGROUND:** [spacing-system](../spacing-system/SKILL.md) — the unit primitives (minor + major) drive which density mode applies, and the WCAG 2.5.8 floor lives there.
- **For the font sizes paired with each rung:** [type-scale](../type-scale/SKILL.md) — the per-rung font is taken from the canonical scale, not free-picked.
- **For line-heights inside each rung:** [line-height-grid](../line-height-grid/SKILL.md) — interactive controls use `lh-ui` (1.20), not `lh-prose`.

## Verification

After picking a rung:

1. **Density match:** the rung is from the density mode declared in the current foundation theme. Mixing balanced and spacious ladders in the same surface is a bug.
2. **Interactive floor:** the height is ≥ 24 CSS px for interactive controls. `xs` rungs in balanced and dense are reserved for non-interactive.
3. **Font pairing:** the inner font-size matches the rung's pairing (not a one-off).
4. **Icon pairing:** the leading or trailing icon size matches the rung's pairing.
5. **Sibling consistency:** sibling controls in the same surface share a rung.

## Sources

- [WCAG 2.5.8 — Target Size (AA, added in 2.2)](https://www.w3.org/TR/WCAG22/#target-size-minimum).
- Material Design 3 — Component sizing guidance.
- Apple Human Interface Guidelines — touch targets (44 pt mobile; relaxed to 24 CSS px desktop per WCAG).
- The UDTS / token.design spacing-and-sizing foundations spec.
