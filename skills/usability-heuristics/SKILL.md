---
version: "9d79fc250e83"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: usability-heuristics
description: >-
  Use when a decision or review is about to cite Nielsen's ten usability
  heuristics, heuristic evaluation, Norman on affordances and signifiers,
  Shneiderman's eight golden rules, progressive disclosure, or recognition
  over recall — and when a number arrives attached to one of them: five users,
  3-5 evaluators, 85% of problems, the 7±2 in Shneiderman's rule 8, the
  three-click rule, "users don't scroll". Also use before running a heuristic
  inspection, or reporting one as findings. These are inspection rubrics whose
  only measured properties are defect coverage and inter-rater agreement, so
  the check is never "does it predict" but "which source, which year, which
  edition" — Norman revised affordance across four texts and the list count
  went 10 to 9 to 9 to 10. Gives what each source actually says and what it
  does not license. Does NOT cover the empirical tradition — Fitts, Hick,
  Miller, Gestalt, von Restorff — see empirical-design-principles.
---

# Usability heuristics

## When to use

- A finding is about to be justified by naming Nielsen, Norman or Shneiderman,
  or by a term that moved between editions — affordance, signifier, progressive
  disclosure — or by a number: five users, 3-5 evaluators, 85%, 7±2, three
  clicks.
- Before running a heuristic evaluation, or reporting one as findings.

## When NOT to use

- **Reaching for an empirical principle instead.** Fitts, Hick, Miller, Gestalt,
  von Restorff and the aesthetic-usability effect belong to
  empirical-design-principles, linked below: those predict, and fail by
  predicting wrongly.
- Picking token values, or judging craft quality — see Cross-references.

## The gate: provenance, then reliability

- **Which source, year, edition?** The sibling's falsification gate returns
  nothing here. The failure is a term whose cited meaning was retracted by the
  person *being cited*, hence a year on every row.
- **Would a second evaluator have found this?** Agreement is the measured
  property and it is poor: correct use is several independent evaluators,
  merged. The merge is the method; the abuse is an appeal to a list.

## Nielsen — the list, the method, the numbers

- **Nielsen & Molich, CHI '90** — claimed a usability verdict; actually single
  evaluators found 51/38/26/20% of known problems, and were students and
  magazine readers. Licenses no solo inspection and no substitute for user
  testing: 3-5 independent, merged.
- **The count, 1989 → now** — claimed ten, factor-analysed 1994; actually 10 (a
  1989 course rubric, per Nielsen 2024) → **9** published 1990 → **9** derived
  1994 → 10 today. Seven came from the PCA, two from judgement, h10 from
  neither. The ten, abbreviated from NN/g: system status, real-world match,
  user control, consistency, error prevention, recognition over recall,
  flexibility, aesthetic and minimalist design, error recovery, help and
  documentation.
- **Nielsen, CHI '94** — claimed the ten explain 85% of problems, validated;
  actually "53 factors are needed to account for 90% of the variance", and the
  85% is in-sample coverage of a *different* ten, one rater, on the problems it
  was selected on. It is "excellent for EXPLAINING previously found usability
  problems"; whether it finds new ones "remains to be seen" — the
  audit-checklist use is the one it declines.
- **Hertzum & Jacobsen, IJHCI 2003 (2001)** — claimed an evaluation yields *the*
  problem list; actually any-two agreement is 5-65% across 11 studies,
  undiminished by experience or by severity, which itself correlates 0.24 — so
  no backlog ranking off one reviewer. Their own bound, dated: "the validity of
  UEMs has not been investigated" (2003).
- **h8 aesthetic and minimalist design, 1994/NN-g** — claimed to endorse
  minimalism, whitespace or beauty; actually a density claim: irrelevant
  information competes with relevant for visibility. It does not license fusing
  it with the **aesthetic-usability** effect (Kurosu & Kashimura 1995) — other
  authors, a claim about *perceived* beauty and *perceived* usability, and the
  sibling's.
- **Five users, Nielsen 2000 (Nielsen & Landauer 1993; Virzi 1992)** — claimed
  as a measurement; actually the expected value of N(1-(1-L)^n) at L≈.31,
  assuming equal discoverability and independence. Faulkner 2003, five-user
  subsets of 60: mean ~85% but **range ~55-99%**; Spool & Schroeder 2001, ~35%
  from the first five on four production sites. The 3-5 of heuristic evaluation
  is a different unit, evaluators not participants — though Nielsen & Landauer
  fit **one** Poisson model to both, so the conflation is in the source.
- **Three pinned on Nielsen** — the three-click rule is nobody's: earliest
  located is Zeldman 2001, and NN/g reports no study supports it. He never
  retracted "users don't scroll" — 1997 rescoped it to navigation pages, 2010
  reinforced it by eyetracking — and it was never "a 1994 Alertbox": that column
  began June 1995. Nor does h1 own the 0.1/1/10 s budget (Miller 1968).

## Norman — every term has an edition

- **Affordance: POET 1988 → 1999 → DOET 2013** — the 1988 import, "the perceived
  and actual properties of the thing", is what everyone quotes; Norman disowned
  it in 1999 (he meant *perceived* affordances) and replaced it in 2013
  with "not a property... a relationship". So "a button affords clicking" is
  true but useless; the misuse is "I added an affordance" — it exists
  independently of the screen, and what was added is a signifier.
- **Signifiers, interactions 2008 → DOET 2013** — claimed to abolish
  affordances, on the closer "Forget affordances provide signifiers"; actually
  the same column keeps them three paragraphs in: "there are still perceived
  affordances... but there is more". 2013 divides the labour — affordances
  determine what is possible, signifiers where the action goes, "We need both."
- **DOET 2013, ch. 1 p. 10 vs ch. 2 p. 72** — two lists, not a miscount. Ch. 1
  gives **six** principles of *interaction* — affordances, signifiers,
  constraints, mappings, feedback, conceptual model — with discoverability as
  their *outcome*; ch. 2 gives **seven** "fundamental principles of design",
  those six plus discoverability at #1. Cite the chapter, not the count.

## Shneiderman, disclosure, recall

- **Shneiderman's eight golden rules, 1987 → 6th ed. 2016** — the author's
  framing is the content: "derived from experience... require validation and
  tuning for specific design domains", and "No list such as this can be
  complete." Headings drift between editions while the bodies hold — quote the
  edition you read rather than claim the rules changed meaning.
- **Rule 8, reduce short-term memory load, 6th ed.** — carries "seven plus or
  minus two" in the originator's words, hedged by him as "the rule of thumb".
  Its operative content is narrow: do not make the user carry information
  between displays. It does not cap a menu at seven, a recognition task with the
  items present — Miller 1956 is the sibling's.
- **Progressive disclosure: Star 1982; Carroll & Carrithers 1984** — the
  earliest located printed HCI use is the Star team's, in scare quotes ("hiding
  complexity until it is needed") — they name an existing technique, and who
  coined it is unresolved; Nielsen's 2006 article claims no origin. Its nearest
  empirical relative tested another mechanism: training wheels **blocks**,
  functions visible but unavailable, where disclosure **hides** — one removes an
  error state, the other removes discovery.
- **Recognition over recall (Star 1982; Nielsen h6)** — the memory basis is real
  (Shepard 1967; Standing 1973, 10,000 pictures at ~83%). The strong form is
  not: Tulving & Thomson 1973 and Watkins & Tulving 1975 document recognition
  *failure* of recallable words, and Nickerson & Adams 1979 found under half
  could pick the correct US penny from drawings after lifelong exposure. Visible
  is not recognised.

## Verification

Before a heuristic name carries weight, produce the source, its **year or
edition**, and the sentence supporting the use being made — where that sentence
is the author's own hedge, quote the hedge. Before reporting an inspection, say
how many evaluators produced it: one is a hypothesis list, by the method's own
yield.

## Cross-references

- [empirical-design-principles](../empirical-design-principles/SKILL.md) — the
  falsifiable half: Fitts, Hick, Miller, Gestalt, von Restorff, and the
  aesthetic-usability effect h8 is fused with.
- [reviewing-design-work](../reviewing-design-work/SKILL.md) — phrasing a
  finding once it is sound.
- [frontend-a11y](../frontend-a11y/SKILL.md) — when the "usability problem" is
  really a conformance failure with a normative source and a test.

## Sources

Unreached primaries, not to be sharpened past the rows above: Nielsen &
Landauer 1993 (abstract only); Faulkner 2003 and Spool & Schroeder 2001
(secondary — the range is sound, the tables are not); POET 1988 (via McGrenere &
Ho 2000). Cockton & Woolrych's 69% figure is absent, search-summary-sourced.
