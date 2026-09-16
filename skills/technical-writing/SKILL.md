---
version: "1.0.0"
digest: "13e8b85d472a"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: technical-writing
description: Flag a PR that ships a new env var, CLI flag, config key, exported function/type, or endpoint with no matching doc or changelog entry — working and undocumented, not broken. Apply to any addition, a new capability with no removal or behavior change to existing surface. Not for a reversed or superseded value (see retiring-a-superseded-decision) or a breaking API change (see api-contract-enforcement); pairs with the latter when a finding also touches behavior.
kind: writing
---

# Technical writing

A shipped addition and its documentation are two separate facts, and only one
is checked by CI. `check-doc-links.yml` proves links resolve; `check-prose-
retention.yml` stops prose disappearing unannounced. Neither asks whether a
*new* env var, flag or export has a matching line anywhere — both are built to
catch loss, not silence, and an addition is not a loss. The clud-bug seed
(`CLUD_BUG_NOTARY_URL`, `--bundle`) shipped working and undocumented; this
repo's own `bd1b554`/`8f7fdbb` F2 pass existed to close the same gap a second
time, independently. Two occurrences is a pattern, not a one-off.

## When to use

- A diff adds a new env var, CLI flag, config key, exported function/type, or
  endpoint that runs correctly and ships with no doc or changelog line naming
  it.
- You are closing a "docs truth" pass and need to confirm every addition since
  the last one is covered — not just that the existing docs still resolve.
- A PR's own description claims a capability the diff adds, but no README,
  `--help` text, docstring or CHANGELOG entry says so anywhere in the tree.

## When NOT to use

- **The change reverses an earlier value.** `retiring-a-superseded-decision`
  owns this, and says why it doesn't cover the addition case: *"The decision
  is new and replaces nothing — no old value to hunt."* An addition has no old
  value by definition — that gap is this skill's case, not that one's.
- **The change breaks an existing surface.** `api-contract-enforcement` owns
  removed fields, renamed parameters, changed status codes, tightened
  validation — and disclaims itself only where *"the change is purely
  additive — adding a new optional field, new endpoint, new CLI flag — with no
  removal or behavior change to existing surface,"* which is precisely this
  skill's territory, not its own.
- **The finding is about the diff's behavior, not its documentation.** This is
  a `kind: writing` skill; per SPEC §2.2 it must not be the sole citation for
  a claim about code behavior — pair it with the `rule` skill that owns that
  surface (often `api-contract-enforcement`) when the code itself, not only
  its coverage, is in question.

## Search the new surface, not the old one

An addition has nothing to contradict, so there is no stale sentence to find —
the failure mode is a gap, not a lie, and the thing to search for is the new
name itself: the flag's own spelling, the env var's own spelling, the export's
own spelling, across every doc location (README, CHANGELOG, `--help` text,
docstrings). A hit is coverage; nothing is the finding. Control-test the search
first against an addition you already know is documented, per
`proving-an-absence` — a search that finds nothing may be the search, not the
repo.

## Changelog cadence

The same PR that ships the capability states what changed, in the format its
readers use — not a promised follow-up. SemVer ties this to a version-visible
fact: "MINOR version when you add functionality in a backward compatible
manner" (semver.org §7–8). Keep a Changelog is one worked instantiation of the
cadence itself: an `Unreleased` section at the top, entries grouped by type
(`Added`/`Changed`/`Deprecated`/`Removed`/`Fixed`/`Security`), one section per
version. Two named systems make the rule machine-checkable instead of a habit
to remember: Changesets gates a merge on `changeset status --since=main`
failing when code changed with no changeset file; towncrier requires one
newsfragment file per PR, assembled into the changelog at release. Neither is
prescribed here — the generic rule is that the PR adding the surface also
states it; which mechanism enforces that is the repo's own choice.

## Verification

1. Grep the new surface's own name across doc locations; control-test against
   a known-documented addition first, so a broken search doesn't read as a
   clean repo.
2. Confirm the changelog entry (or the repo's chosen mechanism) landed in the
   same PR — not a promise to add it later.
3. If the finding also touches the diff's behavior, pair it with the
   code-aware skill that owns that surface; this skill's citation alone does
   not cover a behavior claim.

## Cross-references

- [retiring-a-superseded-decision](../retiring-a-superseded-decision/SKILL.md)
  — the reversed-value case this skill excludes; search the old value, not
  the new one.
- [api-contract-enforcement](../api-contract-enforcement/SKILL.md) — the
  breaking-change case this skill excludes; pair with it when a finding also
  touches behavior, per SPEC §2.2.
- [proving-an-absence](../proving-an-absence/SKILL.md) — control-testing the
  "no doc found" grep before reporting it.

## Sources

- Keep a Changelog 1.1.0, keepachangelog.com — the `Unreleased` section and
  the `Added`/`Changed`/`Deprecated`/`Removed`/`Fixed`/`Security` categories.
- Semantic Versioning 2.0.0 §7–8, semver.org — MINOR for backward-compatible
  additions.
- Changesets, github.com/changesets/changesets `docs/automating-changesets.md`
  — `changeset status --since` as a merge-time gate.
- towncrier, github.com/twisted/towncrier — one newsfragment file per PR.
- protocol SPEC §2.2, github.com/thrillmade/protocol `SPEC.md` — `kind`
  routes a skill to a pass; the pairing rule this skill's `kind: writing`
  is bound by.
