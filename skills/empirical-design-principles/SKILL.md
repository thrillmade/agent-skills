---
version: "69b8422f9b0a"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: empirical-design-principles
description: Use when a layout decision is about to be defended by naming a principle — Gestalt grouping and common region, Fitts's, Hick's, Miller's, Jakob's, von Restorff, the aesthetic-usability effect — or when a rule of thumb like "seven items max" needs checking against what the underlying work actually says. Covers the empirical tradition only, meaning principles that make a prediction which can be tested and can fail. Says which ones predict something real, which four do not say what design writing claims, and how to use one forward as a prediction rather than backward as a post-hoc justification. Does NOT cover usability heuristics — Nielsen's ten, Norman's signifiers, Shneiderman's eight, progressive disclosure, recognition over recall — which are design judgement organised for inspection, not falsifiable prediction; those are in usability-heuristics. Norman's constraints, forcing functions, natural mapping and the gulfs of execution and evaluation are in neither skill and are covered nowhere yet.
---

# Empirical design principles

## When to use

- Deciding spacing, grouping, hierarchy or emphasis on a page, before it is built.
- Reviewing a layout where a principle is being cited as the reason it works.
- Someone proposes a rule of thumb — "seven items max", "reduce the options" —
  and it needs checking against what the underlying work actually says.

## When NOT to use

- **Reaching for a usability heuristic rather than an empirical principle.**
  Nielsen's ten, Shneiderman's eight and the rest are not here, deliberately.
  They make a different *kind* of claim, so they fail differently: a heuristic is
  accumulated judgement organised for inspection, and it fails by missing a
  problem. A principle here predicts, and fails by predicting wrongly. Applying
  one is an act of judgement you defend; applying the other produces a number you
  test. That absence is declared, not covered —
  see [usability-heuristics](../usability-heuristics/SKILL.md).
- **Reaching for Norman's constraints, forcing functions, natural mapping, or
  the gulfs of execution and evaluation.** Neither skill covers them. That one is
  a real gap, not a declared absence: cite the edition and page yourself — DOET
  rev. ed. 2013 ch. 4 for constraints and forcing functions, ch. 1 and 3 for
  mapping, Hutchins, Hollan & Norman 1985 for the gulfs — and do not read either
  file's silence as clearance.
- Picking token values. Contrast, type scale, spacing steps and control heights
  are owned by the system, not by the findings here — see Cross-references.
- Judging craft quality. Whether something is *elite* is a separate question
  from whether its arrangement is well-formed.

## They are descriptive, not prescriptive

Every principle here describes what perception or behaviour *does* under stated
conditions. None instructs you what to build. They are *ceteris paribus* claims —
true when nothing else varies — and an interface is precisely the case where
everything else varies. Palmer, who introduced common region, says so himself:
he calls them "principles" or "factors" rather than laws because "they lack the
quantitative structure of standard scientific 'laws'."

**So use them forward, never backward.** Forward: predict what a layout will do,
then build it and check. Backward: ship the layout, then name a principle that
sounds like what you did. The second is the dominant failure and it is invisible,
because a post-hoc citation is always available for any arrangement — a card grid
with 12/16/20px spacing gets defended as "grouping by proximity" when applied
forward the same principle predicts it fails. Used before, a principle produces
a number you can test; used after, only a name for what already exists.

## The one that changes how you space things

**Proximity works on ratios, and is scale-invariant.** Grouping strength follows
relative distance, not absolute distance — the same layout scaled up groups
identically. Below roughly a 1.5 ratio between competing gaps, no grouping
reliably dominates.

That refutes the common framing. "8px means related, 24px means separate" works
because it is 3:1, not because of the numbers, and it silently stops working the
moment a neighbouring group uses a different base. A spacing scale that
*multiplies* across breakpoints preserves grouping; one that adds a fixed offset
("+8px on desktop") compresses every ratio toward 1 and dissolves the structure it
was meant to protect.

Check ratios, not pixels. 24 against 32 is 1.33 — near-bistable, and readers will
parse it differently on different visits.

## Two that hold, inside a stated scope

- **Fitts's** — movement time rises with distance and falls with target size,
  logarithmically. It models movement to a target of *known* location, not
  finding one, and its edge corollary needs a pointer to pin against, not a
  finger.
- **Jakob's** — users arrive with a model built on other sites, so an unfamiliar
  convention costs errors on first encounter. The measured support is control
  placement and behaviour only; the visual half is Nielsen's opinion.

## Four that do not say what design writing says

Read [interaction-laws](references/interaction-laws.md) before citing any of these.

- **Hick's Law** — "reduce the number of options and nest them into categories"
  is not supported, and on the law's own maths is backwards: nesting charges an
  extra intercept at every level, so the interface looks simpler and measures
  slower.
- **Miller's Law** — "7±2 items in a menu" is the most repeated misquote in
  interface design. The paper is about immediate memory for unrelated items and
  supports no menu limit in any form.
- **The aesthetic-usability effect** (Kurosu & Kashimura 1995; replicated with a
  controlled manipulation by Tractinsky, Katz & Ikar 2000) — users *rate*
  attractive designs as more usable. It is a claim about perception and
  tolerance. The study that manipulated real usability found aesthetics did not
  move actual performance, so it never licenses deferring usability work. It is
  **not** Nielsen's heuristic 8, "aesthetic and minimalist design" — different
  authors, and a density claim about irrelevant information competing with
  relevant, saying nothing about beauty. Fusing the two is the commonest error
  on this entry; the heuristic side is in
  [usability-heuristics](../usability-heuristics/SKILL.md).
- **Von Restorff** — a memory effect, measured by delayed recall of lists.
  Nothing in it addresses click-through, so it cannot justify "make the CTA
  orange and it will be clicked."

## Verification

Before citing a principle in a review, state the prediction it makes and the
observation that would falsify it. If neither is available, the citation is
decoration and the finding should stand on what was actually observed.

For spacing claims, compute the ratio between competing gaps and quote it.

## Cross-references

- [usability-heuristics](../usability-heuristics/SKILL.md) — the judgement half:
  Nielsen's ten and heuristic evaluation, Norman by edition, Shneiderman's eight,
  progressive disclosure, recognition over recall.
- [reviewing-design-work](../reviewing-design-work/SKILL.md) — the dispatcher that
  routes here when a finding is being justified by naming a principle.
- [visual-polish](../visual-polish/SKILL.md) — the rendered-surface lens that catches
  two gaps reading identical; it defers to the ratio above for how far apart they
  then have to be, so do not answer that question from the render alone.
- [designing-elite-ui](../designing-elite-ui/SKILL.md) — the craft bar, once the
  layout is sound.
- [spacing-system](../spacing-system/SKILL.md) — the spacing ramp these ratios
  are expressed in.
- [component-sizing-principles](../component-sizing-principles/SKILL.md) — control
  heights and the 24 CSS px interactive floor.
- [apca-contrast](../apca-contrast/SKILL.md) — figure/ground separation as a
  measured contrast obligation rather than an intuition.
- [consuming-a-design-system](../consuming-a-design-system/SKILL.md), plus your
  own project's design-system skill if it has one — this skill settles the
  arrangement, the system settles the value.

Detail sits beside this file on disk — `npx skills add` copies `references/`
wholesale — so read it there, not over the network:
[gestalt](references/gestalt.md) ·
[interaction-laws](references/interaction-laws.md) ·
[convention-and-memory](references/convention-and-memory.md).
No `blob/main` URL is given: that promises a path that never moves.

## Sources

The three reference files linked above hold 78 source entries. Verification is
partial and the scope is the claim: about 20 were opened and read against the
original — those marked `[read in full]`, plus the ones the inline corrections
turn on — and the rest are DOI- or URL-resolved only. A resolving DOI shows a
work exists, not that it says what the citing line claims. Corrections are
recorded inline, including who actually established figure/ground, common region
and element connectedness, none of whom is Wertheimer.
