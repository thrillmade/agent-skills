---
version: "1.0.0"
digest: "e89a261fddd8"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: token-naming-conventions
description: |
  Use when designing, auditing, or critiquing a design-token naming scheme for any design system. Names the universal principles: hyphen-separated kebab-case names; prefix-loaded naming where the first segment declares the token's class and kind, so a linter or agent can derive contrast obligations from the name alone; redundant class encoding in metadata so validators catch name/metadata mismatches; physical, non-semantic primitive names (hue angles, not accent-teal) with semantic labels reserved for the theme layer; resolution-chain naming (direct vs via-semantic component-token shapes); and the rule that theme and density are runtime axes that never appear in a token name. Cite when an agent proposes dot-separated paths, semantic primitive names, or names whose class isn't derivable from the prefix. For UDTS's concrete instantiation see udts-naming-convention.
---

# Token naming conventions

A design-token name should let an agent or linter derive the token's class and
contrast obligation *from the name alone*. The universal shape that makes this
possible is hyphen-separated, prefix-loaded, and redundantly encoded in token
metadata so a validator can catch a name that disagrees with its own class.

These are system-neutral principles. For one worked instantiation — concrete
prefix families, spec fields, and worked chains — see [udts-naming-convention](../udts-naming-convention/SKILL.md).

## When to use

- Designing a new token naming convention for a system that needs to be
  AI-legible.
- Auditing existing tokens that drift across naming styles (dot-paths, BEM,
  T-shirt-only, etc.).
- Adding a new component or token family — picking the prefix is the
  load-bearing decision.
- Code review: flag tokens whose prefix doesn't match their class, or tokens
  that hide their class in metadata instead of the name.

## When NOT to use

- One-off internal tokens that never leave the file (a CSS-variable convenience
  for a single component). The naming discipline isn't earned at that scope.
- Adapting an existing system that already uses a different convention
  (Material 3 roles, Tailwind utilities, Radix layers). Don't propose these
  principles as a rename project — apply them to new systems or to the boundary
  layer.

## Prefix-loaded naming

Give every token name the shape `<prefix>-<role-or-kind>-<modifier>-<stop>-<state>`.
The first segment — the **prefix** — declares the token's **class** (whether it
carries a contrast obligation or is free of one) and its **kind** (text,
surface, border, control, and so on). Both must be machine-derivable from the
prefix without opening the token body.

Split prefixes into two disjoint groups:

- **Contrast-bound** prefixes (e.g. `content-*`, `surface-*`) name tokens that
  carry a contrast-pairing obligation — every value must clear an APCA/WCAG
  check against its intended background.
- **Free** prefixes name tokens with no contrast obligation — decorative,
  illustration, and brand-spot colors that are never asked to be legible text.

The prefix need not match the kind label one-for-one (a `content-*` prefix may
name tokens of kind `text` because designers think in "content"). What matters
is that the prefix deterministically declares the *class*, and the kind is
recorded canonically alongside it.

## Redundant class encoding

Encode the class a *second* time, in a namespaced metadata extension on the
token, so the name and the metadata must agree. A validator then rejects any
token whose declared class contradicts what its prefix implies — a
`surface-rainbow` marked `free` is caught mechanically, before it ships. The
name is the human-legible signal; the metadata is the machine cross-check. One
without the other loses either legibility or enforceability.

## Physical, non-semantic primitive names

Name color primitives by a **physical** property, not a semantic role. The
universal convention is the OKLCH **hue angle** in degrees:

```
red-30        orange-60      yellow-90
lime-120      green-150      teal-180
sky-200       blue-220       indigo-260
purple-280    pink-320
```

Adding a new hue doesn't renumber the existing ones — the angle is load-bearing
and stable. **Reserve semantic labels (`accent-teal`, `primary`, `brand`) for
the theme layer above primitives**, never for the primitive itself. A primitive
named `accent-teal` bakes a role into a physical fact and breaks the moment the
theme reassigns the accent. The full primitive name carries the variant and
stop after the angle, e.g. `teal-180-harmony-500`.

## Mode behavior lives in the name

When a token's resolved value depends on the active light/dark mode, put the
*resolution behavior* — mode-varying vs mode-fixed — into the name pattern
itself, per (role, stop) combination:

```
<role>-<mode-behavior>-<stop>
e.g.
  primary-contrast-500     (varies between light and dark by stop math)
  primary-fixed-500        (same primitive in every declared mode)
  neutral-contrast-100
  danger-fixed-700
```

A `contrast-N` segment is the name pattern for a value that *varies* by mode; a
`fixed-N` segment is the pattern for a value that is the *same* primitive in
every mode. The reader learns the mode behavior from the name, not from
resolving the token.

## Component-token chain shapes

A component token can resolve through one of two chain shapes; the name should
reflect which one applies.

**Direct shape** — the component token binds straight to a role+stop token
because the component already implies the role:
```
button-bg-primary-default   → primary-contrast-500 → palette → primitive
```

**Via-semantic shape** — the component token routes through a generic semantic
intermediate before reaching the color-mode layer:
```
button-text-primary-default → content-on-primary → color-mode token → palette → primitive
```

Both are fully deterministic. Pick the direct shape for properties where the
component already names the role (`bg-*`); pick the via-semantic shape for
properties that route through a generic content/border/surface intermediate
(`text-*`).

## Theme and density are NOT name segments

Density (dense / balanced / spacious) and color theme (default / seasonal /
enterprise) are **runtime axes** applied by the theme layer. Tokens are
theme-agnostic: `button-bg-primary-default` resolves the same way regardless of
which theme is active, because the theme reassigns what `primary` *means*, not
what the token is named.

Anti-pattern: `button-bg-primary-default-dense` (density in the name). Correct:
density is a foundation-theme axis; the token's resolved value differs because
the theme differs, not because the name differs.

## Verification

For each new or modified token:

1. **Prefix declares the class.** The prefix maps deterministically to a known
   contrast-bound or free class. A name whose class isn't derivable from the
   prefix is malformed.
2. **Metadata agrees with the prefix.** The redundantly-encoded class matches
   what the prefix declares; a mismatch is a validation failure.
3. **Primitives use a physical name.** Hue primitives carry the angle, not a
   semantic label — no `primary-500`-as-primitive.
4. **No theme or density in the name.** These are runtime axes, not token-name
   segments.
5. **Cross-references resolve.** If the token aliases another, the target
   exists in the catalog.

## Cross-references

- **Routed here by:** [designing-a-design-system](../designing-a-design-system/SKILL.md) — the L1 dispatcher for building or extending a system.
- **REQUIRED BACKGROUND:** [oklch-color-space](../oklch-color-space/SKILL.md) for the hue-angle convention;
  [apca-contrast](../apca-contrast/SKILL.md) for the contrast-class concept.
- **For the metadata-extension mechanism:** [dtcg-format](../dtcg-format/SKILL.md) — how a namespaced
  extension redundantly encodes what the prefix declares.
- **For SemVer behavior on naming changes:** [semver-design-tokens](../semver-design-tokens/SKILL.md) — a rename
  is always a major change.
- **For one worked instantiation:** [udts-naming-convention](../udts-naming-convention/SKILL.md) (an incubating L2
  stub) applies these principles with concrete prefix families and metadata
  fields.

## Sources

- IBM Carbon, Google Material 3 — the three-tier (primitive → semantic →
  component) shape these conventions borrow and extend with the class system.
