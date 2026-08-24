---
version: "1.0.0"
digest: "36a59edf6f40"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: https://github.com/thrillmade/agent-skills
name: palette-relationships
description: Use when proposing a palette around a single seed hue and needing to pick which relationship model (monochromatic / analogous / complementary / split-complementary / triadic / tetradic / compound) fits the brief. Names the hue-angle math for each, when each is appropriate (analogous for restraint; triadic for vibrance; complementary for tension), and the role assignment heuristic.
---

# Palette relationships

When a designer hands an agent a single starting hue and asks for "the rest of the palette," the choice is which **relationship model** to apply. Each model is a hue-angle pattern with a different emotional and functional register. Knowing the patterns is most of the job.

## When to use

- A designer or agent has a starting hue and needs additional hues to fill a palette.
- Proposing a palette for a brief that uses words like "balanced," "vibrant," "calm," "tense," "restrained," "dynamic."
- Reviewing a palette proposal — name the implicit relationship and check whether the brief asked for it.

## When NOT to use

- The palette is already specified (all hues given). Use [chroma-harmonization](../chroma-harmonization/SKILL.md) to balance them, not this skill.
- The brief is for a single-hue system (just stops of one palette). No relationship to pick.

## The relationships

Hue angle math is on the OKLCH 0–360° wheel, anchored at the seed hue `H₀`.

| Relationship | Hues | Use when | Hue math |
|---|---|---|---|
| **Monochromatic** | 1 | calm, single-brand voice, editorial | `H₀` (vary L and C across stops) |
| **Analogous** | 2–5 | restrained, coherent, "family" | `H₀ ± 15°`, `H₀ ± 30°` |
| **Complementary** | 2 | tension, before/after, success/danger pairing | `H₀`, `H₀ + 180°` |
| **Split-complementary** | 3 | softer tension than complementary, more usable | `H₀`, `H₀ + 150°`, `H₀ + 210°` |
| **Triadic** | 3 | vibrant, balanced, distinct primary/secondary/tertiary | `H₀`, `H₀ + 120°`, `H₀ + 240°` |
| **Tetradic — square** | 4 | bold, energetic, four equal roles | `H₀`, `H₀ + 90°`, `H₀ + 180°`, `H₀ + 270°` |
| **Tetradic — rectangle** | 4 | dynamic but balanced, two complement pairs | `H₀`, `H₀ + 60°`, `H₀ + 180°`, `H₀ + 240°` |
| **Compound (analogous + complement)** | 3–4 | warm core + cool accent (or vice versa) | `H₀ ± 30°`, `H₀ + 180°` |

For matching briefs to relationships:

- **"calm, monochrome editorial"** → monochromatic
- **"restrained, family-feel"** → analogous
- **"tension, success vs danger"** → complementary
- **"vibrant, distinct roles"** → triadic
- **"dynamic and balanced"** → tetradic-rectangle (the square is harder to balance at usable chromas)
- **"warm with one cool accent"** → compound

## Role assignment after picking the relationship

The number of hues dictates the role count, but not the assignment. A triadic palette has three hues; which becomes `primary`, `secondary`, `tertiary` is a design decision driven by intent.

Default heuristic (60/30/10 + accent):

- **60% — primary** = the seed hue (`H₀`). The dominant brand voice.
- **30% — secondary** = the relationship hue closest to the seed in temperature.
- **10% — tertiary / accent** = the relationship hue furthest from the seed.

For complementary pairs, the seed is `primary`; the complement is `danger` or `info` depending on hue (warm → danger, cool → info).

## Pitfalls

- **Square tetrads at usable chromas often read garish** — chartreuse (90°) and magenta (270°) next to the seed and its complement tend to fight. Prefer rectangle tetrads (60° / 120° offsets) when the brief is "balanced."
- **Analogous past 60° total spread starts to read as triadic** — keep analogous ranges tight.
- **Complementary pairs work for two hues only** — padding to four forces a near-duplicate and breaks the relationship.

## Verification

After picking hues:

1. **Spread check:** every hue is within the relationship's declared offset from the seed.
2. **Distinguishability check:** at the palette's typical contrast stop (e.g. 500), neighboring hues are visually distinguishable (rule of thumb: ≥ 20° apart at the same L and C).
3. **Brief match:** the relationship matches the brief's adjective (calm / vibrant / tense / dynamic). If not, pick a different relationship.

## Cross-references

- **Routed here by:** [designing-a-design-system](../designing-a-design-system/SKILL.md) — the L1 dispatcher for building or extending a system.
- **REQUIRED BACKGROUND:** [oklch-color-space](../oklch-color-space/SKILL.md) — hues are OKLCH angles; the relationship math operates on those.
- **For palette balance after picking hues:** [chroma-harmonization](../chroma-harmonization/SKILL.md) — cap chroma at the cross-hue minimum.
- **For contrast targets across stops:** [apca-contrast](../apca-contrast/SKILL.md).

## Sources

- [Adobe Color wheel](https://color.adobe.com/create/color-wheel) — the canonical interactive picker for relationships.
- [Coolors palette generator](https://coolors.co/) — applies the same relationship taxonomy.
- Itten's color wheel theory (foundational; predates digital tools but supplies the taxonomy).
