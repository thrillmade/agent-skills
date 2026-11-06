---
version: "1.1.3"
digest: "ab76bd518928"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: thrill-design
description: |
  Use when designing, critiquing or choosing between options for any surface Thrill makes or ships for a client — a page, a product screen, a deck, an artifact, a component set — on any project; the interaction rules in principle 7 name web media features but apply to any platform's input model. Thrill's house taste, stated as nine principles each with a test: subtract until it breaks, reuse one source, the work is the hero, big type with few and distinct words, continuity over cuts, measured not eyeballed, intent travels across screens, delight stays quiet, decide then ship. Cite when a surface reads busy, too much or "not us", when two siblings drifted apart, when chrome competes with the content, when sibling headlines blur together, when a state change cuts or jumps, when a value was eyeballed, when the phone version was invented rather than mirrored, when an easter egg announces itself, or when a decided thing is being reopened. Layered on designing-elite-ui; not for a project already governed by another house's system.
kind: design
applies_to:
  paths: ["site/**", "app/**", "**/site/**", "**/app/**", "**/components/**", "**/ui/**", "**/styles/**"]
  extensions: [".tsx", ".jsx", ".vue", ".svelte", ".astro", ".html", ".css", ".scss"]
---

# Thrill design

Thrill's house taste, for any surface on any project: an L2 house stance layered on [designing-elite-ui](../designing-elite-ui/SKILL.md). That skill is the bar every system shares; this one says which way the house leans where the bar leaves room.

## When to use

- Starting any Thrill surface, before options are drawn — to brief a designer lane or a critic.
- Critiquing Thrill work: "too busy", "too much", "doesn't feel like us".
- Choosing between options that both clear the elite bar.

## When NOT to use

- **Inside another house's or client's own design system** — obey that system's stance ([consuming-a-design-system](../consuming-a-design-system/SKILL.md)); apply these only where it is silent.
- **Measuring a value** — contrast, type, spacing and sizing numbers are owned by [apca-contrast](../apca-contrast/SKILL.md), [type-scale](../type-scale/SKILL.md), [spacing-system](../spacing-system/SKILL.md), [component-sizing-principles](../component-sizing-principles/SKILL.md).
- **Composing from scratch** — [composing-a-screen](../composing-a-screen/SKILL.md) owns the sequence; Gestalt and the laws are [empirical-design-principles](../empirical-design-principles/SKILL.md)'.

## The principles

Where [designing-elite-ui](../designing-elite-ui/SKILL.md) owns the universal rule and its test, this lists only the house lean and points at the principle (DEU n).

**1. Subtract until it breaks** (DEU 9). The house leans further than the bar: minimalism is editing, not a look, and the default answer to "should we add it?" is no. When a surface reads busy, cut before restyling. *Holds when:* the subtraction pass names what it cut, and nothing added since lacks a written reason.

**2. Reuse one source** (DEU 10). When two siblings disagree, fix the class, not the instance: route both through one primitive rather than patching each, and say which primitive in the change. *Holds when:* no fix for disagreeing siblings patches one sibling instead of their shared primitive.

**3. The work is the hero.** Content over chrome. Imagery gets the room it needs — full-bleed where the image is the work, contained where cropping loses content; the facts that matter surface first, in the reader's terms; nav, controls, borders and grounds step back until needed. *Holds when:* at each tested width the largest element in the first viewport is the work, and a search of the page copy finds each key figure once.

**4. Big type, few words, distinct names** (DEU 12). Headlines as short as the meaning allows, as high as the hierarchy affords. DEU 12's actor rule, strictly: never a claim of credit the person does not hold. Copy: [UI](../writing-interface-copy/SKILL.md), [pages](../writing-marketing-copy/SKILL.md); [voice](references/voice.md). Headings name the reader's situation ("Needs a look", not "Exceptions"); empty states answer it, scoped ("Nothing due this week"); counts sit in a chip; deadlines say "by" or "due"; "please" only beside an apology for our failure. *Holds when:* sibling headlines in one column differ; every subject did what it says; no heading is a system noun; each empty state names its scope; no label's text carries its count; and a search finds no "through" deadline or unapologetic "please".

**5. Continuity over cuts.** Objects never jump between states; mechanics are [motion-continuity](../motion-continuity/SKILL.md)'s. The house lean on interruption: user-triggered state changes are atomic — input during a change queues, the change lands, then the next state is computed from current input. Only an ambient or intro sequence may be cut short by input. *Holds when:* motion-continuity's Verification 1 passes, and a click during a change never produces a half-state.

**6. Measured, not eyeballed** (DEU 11, 2, 8). Sizes, grid and contrast are measured, and every check is shown able to fail before its pass is believed. *Holds when:* each size traces to its rule, DEU 8's footprint rule holds, and each check has a control run that went red.

**7. Intent travels across screens.** Layout follows width; behaviour follows input. A small screen mirrors the large one's intent — motion, order, layering, rules — and is bespoke only where forced, with the reason written down. Every hover-only affordance has a touch equivalent the platform's conventions support, or a written reason it has none. Gate behaviour on input capability (on the web, `(hover: hover)` and `(pointer: coarse)`), never on width. *Holds when:* each divergence has a written reason, and narrow-with-mouse and wide-with-touch were both exercised.

**8. Delight stays quiet.** A surprise is earned and discoverable, never a feature competing with the work. It carries no hint copy, sits off the primary path, and costs nothing to someone not looking for it. Hover is a tone change from the theme's neutral ramp before it is an effect. *Holds when:* with every delight removed the surface works and reads the same, and nothing on screen points at one.

**9. Decide, then ship.** An open question goes to an artifact as options first: cheap approximations to lock a direction, and the real page with every state only when it is a real design problem — both with real content and edge cases. A hedged ask ("maybe?") gets a mock, not a build. Once someone with the authority picks, build the pick as the base and ship it; do not keep rotating variants. Change only what was asked: an unasked change to something liked reads as a regression. *Holds when:* the artefact after a decision is the built pick, and a diff answering one question touches only that.

## Scale the check to the change

The rule is [designing-elite-ui](../designing-elite-ui/SKILL.md)'s (Verification). The house lean: a look-and-feel tweak — a fade, a tone, a curve, a line of copy — is one builder on one branch, judged by the decider; no panel, no measurement campaign, since measurement governs sizes, grid and contrast, not feel. The full gate is [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md).

## Silent failures

- **The busy sum.** Each addition passed review; together they are noise. Only a whole-surface subtraction pass (1) finds it.
- **The small screen written fresh.** It re-introduces bugs the large screen solved; brief it as "mirror this; list where and why you differ".
- **Ink on the margin** (DEU 8, broken by a pixel or two) reads as misalignment only beside a neighbour.

## Verification

Scaled to the change, per the section above. For a new surface or structural change:

1. Every *Holds when* above was checked on the render, not inferred.
2. Contrast was measured in every mode [frontend-a11y](../frontend-a11y/SKILL.md) names.
3. Narrow-with-mouse and wide-with-touch were exercised on real input.

## Cross-references

- **REQUIRED BACKGROUND:** [designing-elite-ui](../designing-elite-ui/SKILL.md) — the shared bar this house leans on.
- **Mechanics:** [motion-continuity](../motion-continuity/SKILL.md) (5), [spacing-system](../spacing-system/SKILL.md) (6), [ios-safari-surfaces](../ios-safari-surfaces/SKILL.md) (7, on iPhone).
- **Proving the checks in 6 can fail:** [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md), [proving-an-absence](../proving-an-absence/SKILL.md).
- **Judging the build:** [reviewing-design-work](../reviewing-design-work/SKILL.md).

## Sources

- **House convention, not a standard:** Thrill's own design rulings, abstracted from project work. Where the field holds a matching position it is named: principle 1 — Rams's tenth principle, "as little design as possible" ([Vitsoe](https://www.vitsoe.com/us/about/good-design)); principle 4 — active voice ([GOV.UK style guide](https://www.gov.uk/guidance/style-guide/a-to-z)); principle 5 — see [motion-continuity](../motion-continuity/SKILL.md)'s sources; principle 7 — `hover` and `pointer` are input features, independent of width ([Media Queries 4 §7](https://www.w3.org/TR/mediaqueries-4/#mf-interaction)).
- Principles 1, 2, 4 and 6 defer to designing-elite-ui for the rule and its sources; principle 6 asserts no number of its own; each measurement defers to the primitive that cites it.
