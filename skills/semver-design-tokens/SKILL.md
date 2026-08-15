---
name: semver-design-tokens
description: |
  Use when applying SemVer to a design-token release, computing a version bump from a token-tree diff, or auditing a release for correct severity. Names the compute-from-the-diff policy (major = remove / rename / type-change / class-change; minor = add or deprecate; patch = value-only or alias-rebind-preserving-value), the alias-chain awareness rule (compute by resolved values, not source paths), the snapshot-per-release convention, the deprecation cycle (warn in a minor, remove in the next major), and the pattern of documenting an explicit pre-1.0 relaxation. Cite when an agent picks a bump by intuition rather than computing it from the diff. For one system's concrete policy choices see udts-semver-defaults.
---

# SemVer for design tokens

Design tokens are an API. Consumers depend on **names** (the contract) and **resolved values** (the rendered output). Compute the bump from a structured diff between successive snapshots — humans don't pick the bump; the diff does.

## When to use

- Computing the next version number for a token release.
- Auditing a proposed release for under- or over-stated severity.
- Reviewing a PR that changes tokens and the proposed bump.
- Reading a token-tree diff and classifying each entry by SemVer impact.

## When NOT to use

- Non-token releases (purely tooling changes, docs, build infrastructure). Use ordinary SemVer for those.
- Internal-only releases that have no external consumers — `0.x` SemVer suffices, no formal compute needed.

## The bump policy

The bump is computed from the diff between the previous published snapshot and the current. Each diff entry maps to a severity; the release's bump is the **highest** severity across all entries.

### Major (breaking)

- Token **removed** (its name is gone from the catalog).
- Token **renamed** (a name disappears and a new name appears; even if the resolved value is identical).
- Token's `$type` **changes** (color → string, dimension → number, scalar → composite).
- A token's declared **class** changes (e.g. contrast-bound to free) — a contract change.
- A theme is **removed**, or the default theme is **swapped**.
- The DTCG export structure changes (groups reorganized, paths shifted).

### Minor (additive, backwards-compatible)

- New token added.
- New theme added (existing themes untouched).
- New alias pointing at an existing token.
- New output target / platform added.
- A token is marked **deprecated** (still resolves; only metadata changes).

### Patch (value-only)

- A token's `$value` changes within visual noise (rounding, hex casing, equivalent color representation).
- A token's `$description` or other metadata changes.
- An alias is rebound to a different source token **whose resolved value is identical**.
- Build / tooling fixes that produce byte-identical resolved output.

## Compute from resolved values, not source paths

Evaluate the diff against **resolved values**, not source paths. This matters for alias chains:

If `button-bg-primary-default → primary-contrast-500 → teal-180-harmony-500 → #008b8b` and you change `teal-180-harmony-500`'s OKLCH value, **every alias inherits the major-bump consideration** — even if `button-bg-primary-default`'s name didn't change.

The compute is:

```
for each token in current_catalog:
  resolved_now  = resolve(token, current_catalog)
  resolved_prev = resolve(token, previous_snapshot)
  if resolved_now != resolved_prev:
    classify by the severity rules above
```

Source-path diffs miss this. A linter that only diffs source paths reports "no change" when the leaf primitive changed; the resolved-value diff catches it.

## Pre-1.0 relaxation

Per the standard SemVer caveat, `0.x.y` is "anything goes." A `0.x` catalog is still shaping its contract, so document an **explicit** relaxation rather than leave the behavior undefined. One reasonable relaxation (the one UDTS documents — see [udts-semver-defaults](../udts-semver-defaults/SKILL.md)):

- **Removals are minor**, not major. Pre-1.0 catalogs are still actively shaping their contract; removing tokens that turn out to be wrong shouldn't burn a major.
- **Renames remain minor** for the same reason.

Whatever relaxation you document, **type changes stay major even pre-1.0** — that level of break shouldn't be silent.

Cut 1.0 **before** you have external consumers, not after. The relaxation is for the system-design phase, not for shipping breakage to a stable consumer base.

## Snapshot storage

Store every published snapshot; it is the diff target for the *next* release's bump compute. One convention is to commit each release's snapshot at `snapshots/v<X>.dtcg.json` in the repo:

```
snapshots/
  v1.0.0.dtcg.json
  v1.1.0.dtcg.json
  v1.1.1.dtcg.json
  v2.0.0.dtcg.json
```

Snapshots are large (catalogs run hundreds to thousands of tokens) but flat key→value JSON that compresses well and diffs cleanly. The first published snapshot is `0.1.0`, not `1.0.0` — the npm convention applies.

## Deprecation cycle

A token marked for removal goes through a deprecation cycle:

1. In version `N.x` (minor bump): the token gains `$description` noting deprecation + a pointer to its replacement.
2. The token remains resolvable through the rest of the `N.x` line.
3. In version `N+1.0` (major bump): the token is removed.

Never remove a token without a prior deprecation release. Consumers rely on the cycle to migrate gracefully.

## Theme value changes

A theme's resolved values changing is a separate axis:

- **Default theme value change:** classify per the bump policy above. Most value changes are patch; some are major (semantic role flip — `danger` becoming green).
- **Non-default theme value change:** classify the same way IF the theme is GA. If the theme is explicitly **experimental** (documented as such), value changes within it are minor regardless of severity.

## Cross-references

- **REQUIRED BACKGROUND:** [dtcg-format](../dtcg-format/SKILL.md) — the snapshot format the diff operates on.
- **For name conventions that the bump rules reference:** [token-naming-conventions](../token-naming-conventions/SKILL.md).
- **For one system's concrete policy choices (worked example):** [udts-semver-defaults](../udts-semver-defaults/SKILL.md).

## Verification

For each release candidate:

1. **Diff resolved values**, not source paths.
2. **Classify every diff entry** by the bump policy.
3. **Bump = max severity** across all entries.
4. **If the catalog documents a pre-1.0 relaxation, it's applied exactly as documented.**
5. **Snapshot stored** at `snapshots/v<new>.dtcg.json` before tagging.
6. **Deprecation cycle honored** — no removals without a prior minor that marked the token deprecated.

## Sources

- [SemVer 2.0.0](https://semver.org/) — the underlying spec.
- The [udts-semver-defaults](../udts-semver-defaults/SKILL.md) skill — one system's concrete versioning-policy choices (incubating).
- [Style Dictionary's release notes](https://github.com/amzn/style-dictionary/releases) — practitioner reference for how token systems version in practice.
