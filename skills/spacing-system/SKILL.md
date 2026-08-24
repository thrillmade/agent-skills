---
version: "aef0e20032c4"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: spacing-system
description: Use when designing or auditing a spacing scale for padding, gaps, icon sizes, component heights, or border radii. Names the two-unit primitive model (a minor unit — the smallest legal increment — plus a major unit — the dominant rhythm — where major divides cleanly by minor), the derivation rule (padding / gap / radius / height ladders all derive from the unit primitives, never invented per-surface), the 24 CSS px WCAG 2.5.8 AA target floor for interactive heights, and the T-shirt-vs-numeric naming options. Cite when an agent proposes a single-unit grid for a mixed-density system or invents off-grid spacing values for "this one specific case." For one system's concrete density-mode unit choices see udts-spacing-defaults.
---

# Spacing system

Spacing in a token-driven design system is a **two-unit primitive** problem, not a one-number guess. A token-driven system declares a **minor unit** (the smallest legal increment) and a **major unit** (the dominant rhythm), with the constraint that the major divides cleanly by the minor. Everything downstream — padding, gap, icon size, component height, border radius — derives from those two numbers.

## When to use

- Designing a new spacing scale from a density brief.
- Auditing an existing scale with one-off off-grid values.
- Picking unit primitives for a density mode (dense / balanced / spacious).
- Code review: flag raw px values for `padding` / `gap` / `margin` outside the system's declared scale.

## When NOT to use

- No token layer on disk — no unit primitives declared anywhere, so there is no grid to be off of. A marketing surface built inside a system that has declared primitives is still in scope.
- Print-design contexts where the grid math is pt-based and a different system applies.

## The two-unit primitive model

A token-driven system declares two unit primitives per foundation theme:

| Slot | Typical value | Role |
|---|---|---|
| **minor** | e.g. 4 | Smallest legal increment — used for tight inline gaps, sub-pixel-but-aligned spacing |
| **major** | e.g. 8 | Dominant rhythm — used for padding, gap, vertical stack rhythm |

Constraint: `major mod minor == 0`. Both default to 4 when not split (single-unit systems collapse to `minor == major`).

Different density briefs pick different unit pairs — a dense data tool wants a smaller minor unit than a spacious marketing surface, so the same derivation rule yields a 2/4, 4/8, or 4/16 pairing depending on the brief. One system's concrete density-mode unit choices live in [udts-spacing-defaults](../udts-spacing-defaults/SKILL.md) (an incubating L2 stub).

## What derives from the unit primitives

Every secondary scale derives from the two units. Designers and developers don't invent these — the system generates them.

### Padding ladder

Generated from the major unit, with minor steps for tight cases:

```
padding-0       = 0
padding-2xs     = minor                  (e.g. 4)
padding-xs      = major                  (e.g. 8)
padding-sm      = 1.5 × major            (e.g. 12)
padding-md      = 2 × major              (e.g. 16)
padding-lg      = 3 × major              (e.g. 24)
padding-xl      = 4 × major              (e.g. 32)
padding-2xl     = 6 × major              (e.g. 48)
padding-3xl     = 8 × major              (e.g. 64)
```

### Gap ladder

Same ladder as padding, separately labeled (`gap-*`) because horizontal and vertical gaps may diverge in some themes. The major-unit base ensures stacked rhythm preserves baselines.

### Icon-size ladder

Curated, not derived — [component-sizing-principles](../component-sizing-principles/SKILL.md) owns the curated set, the reasoning, and the rule that pairs an icon size with a control height.

### Component-height ladder

Curated per density mode, with the **24 CSS px WCAG 2.5.8 AA Pointer Target floor** for interactive controls (anything clickable / tappable / focusable). See [component-sizing-principles](../component-sizing-principles/SKILL.md) for the per-density ladder.

### Border-radius ladder

Radius snaps to the minor unit like every other ladder here, but **how many rungs and how fast they grow is the system's own personality call, not a universal formula** — a sharp-cornered enterprise tool and a soft-cornered consumer app can share the same unit primitives and still diverge completely on radius. Two endpoints are universal regardless of personality: `radius-pill` (9999, fully-rounded) and `radius-circle` (50%, relative, for circular elements). One worked ladder between `0` and those endpoints lands in [udts-spacing-defaults](../udts-spacing-defaults/SKILL.md) once that stub stabilizes.

## Naming: T-shirt OR numeric

Emit **both** sets of names and let consumers pick the family that fits their codebase convention:

| T-shirt | Numeric | px (balanced) |
|---|---|---|
| `padding-2xs` | `space-1` | 4 |
| `padding-xs` | `space-2` | 8 |
| `padding-sm` | `space-3` | 12 |
| `padding-md` | `space-4` | 16 |
| `padding-lg` | `space-5` | 24 |
| `padding-xl` | `space-6` | 32 |
| `padding-2xl` | `space-7` | 48 |
| `padding-3xl` | `space-8` | 64 |

Emit both in DTCG with cross-aliases. Pick the family that fits your codebase, not "the correct one" — there isn't one.

## The WCAG 2.5.8 AA Pointer Target floor

Any interactive control's minimum **height** is **24 CSS px** for AA conformance. The smallest rung in the component-height ladder is reserved for non-interactive elements (badges, read-only chips, density tags); interactive controls start at the first rung that clears the 24 px floor.

Failing this is one of the most common WCAG 2.2 misses in design systems. The skill exists partly to make the rule load-bearing.

## Cross-references

- **Routed here by:** [designing-a-design-system](../designing-a-design-system/SKILL.md) — the L1 dispatcher for building or extending a system.
- **REQUIRED BACKGROUND for height + font + icon pairing:** [component-sizing-principles](../component-sizing-principles/SKILL.md) — the curated per-density component-height ladder + font-pairing + icon-size pairing.
- **For the typography scale that pairs with spacing:** [type-scale](../type-scale/SKILL.md) and [line-height-grid](../line-height-grid/SKILL.md) — line-heights snap to the minor unit declared here.
- **For one system's concrete density-mode unit choices (worked example):** [udts-spacing-defaults](../udts-spacing-defaults/SKILL.md) — an incubating L2 stub that instantiates this model.

## Verification

After picking unit primitives + emitting ladders:

1. **Divisibility:** `major mod minor == 0`. If not, the system is malformed.
2. **Grid alignment:** every padding, gap, and component-height token is a multiple of the minor unit.
3. **Pointer target:** every interactive component-height rung is ≥ 24 CSS px.
4. **Naming sync:** if both T-shirt and numeric families are emitted, every value has a matching pair in both. No orphans.
5. **Icon-size curation:** icon sizes match [component-sizing-principles](../component-sizing-principles/SKILL.md)'s curated set, not a formula output.

## Sources

- [WCAG 2.5.8 — Target Size (AA, added in 2.2)](https://www.w3.org/TR/WCAG22/#target-size-minimum) — the 24 CSS px floor.
- One system's concrete density-mode unit choices: [udts-spacing-defaults](../udts-spacing-defaults/SKILL.md) (incubating).
