---
version: "1.0.0"
digest: "9bdad1baf4f5"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: dtcg-format
description: |
  Use when authoring, validating, or transforming W3C Design Tokens Format (DTCG) JSON. Names the $type / $value / $extensions separation, alias-reference syntax ({path.to.token}), group inheritance for shared $type / $description, composite token shapes (shadow, typography, transition), and the namespaced $extensions mechanism for tool-specific metadata. Cite when an agent proposes bare value / type keys without $, invents a top-level $modes key (themes/modes aren't in the DTCG draft), or hand-rolls tool metadata outside a namespaced extension bag. For one system's concrete extension schema see udts-dtcg-extensions.
---

# DTCG format

W3C Design Tokens Community Group format (DTCG) is the canonical interchange format for design tokens. Token systems typically treat a DTCG snapshot as the export source of truth from which every platform format (CSS variables, Tailwind, TypeScript, iOS, Android, Flutter) derives.

The DTCG spec is in draft (currently 2025.10) — practitioner adoption is wide enough that breaking changes face strong pushback, but the format is a Community Group product, not a W3C Recommendation.

## When to use

- Authoring a new DTCG file from scratch.
- Migrating an existing token system to DTCG.
- Validating a DTCG file against the spec.
- Transforming DTCG into another format (Style Dictionary, CSS variables, etc.).
- Code review on PRs that change DTCG files.

## When NOT to use

- Quick prototypes / single-file tokens that won't be exported across tools. The DTCG ceremony isn't earned at that scope.
- Tools that have their own native format (Tailwind config, native CSS variables in a one-product codebase). DTCG is the *interchange* format; you don't have to author in it.

## The reserved-key separation

Every DTCG token is an object with reserved `$`-prefixed keys:

| Key | Required? | Meaning |
|---|---|---|
| `$value` | yes (on tokens; groups omit it) | The token's data — a primitive value or an alias reference |
| `$type` | yes on leaves, optional on groups | The semantic type (`color`, `dimension`, `fontFamily`, `duration`, `shadow`, `typography`, `transition`, `cubicBezier`, etc.) |
| `$description` | no | Free-form description; carried into doc generation |
| `$extensions` | no | Namespaced bag for tooling-specific metadata; namespace under a tool/system identifier so other tooling can ignore it |

Bare keys (no `$` prefix) are **group children**, not properties. A token named `value: "#ff0000"` (no `$`) is a child token named `value`, not a token with a value of `#ff0000`. Validators that don't strictly enforce this silently accept it and produce empty output.

```json
{
  "color": {
    "primary": {
      "500": {
        "$type": "color",
        "$value": "#1d4ed8",
        "$description": "Primary brand color"
      }
    }
  }
}
```

## Aliases

Reference another token's `$value` with `{path.to.token}` syntax. Aliases inherit `$type` from the target — **do not redeclare it**:

```json
{
  "color": {
    "primary": { "500": { "$type": "color", "$value": "#1d4ed8" } },
    "action":  { "default": { "$value": "{color.primary.500}" } }
  }
}
```

Aliases resolve transitively. **Alias cycles aren't caught by the spec** — add a resolver check in CI.

## Groups + inheritance

Any object without a `$value` is a group. Groups carry `$type` and `$description` that children inherit — so you can drop `$type` on every leaf in a ramp:

```json
{
  "color": {
    "$type": "color",
    "$description": "Core palette",
    "neutral": {
      "100": { "$value": "#f5f5f5" },
      "900": { "$value": "#171717" }
    }
  }
}
```

## Composite tokens

DTCG defines composite types where `$value` is an object, not a primitive:

```json
{
  "shadow": {
    "md": {
      "$type": "shadow",
      "$value": {
        "color": "{color.neutral.900}",
        "offsetX": "0px",
        "offsetY": "2px",
        "blur": "4px",
        "spread": "0px"
      }
    }
  },
  "typography": {
    "body-md": {
      "$type": "typography",
      "$value": {
        "fontFamily": "{font.sans}",
        "fontSize": "{font.size.md}",
        "fontWeight": "{font.weight.regular}",
        "lineHeight": "{font.lh.body-md}",
        "letterSpacing": "0"
      }
    }
  },
  "transition": {
    "default": {
      "$type": "transition",
      "$value": {
        "duration": "{duration.fast}",
        "delay": "0ms",
        "timingFunction": {
          "$type": "cubicBezier",
          "$value": [0.4, 0, 0.2, 1]
        }
      }
    }
  }
}
```

The `transition` composite bundles `duration`, `delay`, and `timingFunction` (itself a `cubicBezier` token). Sub-values can be aliased (`duration`, `delay`) or inlined (the `cubicBezier` here). Composite tokens render to the platform's native shape — CSS `transition` shorthand, Swift `UIViewPropertyAnimator` parameters, etc.

Composite tokens can alias individual sub-values — useful for systems that share a font family across many typography tokens.

## Extensions

`$extensions` is a namespaced bag for tool- or system-specific metadata that the DTCG spec deliberately leaves open. Namespace every entry under a stable tool/system identifier (reverse-DNS or a short vendor slug) so entries never collide.

- **Unknown namespaces are ignored by other tooling — that's the design.** Each tool reads only the namespaces it owns and passes the rest through untouched.
- **Keep extension schemas versioned and documented.** Pin a schema version inside the bag so consumers can detect drift, and document the fields somewhere durable.

One worked extension schema is UDTS's, documented in [udts-dtcg-extensions](../udts-dtcg-extensions/SKILL.md) (an incubating L2 stub).

## Common pitfalls

1. **Bare `value` / `type` keys.** Legacy systems use unprefixed names; DTCG ignores them as group children. Codemod before migration.
2. **Top-level `$modes` key.** Multi-mode theming isn't in the DTCG draft. Valid approaches include a namespaced extension (see [udts-dtcg-extensions](../udts-dtcg-extensions/SKILL.md)), Style Dictionary's `$extensions["studio.tokens"].modes`, Tokens Studio sets, or per-mode files. Pick one explicitly.
3. **Alias cycles.** Not caught by the spec; CI must verify.
4. **Composite-token sub-aliasing with wrong type.** `shadow.color` must reference a color token, not a dimension. Validators flag this; if your validator doesn't, your runtime will.
5. **`$type` repeated on leaves under a typed group.** Redundant but not wrong; clean DTCG omits it.

## Cross-references

- **Routed here by:** [designing-a-design-system](../designing-a-design-system/SKILL.md) — the L1 dispatcher for building or extending a system.
- **REQUIRED BACKGROUND:** [token-naming-conventions](../token-naming-conventions/SKILL.md) — the naming principles that extension metadata redundantly encodes.
- **For the version-bump policy when DTCG files change:** [semver-design-tokens](../semver-design-tokens/SKILL.md).
- **For one system's concrete extension schema:** [udts-dtcg-extensions](../udts-dtcg-extensions/SKILL.md) — the worked example.

## Verification

For each DTCG file:

1. **Reserved-key discipline:** every leaf is an object with `$value`; every group has children with `$value`.
2. **Alias resolution:** every `{path}` reference resolves to an existing token.
3. **Type inheritance:** leaves under a typed group don't redeclare `$type`.
4. **No cycles:** alias chains terminate.
5. **Extension consistency:** if the catalog declares a namespaced extension schema, every token carries it consistently and its fields agree with what the token's name declares.

## Sources

- [W3C Design Tokens Format Module](https://tr.designtokens.org/format/) — the spec.
- [Design Tokens Community Group](https://www.designtokens.org/) — group home + discussion archive.
- [Style Dictionary](https://styledictionary.com/) — the reference transformer pipeline.
