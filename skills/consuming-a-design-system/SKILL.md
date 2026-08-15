---
name: consuming-a-design-system
description: |
  Entry-point dispatcher for CONSUMING a design system in a product — installing its tokens, wiring CSS variables, theming, upgrading across token releases, or deciding whether to extend or fork. Routes to token discipline (reference tokens, never raw hex/px — token-naming-conventions), composition rules (semantic over primitive; themes swap role-to-palette bindings), install patterns (dtcg-format to CSS variables and framework primitives), and migration discipline (semver-design-tokens, token-diff reading, deprecation cycles). Use when the task is using an existing system; for building one load designing-a-design-system; for reviewing design output load reviewing-design-work.
---

# Consuming a design system

You are wiring a product to a design system someone else owns: installing its token release, binding tokens into your CSS/framework layer, theming, or upgrading across a version bump. This skill orients you across that lifecycle and points at the skill that carries each station's actual rules — it does not re-teach them here.

## When to use

- Installing a design system's token package into a product for the first time.
- Wiring tokens to CSS variables, Tailwind config, or framework-native theme primitives.
- Adding or changing a theme (light/dark, brand variant, density) in a product that consumes a system.
- Upgrading across a token release — reading a token-diff, mapping deprecations, choosing a bump-aware upgrade path.
- Deciding whether a product-specific need should alias existing tokens, get proposed upstream, or justify a fork.

## When NOT to use

- Building, extending, or authoring a design system's own token catalog — load [designing-a-design-system](../designing-a-design-system/SKILL.md) instead.
- Reviewing a PR or rendered UI for compliance with a system's rules — load [reviewing-design-work](../reviewing-design-work/SKILL.md) instead.
- This skill is for the consumer side of the relationship only; it assumes the system already exists.

## 1. Token discipline

Product source references tokens through CSS variables or framework bindings — never raw hex, rgb, or px values. Picking the *right* token depends on reading its name correctly (class, kind, role) rather than guessing from context.

**REQUIRED BACKGROUND:** [token-naming-conventions](../token-naming-conventions/SKILL.md)

For user-facing string consistency alongside token consistency, see [brand-voice-review](../brand-voice-review/SKILL.md).

## 2. Composition rules

Prefer semantic tokens over primitives in product code; theme and density are runtime axes, not name segments — see [token-naming-conventions](../token-naming-conventions/SKILL.md).

## 3. Install patterns

A system publishes its source of truth as a DTCG snapshot; everything a product consumes — CSS variables, Tailwind config, iOS/Android/Flutter primitives — is transformed from that snapshot, not authored by hand.

**REQUIRED BACKGROUND:** [dtcg-format](../dtcg-format/SKILL.md)

Pin the version you consume. Treat the transform pipeline (snapshot → transformer → CSS variables / framework primitives) as the install contract: if a product hand-edits the generated output, the next re-generation silently reverts it.

## 4. Migration & upgrade

Before bumping a consumed system's version, read its token-diff report rather than diffing files by eye — the diff is what tells you what actually changed at the resolved-value level, not just the source paths. Map every deprecated token to its replacement during the deprecation window; don't let a removal land as a silent breakage on the next major.

**REQUIRED BACKGROUND:** [semver-design-tokens](../semver-design-tokens/SKILL.md)

The bump severity tells you whether product code must change — see [semver-design-tokens](../semver-design-tokens/SKILL.md).

## 5. Extending vs. consuming

- **Alias, don't fork.** Product-local tokens that need something the system doesn't provide should be authored *on top* — aliasing system tokens — not by duplicating or forking the system's catalog.
- **Fork only when you own the whole lifecycle.** A fork means you now maintain contrast floors, SemVer discipline, and migrations yourself; that's a heavier commitment than most product-specific needs justify.
- **Upstream recurring extensions.** If the same product-local alias keeps getting reinvented across teams, that's a signal to propose it to the system's maintainers rather than let it live as private drift.

One system's worked instantiation of a consumer-facing contract (incubating, not yet loadable): [udts-token-model](../udts-token-model/SKILL.md), [udts-linter-rules](../udts-linter-rules/SKILL.md).

## Cross-references

**L0 primitives:**
- [token-naming-conventions](../token-naming-conventions/SKILL.md) — name-shape rules for picking/validating a token by its name.
- [dtcg-format](../dtcg-format/SKILL.md) — the DTCG interchange format a system's snapshot is published in.
- [semver-design-tokens](../semver-design-tokens/SKILL.md) — SemVer bump severity and deprecation-cycle discipline for token releases.
- [brand-voice-review](../brand-voice-review/SKILL.md) — microcopy voice consistency for user-facing strings.

**L2 stances (incubating — parity markers, not yet loadable guidance):**
- [udts-token-model](../udts-token-model/SKILL.md) — one system's worked token taxonomy as a consumer-facing contract.
- [udts-linter-rules](../udts-linter-rules/SKILL.md) — one system's worked machine-enforceable consumer rules.

**Sibling L1 dispatchers:**
- [designing-a-design-system](../designing-a-design-system/SKILL.md) — building or extending a system (not consuming one).
- [reviewing-design-work](../reviewing-design-work/SKILL.md) — reviewing design output against a system's rules.
