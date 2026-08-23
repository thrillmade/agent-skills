---
version: "2d3ef77ae21b"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: curating-a-skill-catalog
description: |
  Use when judging whether a skill earns its place — running or reviewing a skill census cycle, triaging gap:/placement:/revise:/promotion-candidate:/demotion-candidate: issues, deciding to deprecate or promote a skill, or auditing a skill catalog's health. Names the lifecycle state machine (incubating → active → needs-revision → deprecated → retired), the six verdict kinds with their evidence standards (Keep is silent — no issue; Revise needs a fought-usage or stale-source quote; Demote needs zero citations across cycles AND no structural role, with L0-primitive grace; Promotion-candidate needs convergent evolution or a named consumer; Placement needs an applies_to profile or placement-map row naming the repo; Gap needs the concrete recurring case), the prosecutor/defender judgment frame, the top-5-plus-digest noise budget, and the human-editor gate (the census proposes; it never merges or demotes by itself). Cite when a census run files more than ~6 issues, when a demotion is proposed without usage evidence, or when a verdict issue lacks quoted grounds.
---

# Curating a skill catalog

A skill census judges whether each skill in a catalog still earns its place —
not whether its prose is well-written (that's nomination-time content review),
but whether the catalog as a *whole* is the right shape. Every verdict short
of Keep must survive an attempt to refute it, on evidence you can quote.

## When to use

- Running a periodic census cycle over a skill catalog.
- Reviewing someone else's census output before it reaches the human editor.
- Triaging `gap:`, `placement:`, `revise:`, `promotion-candidate:`, or
  `demotion-candidate:` issues.
- Deciding whether a specific skill should be deprecated, promoted, split, or
  merged.
- Auditing catalog health (drift, dead skills, missing coverage) outside a
  formal cycle.

## When NOT to use

- Reviewing a skill's *content* quality at nomination time — frontmatter
  discoverability, voice, missing fields. That's [skill-frontmatter-quality](../skill-frontmatter-quality/SKILL.md),
  gated by the human editor, not a catalog-lifecycle question.
- One-off authoring of a single new skill with no catalog-fit question in
  play. That's [skillforge](../skillforge/SKILL.md).

## Lifecycle state machine

```
incubating → active → needs-revision → deprecated → retired
```

- **incubating** — a stub; not yet load-bearing, exempt from citation-based
  Demote (see L0-primitive grace below).
- **active** — in normal rotation, judged on the same terms as any other
  skill.
- **needs-revision** — a Revise verdict landed; content is stale or fought in
  practice but the skill's *place* in the catalog isn't in question.
- **deprecated** — a Demote verdict landed; on the removal track.
- **retired** — removed from the catalog.

Demotion follows the catalog's own SemVer deprecation discipline, not an
ad-hoc cut: **warn in a minor, remove in a major, notify subscribers**. See
[semver-design-tokens](../semver-design-tokens/SKILL.md) for the underlying warn/remove cycle this borrows.

## The six verdict kinds

**Keep** — the silent default. No issue is filed. Sufficient grounds: none
required — Keep is what happens when no other verdict clears its bar.
Insufficient-to-overturn: a reviewer's hunch that "probably nobody uses this"
with no citation data behind it stays Keep, it does not become Demote.

**Revise** — a fought-usage or stale-source quote. Sufficient: a quoted
review thread where an agent applied the skill's rule and got pushback, or a
quoted dead link / superseded API in its Sources section. Insufficient: "this
reads a bit dated" with nothing quoted.

**Demote** — zero usage citations across multiple census cycles **and** no
structural role (not named as `REQUIRED BACKGROUND` or a cross-reference
target anywhere), with grace for `incubating` L0 primitives that are cited
structurally rather than by usage. Sufficient: "zero citations across three
consecutive cycles; not referenced by any other skill; not L0." Insufficient:
"this feels redundant with X" with no citation count quoted.

**Promotion-candidate** — convergent evolution or a named consumer.
Sufficient: two independent repos quoted arriving at the same pattern
unprompted, or a named skill citing this one as `REQUIRED BACKGROUND`.
Insufficient: "this seems important enough to promote" with no repo or
consumer named.

**Placement** — a skill belongs in a repo that doesn't subscribe (or vice
versa). Sufficient: an applies_to profile or placement-map row naming the
repo. Insufficient: "seems useful there."

**Gap** — the concrete recurring case. Sufficient: three quoted PRs this cycle
each hand-rolling the same missing pattern. Insufficient: "agents might want
this eventually."

A gap's first question is never *what new skill?* — it is *which existing
skill is the natural home?* Compare the case against the catalog's
descriptions before proposing anything new: when an existing skill's scope
should absorb it, the verdict files as **Revise** on the owning skill (an
amendment), not Gap. Only when no existing skill is the right home does it
stay Gap — and the grounds must say why not. (Precedent: the dual-review gap
that first had to check overlap with [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) before
forging.)

Filed labels are symmetric candidates: a demote verdict files as
`demotion-candidate`, a promotion verdict as `promotion-candidate`; the other
kinds file under their own names.

## Prosecutor/defender judgment frame

Argue every non-Keep verdict twice: once as prosecutor (state the verdict,
quote the grounds), once as defender (try to refute it — is there a citation
the prosecutor missed, a structural role overlooked, an L0 exemption that
applies?). A verdict survives only if the defender's refutation fails. **A
verdict whose grounds you cannot quote is a Keep** — no exceptions. This
frame is the same refute-first adversarial-review discipline as
[orchestrating-agent-delegation](../orchestrating-agent-delegation/SKILL.md); the census panel is one instance of a
delegated adversarial review, not a special case.

## Signals hierarchy

Rank evidence in this order; higher always outweighs lower:

1. **Committed manifests** — a placement map or catalog index stating a
   skill's role directly.
2. **Usage citations** — clud-bug review data, or logmind's skills-used log
   once it ships.
3. **Convergent local evolution** — the same pattern independently built in
   two or more repos.
4. **Reviewer intuition** — never sufficient alone; it can motivate looking
   for evidence, it cannot substitute for evidence.

## Noise budget

File at most the **top ~5** strongest-evidence verdicts as individual issues
per cycle; everything else folds into **one digest issue** for the cycle. If
a cycle would need more than ~6 individual issues, that's itself a finding:
the census process gets a `revise:` verdict against this skill — a rubric
that keeps overflowing its own noise budget needs fixing, not the catalog.

## Recursion

This skill is itself subject to census. Note that plainly whenever a cycle
runs over it — a rubric that only ever grades other skills and exempts
itself is exactly the kind of unearned position this process exists to
catch.

## The human editor gate

Every verdict is a **proposal**, addressed to the human editor (the
agent-skills maintainer / CDO). A census cycle never merges a PR, deprecates
a skill, or promotes/demotes one by its own authority — it files the issue
and stops. The editor decides.

## Verification

1. Every non-Keep verdict quotes its grounds inline; ungrounded verdicts are
   downgraded to Keep.
2. Every Demote shows a citation count over multiple cycles **and** an
   explicit structural-role check (or a stated L0-primitive grace).
3. At most ~5 individual issues filed; the rest sit in one digest; more than
   ~6 total triggers a `revise:` against this rubric itself.
4. Any deprecation cites [semver-design-tokens](../semver-design-tokens/SKILL.md)'s warn-in-a-minor /
   remove-in-a-major cycle, not an ad-hoc removal.
5. No issue merges, deprecates, or promotes anything directly — output is
   proposals to the human editor only.
6. Every Gap verdict shows the amend-vs-forge comparison — either the named
   owning skill (filed as Revise) or an explicit statement of why no existing
   skill is the right home.

## Cross-references

- **For content quality at nomination:** [skill-frontmatter-quality](../skill-frontmatter-quality/SKILL.md) — judges
  a skill's prose and discoverability, not its catalog-lifecycle standing.
- **For one-off skill authoring:** [skillforge](../skillforge/SKILL.md) — creating a single new skill
  outside a census cycle.
- **For the deprecation mechanics Demote follows:** [semver-design-tokens](../semver-design-tokens/SKILL.md) —
  warn-in-a-minor, remove-in-a-major, notify subscribers.
- **For the adversarial review frame:** [orchestrating-agent-delegation](../orchestrating-agent-delegation/SKILL.md) —
  refute-first reviewer prompts; the census panel is a delegated adversarial
  review.
