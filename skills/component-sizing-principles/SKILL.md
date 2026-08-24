---
version: "1.0.0"
digest: "9de5f0d2c424"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: component-sizing-principles
description: |
  Use when picking a control height (button / input / chip / badge), proposing a component-height or icon-size ladder for a density mode, or auditing one-off heights drifting across a codebase. Names the universal principles: ladders are curated, not formula-derived — formula-clean values render poorly and blur rung distinctions; every interactive control clears the WCAG 2.5.8 AA 24 CSS px target-size floor, with the smallest rung reserved for non-interactive elements; each rung pairs its height with a type-scale font size and a curated icon size; sibling controls in one surface share a rung. Cite when an agent derives heights from a ratio, picks an off-ladder height, or puts an interactive control below 24 px. For one system's concrete rung sets see udts-component-sizing-ladders.
---

# Component sizing principles

Component heights and icon sizes are **curated**, not formula-derived. A good ladder picks each height so it pairs cleanly with a font from the type scale, an icon from the icon set, and target-size requirements — and so each rung distinguishes visually from its neighbors. This skill names the universal principles; it is deliberately system-neutral. For one concrete instantiation — the per-density rung sets with their exact heights, fonts, and icon pairings — see [udts-component-sizing-ladders](../udts-component-sizing-ladders/SKILL.md).

## When to use

- Picking a height for a button, input, chip, badge, dropdown, or any other rectangular interactive control.
- Proposing a control-height or icon-size ladder for a new density mode.
- Auditing one-off heights (`h-7`, `h-9`, `h-11`) drifting across a codebase.
- Code review: flag heights outside the curated ladder; propose the nearest curated rung with rationale.

## When NOT to use

- No token layer on disk — no curated ladder to be off of. A marketing CTA built inside a system with a declared ladder is still in scope.
- Non-rectangular controls (circular avatars, range thumbs) where the size is governed by the icon or asset, not a height token.

## Ladders are curated, not formula-derived

A formula `height → font-size → icon-size` produces *mathematically clean* values that *render poorly*. Curate the rungs by hand instead, for three reasons:

- **Formula heights create visually indistinct rungs.** Heights at every fixed step (24, 28, 32, 36, ...) are hard to tell apart in a stack — adjacent rungs blur, so the ladder loses its job of signalling hierarchy.
- **Off-scale font sizes clash with the typography system.** A formula lands on sizes like 13, 15, 17 that sit outside the modular scale and read as noise next to type set from [type-scale](../type-scale/SKILL.md).
- **Off-curve icon sizes glitch at common zoom levels.** Icon sizes outside the curated set render with hairline artifacts at ordinary zoom.

A curated ladder trades flexibility for visual distinguishability, predictable pairing, and target-size safety. Design systems benefit from less flexibility at this layer.

## The rung-pairing principle

Each rung pairs its height with **a font size from the type scale** and **a curated icon size**. The pairings are fixed per rung, not chosen ad hoc per instance. One invariant holds across every rung: **the icon is never smaller than the paired font size** — an undersized icon next to its label reads as a rendering bug.

Ladders are conventionally labelled with T-shirt sizes (`xs` / `sm` / `md` / `lg` / `xl`) so the rung, its font, and its icon travel together under one name.

## Curated icon sizes

Curate the icon ladder the same way you curate heights. **12, 16, 24, 32, 40, 48** is a widely-used curated set — these are the sizes at which the common icon families (Material Icons, Lucide, Heroicons, Phosphor) render cleanly without hairline glitches, and they subdivide into 4 px steps at the small end (where inline alignment matters) and 8 px steps at the large end (where it doesn't).

**Don't formula-derive icon sizes.** A height-to-icon ratio like `icon = height / 2` produces off-curve values (14, 18, 22, ...) — every one of which renders worse than its curated neighbour.

## Applying the target-size floor to a ladder

[spacing-system](../spacing-system/SKILL.md) owns the WCAG 2.5.8 AA target-size floor and its citation. Applied to a ladder:

- Reserve the **smallest rung** — which may sit at or below the floor — for **non-interactive elements** (badges, read-only chips, density tags).
- Start interactive rungs at the **first rung that clears the floor**.
- In a roomier, lower-density mode whose smallest rung already clears the floor, the entire ladder is interactive-safe.

## Sibling consistency

Sibling controls in the same UI surface share a rung. Mixing (say) an `sm` and an `md` button next to each other reads as a typo, not a hierarchy — hierarchy comes from prominence and placement, not from a one-step height difference between neighbours.

## Picking a rung

Default heuristic:

- **Paired buttons and inputs:** the system's default mid rung. Use the *same* rung for a button and its associated input so they align horizontally in a form.
- **Dense table cell / compact toggle:** one rung smaller than default.
- **Primary CTA / hero button:** one or two rungs larger than default, by prominence.
- **Badge, breadcrumb separator, density tag (non-interactive):** the smallest, non-interactive rung.

## Verification

After picking a rung:

1. **Ladder match:** the rung comes from the declared density ladder, not a one-off height. Mixing rungs from different density ladders in one surface is a bug.
2. **Interactive floor:** the height clears [spacing-system](../spacing-system/SKILL.md)'s target-size floor for interactive controls. Where the smallest rung sits below that floor it is reserved for non-interactive use; a ladder whose smallest rung already clears it has no reserved tier.
3. **Font pairing:** the inner font-size matches the rung's paired size from the type scale, not a free-picked value.
4. **Icon pairing:** the leading or trailing icon size matches the rung's paired icon, and is not smaller than the font.
5. **Sibling consistency:** sibling controls in the same surface share a rung.

## Cross-references

- **Routed here by:** [designing-a-design-system](../designing-a-design-system/SKILL.md) — the L1 dispatcher for building or extending a system.
- **REQUIRED BACKGROUND:** [spacing-system](../spacing-system/SKILL.md) — the unit primitives drive which density ladder applies, and it owns the WCAG 2.5.8 target-size floor.
- **For the font sizes paired with each rung:** [type-scale](../type-scale/SKILL.md) — the per-rung font is taken from the canonical scale, not free-picked.
- **For line-heights inside each rung:** [line-height-grid](../line-height-grid/SKILL.md) — interactive controls use `lh-ui`, not `lh-prose`.
- **For one system's worked rung sets:** [udts-component-sizing-ladders](../udts-component-sizing-ladders/SKILL.md) — concrete per-density heights with their font and icon pairings (incubating L2 stub).

## Sources

- The WCAG 2.5.8 target-size floor cited above is [spacing-system](../spacing-system/SKILL.md)'s to source; linked, not restated, so the two skills can't drift on the number.
- [Material Design's icon sizing](https://m3.material.io/styles/icons) — informs the curated icon set.
- Apple Human Interface Guidelines — touch targets (44 pt mobile; relaxed on desktop to the floor spacing-system cites).
