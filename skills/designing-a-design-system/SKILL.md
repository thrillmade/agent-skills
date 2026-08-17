---
version: "825fefa5297c"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: designing-a-design-system
description: |
  Entry-point dispatcher for BUILDING or EXTENDING a design system — creating a token architecture, color system, type scale, spacing system, or component-sizing ladder from scratch, or adding a new token family to an existing system. Routes to the L0 primitives in build order: naming and taxonomy (token-naming-conventions), color (oklch-color-space, apca-contrast, wcag-contrast, palette-relationships, chroma-harmonization), non-color families (type-scale, line-height-grid, spacing-system, component-sizing-principles), interchange and versioning (dtcg-format, semver-design-tokens), and the quality bar (designing-elite-ui). Use when the task is authoring the system itself; for reviewing design output load reviewing-design-work; for using an existing system load consuming-a-design-system.
---

# Designing a design system

You are building a design-token system from zero, or extending an existing one with a new token family — a color system, a type scale, a spacing system, a component-sizing ladder, or the naming taxonomy that ties them together. This skill orients you across the build pipeline in the order decisions actually depend on each other, and points at the skill that carries each station's real rules; it does not re-teach them here.

## When to use

- Standing up a brand-new design-token system: naming, color, type, spacing, sizing, format, versioning.
- Adding a new token family to an existing system (a new hue, a new component-sizing ladder, a new density mode).
- Deciding the build *order* — naming before color, color before non-color families, both before format and versioning.
- Setting or auditing the visual quality bar a system's tokens are meant to guarantee.

## When NOT to use

- Reviewing rendered UI or a PR against a system's existing rules — load [reviewing-design-work](../reviewing-design-work/SKILL.md) instead.
- Wiring a product to a system someone else owns (install, theme, upgrade) — load [consuming-a-design-system](../consuming-a-design-system/SKILL.md) instead.
- This skill is for authoring the system itself, not for consuming or auditing one.

## 1. Naming & taxonomy

Pick every token's name and class *before* color work starts — the prefix is the load-bearing decision every downstream station reads off (contrast obligation, DTCG extension fields, and SemVer severity of a rename all derive from the name).

**REQUIRED BACKGROUND:** [token-naming-conventions](../token-naming-conventions/SKILL.md)

One worked instantiation (incubating): [udts-naming-convention](../udts-naming-convention/SKILL.md).

## 2. Color

Pick the color space first, then set contrast targets with a dual-model stance — APCA as the primary generation target, WCAG as the legal-baseline cross-check — then generate the palette: hue-relationship math for the seed hue, chroma caps for equal-looking saturation across hues at each contrast stop.

**REQUIRED BACKGROUND:** [oklch-color-space](../oklch-color-space/SKILL.md), [apca-contrast](../apca-contrast/SKILL.md), [wcag-contrast](../wcag-contrast/SKILL.md), [palette-relationships](../palette-relationships/SKILL.md), [chroma-harmonization](../chroma-harmonization/SKILL.md)

## 3. Non-color families

Typography is a paired pair — a modular size ratio plus a line-height grid that snaps to the same units. Spacing follows a two-unit (minor + major) model. Component sizing is a curated, not formula-derived, height ladder that pairs with both.

**REQUIRED BACKGROUND:** [type-scale](../type-scale/SKILL.md), [line-height-grid](../line-height-grid/SKILL.md), [spacing-system](../spacing-system/SKILL.md), [component-sizing-principles](../component-sizing-principles/SKILL.md)

Worked instantiations (incubating): [udts-spacing-defaults](../udts-spacing-defaults/SKILL.md), [udts-component-sizing-ladders](../udts-component-sizing-ladders/SKILL.md).

## 4. Format & versioning

Serialize the system to the DTCG interchange snapshot every consumer transforms from. Compute the version bump from the resolved-value diff, never from intuition.

**REQUIRED BACKGROUND:** [dtcg-format](../dtcg-format/SKILL.md), [semver-design-tokens](../semver-design-tokens/SKILL.md)

Worked instantiations (incubating): [udts-dtcg-extensions](../udts-dtcg-extensions/SKILL.md), [udts-semver-defaults](../udts-semver-defaults/SKILL.md).

## 5. The elite bar

A token system exists so shipped UI clears a concrete visual standard, not so tokens exist for their own sake. Encode that standard in the tokens plus a short design-system doc, so builders and critics measure against one shared source of truth.

**REQUIRED BACKGROUND:** [designing-elite-ui](../designing-elite-ui/SKILL.md)

## 6. Testing & maintenance

Snapshot-test against the DTCG export, lint contrast floors and alias cycles in CI, and run deprecation cycles per the SemVer discipline above rather than breaking consumers silently.

One system's enforcement layer (incubating): [udts-linter-rules](../udts-linter-rules/SKILL.md).

## Cross-references

**L0 primitives:**
- [token-naming-conventions](../token-naming-conventions/SKILL.md) — token name/class/kind shape.
- [oklch-color-space](../oklch-color-space/SKILL.md) — color space and hue-angle primitives.
- [palette-relationships](../palette-relationships/SKILL.md) — hue-relationship math for a seed hue.
- [chroma-harmonization](../chroma-harmonization/SKILL.md) — cross-hue chroma caps per contrast stop.
- [type-scale](../type-scale/SKILL.md) — modular type-size ratio and stops.
- [line-height-grid](../line-height-grid/SKILL.md) — grid-aligned line-height per font size.
- [spacing-system](../spacing-system/SKILL.md) — two-unit (minor + major) spacing model.
- [component-sizing-principles](../component-sizing-principles/SKILL.md) — curated component-height and icon-size ladders.
- [dtcg-format](../dtcg-format/SKILL.md) — token interchange snapshot format.
- [semver-design-tokens](../semver-design-tokens/SKILL.md) — version-bump severity from a resolved-value diff.

**L0 critic lenses:**
- [apca-contrast](../apca-contrast/SKILL.md) — primary perceptual contrast target.
- [wcag-contrast](../wcag-contrast/SKILL.md) — legal-baseline contrast cross-check.
- [designing-elite-ui](../designing-elite-ui/SKILL.md) — the visual quality bar tokens must clear.

**L1 sibling dispatchers:** [reviewing-design-work](../reviewing-design-work/SKILL.md), [consuming-a-design-system](../consuming-a-design-system/SKILL.md).

**L2 stances (incubating — one system's worked instantiation, not yet loadable guidance):**
- [udts-naming-convention](../udts-naming-convention/SKILL.md), [udts-spacing-defaults](../udts-spacing-defaults/SKILL.md), [udts-component-sizing-ladders](../udts-component-sizing-ladders/SKILL.md), [udts-dtcg-extensions](../udts-dtcg-extensions/SKILL.md), [udts-semver-defaults](../udts-semver-defaults/SKILL.md), [udts-linter-rules](../udts-linter-rules/SKILL.md).
