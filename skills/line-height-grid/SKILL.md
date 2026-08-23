---
version: "90eb1dd8eb53"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: line-height-grid
description: Use when calculating line-height for any font size in a grid-aligned design system. Names the two-track model (lh-ui = ceil(font × 1.20) snapped to the minor unit; lh-prose = ceil(font × 1.50) snapped to the minor unit), the picking heuristic per role (ui-track for headings / buttons / labels; prose-track for paragraph body), and worked examples for 4/8, 2/4, and 4/16 grids. Cite when an agent picks a unitless line-height multiplier without snapping to the system's grid.
---

# Line-height grid

Line-height in a token-driven system is not a free multiplier — it's a snapped value on the spacing grid. UDTS uses two tracks: `lh-ui` (tight, for headings / labels / buttons) and `lh-prose` (loose, for paragraph body). Both derive from the font size and snap to the minor grid unit so adjacent paragraphs and successive lines preserve rhythm.

## When to use

- Picking line-height for any font size in a system that has a defined spacing grid.
- Auditing line-heights that "look right but feel off" — usually a sign they're not snapped.
- Setting up a foundation theme that needs both UI and editorial copy on the same grid.
- Code review: flag any unitless line-height (`line-height: 1.5`) on a system token; replace with a snapped px value from the appropriate track.

## When NOT to use

- One-off display elements (hero marketing splashes) where the line-height is hand-tuned by a typographer and the grid doesn't apply.
- Inline contexts where line-height inherits from the parent — the parent owns the grid alignment.

## The two-track formulas

```
lh-ui(size)    = ceil(size × 1.20) snapped UP to nearest minor-unit multiple
lh-prose(size) = ceil(size × 1.50) snapped UP to nearest minor-unit multiple
```

The ratios are intentional:

- **1.20 for UI**: keeps headings, button labels, and control text tight enough that they don't take excess vertical space in dense layouts. Tighter than 1.20 starts clipping diacritics on large sizes.
- **1.50 for prose**: matches the canonical typographic recommendation for fluent paragraph reading. Looser than 1.50 starts feeling spaced-out; tighter than 1.45 fatigues the eye.

The `ceil` step ensures the line-height is never *less* than the natural typographic ratio; the snap step puts it on the grid for downstream rhythm.

## When to use which track

| Role | Track | Why |
|---|---|---|
| Body paragraphs (long-form reading) | `prose` | Fluent reading requires 1.5× space |
| Lead paragraphs | `prose` | Same as body |
| Headings (display through H6) | `ui` | Tight space; headings stand on their own line |
| Button labels, link text, navigation | `ui` | Dense, single-line; no fluent-reading constraint |
| Form labels, helper text | `ui` | Compact |
| Code blocks | `ui` (or `code-tight` variant) | Code rows shouldn't have paragraph-style breathing room |
| Captions, metadata | `ui` | Compact |

When in doubt, ask: "is the user going to read multiple consecutive lines fluently?" If yes, `prose`; if no, `ui`.

## Worked examples

**14 px font, 4/8 grid (minor unit = 4, major = 8):**

```
lh-ui    = ceil(14 × 1.20) = ceil(16.8) = 17 → snap up to 20 (next multiple of 4)
lh-prose = ceil(14 × 1.50) = ceil(21.0) = 21 → snap up to 24 (next multiple of 4)
```

**16 px font, 4/8 grid:**

```
lh-ui    = ceil(16 × 1.20) = ceil(19.2) = 20 → snap up to 20 (already on grid)
lh-prose = ceil(16 × 1.50) = ceil(24.0) = 24 → snap up to 24 (already on grid)
```

**14 px font, 2/4 grid (denser; minor = 2, major = 4):**

```
lh-ui    = ceil(14 × 1.20) = ceil(16.8) = 17 → snap up to 18 (next multiple of 2)
lh-prose = ceil(14 × 1.50) = ceil(21.0) = 21 → snap up to 22 (next multiple of 2)
```

**24 px font, 4/16 grid (spacious; minor = 4, major = 16):**

```
lh-ui    = ceil(24 × 1.20) = ceil(28.8) = 29 → snap up to 32 (next multiple of 4)
lh-prose = ceil(24 × 1.50) = ceil(36.0) = 36 → snap up to 36 (already on grid)
```

## Why "ceil then snap," not "snap to nearest"

Rounding down can put the resolved line-height *below* the natural ratio, which produces:

- Diacritic clipping on larger sizes.
- Visually cramped paragraphs in the prose track.
- Inconsistent rhythm — sometimes you snap up, sometimes down, breaking baseline alignment.

`ceil` + snap-up is monotonic: line-height is always at least the ratio-derived value, and always on the grid.

## Cross-references

- **Routed here by:** [designing-a-design-system](../designing-a-design-system/SKILL.md) — the L1 dispatcher for building or extending a system.
- **REQUIRED BACKGROUND:** [type-scale](../type-scale/SKILL.md) — provides the font sizes this skill snaps line-heights for. The two skills are paired.
- **For the unit primitive that drives snapping:** [spacing-system](../spacing-system/SKILL.md) — the minor / major grid is what `snap up to nearest minor-unit multiple` refers to.

## Verification

After computing line-heights:

1. **Grid check:** every lh value is a multiple of the minor unit.
2. **Ratio floor:** `lh(font) ≥ ceil(font × ratio)` for both tracks. Never below.
3. **Monotonicity:** lh values grow with font size (no decreases between adjacent steps).
4. **Track separation:** at every font size, `lh-prose > lh-ui` (or equal at very small sizes where they collapse).
5. **Multi-line stack check:** stack two paragraphs at the prose track. The total height = `(lines × lh) + paragraph-margin` lands on the major grid.

If any check fails, recompute with stricter ceiling + snap-up.

## Sources

- The UDTS / token.design typography foundations spec.
- Classical typography (Bringhurst, *The Elements of Typographic Style*) — the 1.5× rule for prose pre-dates digital systems.
- [CSS line-height: where things go wrong](https://hacks.mozilla.org/2024/06/css-line-height/) — modern browser handling caveats.
