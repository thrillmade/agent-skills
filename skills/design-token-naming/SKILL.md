---
version: "cde544a56582"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: design-token-naming
description: |
  SUPERSEDED by `token-naming-conventions` (L0) + `udts-naming-convention` (L2, incubating) — see the design-catalog section of the README; kept unchanged during the tokenomics migration window, new work should load the successors. Use when designing, auditing, or critiquing a design-token naming scheme. Names the UDTS convention — hyphen-separated names where the prefix declares the token's class (contrast-bound vs free) and kind (text / surface / border / ui / illustration / decorative / brand-spot), with the class redundantly encoded in `$extensions.udts.class`. Names the hue-angle primitive convention (`teal-180` not `accent-teal`), the role + stop convention for color-mode tokens (`primary-contrast-500`, `surface-fixed-100`), the two component-token chain shapes (direct vs via-semantic), and the rule that themes and density go in the theme layer, not the token name. Cite when an agent proposes dot-separated paths, semantic primitive names, or naming patterns where class isn't derivable from the prefix.
---

# Design-token naming

UDTS names tokens so that an agent or linter can derive the token's class and contrast obligation *from the name alone*. The naming convention is hyphen-separated, prefix-loaded, and redundantly encoded in DTCG `$extensions.udts.class` so a validator catches mismatches.

## When to use

- Designing a new token naming convention for a system that needs to be AI-legible.
- Auditing existing tokens that drift across naming styles (dot-paths, BEM, T-shirt-only, etc.).
- Adding a new component or token family — picking the prefix is the load-bearing decision.
- Code review: flag tokens whose prefix doesn't match their class, or tokens that hide their class in metadata instead of the name.

## When NOT to use

- One-off internal tokens that never leave the file (CSS-variable convenience for a single component). The naming discipline isn't earned at that scope.
- Adapting an existing system that uses a different convention (Material 3 roles, Tailwind utilities, Radix layers). Don't propose UDTS naming as a rename project — use it for new systems or for the boundary layer.

## The prefix-loaded convention

Every UDTS token name is `<prefix>-<role-or-kind>-<modifier>-<stop>-<state>`. The first segment — the **prefix** — declares the token's [class](https://github.com/thrillmade/agent-skills/tree/main/skills/apca-contrast) (contrast-bound vs free, defined in [apca-contrast](../apca-contrast/SKILL.md)) and kind (text / surface / border / ui / illustration / decorative / brand-spot, defined in the UDTS spec).

### Contrast-bound prefixes

| Prefix family | Kind | Examples |
|---|---|---|
| `content-*` | text | `content-primary`, `content-secondary`, `content-on-primary`, `content-disabled` |
| `surface-*` | surface | `surface-base`, `surface-raised`, `surface-overlay`, `surface-inverse` |
| `border-*` | border | `border-subtle`, `border-default`, `border-strong`, `border-focus` |
| `button-*`, `chip-*`, `control-*`, `link-*`, `ui-*` | ui | `button-bg-primary-default`, `chip-text-info`, `control-border-error-focus` |

All of these carry the `contrast-bound` class and an APCA + WCAG pairing obligation.

> The `content-*` family's prefix doesn't match its kind (`text`) literally — historical legibility (designers think in "content") outweighs strict 1:1 prefix-to-kind mapping. The `$extensions.udts.kind` field is the canonical kind; the prefix is the canonical class.

### Free prefixes

| Prefix family | Kind | Examples |
|---|---|---|
| `illustration-*` | illustration | `illustration-hero-warm`, `illustration-empty-state-1` |
| `decorative-*` | decorative | `decorative-chart-1`, `decorative-divider-tint` |
| `brand-spot-*` | brand-spot | `brand-spot-red`, `brand-spot-logo-blue` |

All of these carry the `free` class — no APCA + WCAG check at generation, no pairing obligation.

## Hue-angle primitive naming

Color primitives use the **hue angle** in OKLCH degrees, not a semantic label:

```
red-30        orange-60      yellow-90
lime-120      green-150      teal-180
sky-200       blue-220       indigo-260
purple-280    pink-320
```

Adding a new hue doesn't renumber existing ones; the angle is load-bearing. **Reserve semantic labels (`accent-teal`, `primary`, `brand`) for the theme layer above primitives.**

The full primitive name carries the variant and stop: `teal-180-harmony-500`, `purple-280-max-100`.

## Color-mode token naming (varies / fixed)

Color-mode tokens are emitted per (role, stop) combination per palette role. The naming pattern:

```
<role>-<mode-behavior>-<stop>
e.g.
  primary-contrast-500     (varies between light and dark by stop math)
  primary-fixed-500        (same primitive in every declared mode)
  neutral-contrast-100
  danger-fixed-700
```

`contrast-N` is the token-name pattern for `mode-behavior: "varies"`; `fixed-N` is the pattern for `mode-behavior: "fixed"`.

## Component token chain shapes

UDTS has two resolution-chain shapes; the naming reflects which one a token uses:

**Direct shape** (component already names role + stop):
```
button-bg-primary-default        → primary-contrast-500   → palette → primitive
```
The component token binds straight to a color-mode token.

**Via-semantic shape** (component routes through a generic semantic):
```
button-text-primary-default      → content-on-primary     → color-mode token → palette → primitive
```
The component token binds to a semantic (`content-on-primary`), which then routes through the color-mode layer.

Both are fully deterministic. Pick the direct shape for properties where the component already implies the role (`bg-*`); pick the via-semantic shape for properties that route through a generic content/border/surface intermediate (`text-*`).

## Density and theme are NOT in the name

Density modes (dense / balanced / spacious) and color themes (default / halloween / enterprise) are runtime axes the theme layer applies. Tokens are theme-agnostic — `button-bg-primary-default` resolves the same way regardless of which color theme is active, because the theme reassigns what `primary` *means*, not the token.

Anti-pattern: `button-bg-primary-default-dense` (density in the name). Correct: density is a foundation-theme axis; the token's resolved value differs because the theme differs, not because the name differs.

## Cross-references

- **REQUIRED BACKGROUND:** [oklch-color-space](../oklch-color-space/SKILL.md) for the hue-angle convention; [apca-contrast](../apca-contrast/SKILL.md) for the contrast-class concept.
- **For the DTCG schema that mirrors the prefix:** [dtcg-format](../dtcg-format/SKILL.md) — the `$extensions.udts.class` and `$extensions.udts.kind` fields that redundantly encode what the prefix declares.
- **For SemVer behavior on naming changes:** [semver-design-tokens](../semver-design-tokens/SKILL.md) — renames are always major.

## Verification

For each new or modified token:

1. **Prefix is in the family list.** Names whose prefix isn't on the contrast-bound or free list are malformed.
2. **Class matches prefix.** `$extensions.udts.class` agrees with what the prefix declares. A `surface-rainbow` with `class: "free"` is rejected by validation.
3. **Hue primitives use the angle, not a semantic label.** No `primary-500`-as-primitive; only `<hue>-<angle>-<variant>-<stop>`.
4. **No density / theme in the name.** Density and theme are runtime axes, not token-name segments.
5. **Cross-reference resolves.** If the token aliases another (e.g. `surface-base` aliasing a mode-default), the target exists in the catalog.

## Sources

- The UDTS / token.design spec (foundations/color.md, semantics/component-tokens.md, integrations/code-exports.md).
- Spec-PR-B (the load-bearing classification + naming PR for UDTS).
- IBM Carbon, Google Material 3 — UDTS borrows the three-tier (primitive → semantic → component) shape and extends with the class system.
