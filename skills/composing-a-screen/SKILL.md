---
version: "8137c5e68601"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: composing-a-screen
description: |
  Entry point for MAKING a screen — deciding what is primary, what groups with what, what shares an edge, and what waits behind a click, before any pixel, token, or component is picked. Names the composition sequence (rank → group → encode → space → lay out → conventionalise → target → clear the floors → defer) and carries the principles nothing else in this catalog owns: visual hierarchy and the attribute that must separate each level on its own, proximity as a between-to-within gap ratio rather than a pixel count, column count and measure, alignment as an axis count, and progressive disclosure with the three tests anything hidden must pass — plus Jakob's Law (standard / convention / confusion), Fitts's Law (cut the distance before you grow the target), and Norman's two gulfs (gulf of execution: is the next action findable; gulf of evaluation: is its result visible). Use when asked which design principles apply to a screen, when a layout has to be composed from scratch, when ranking actions before picking button variants, when a user can't tell what to do next or whether an action worked, or when an interface shows more at once than the task needs. Not the visual bar (designing-elite-ui), not judging work that already exists (reviewing-design-work), not the scales themselves (spacing-system, type-scale, component-sizing-principles), and not contrast or accessibility thresholds (apca-contrast, wcag-contrast, frontend-a11y). Cite when every element on a screen carries equal weight, when every gap is the same step, when a group's inner and outer spacing match, when a paragraph runs the full width of the viewport, or when every option is visible at once.
---

# Composing a screen

Composition has a dependency order — you cannot encode a hierarchy you have not ranked, or space a group you have not drawn. Run the nine steps before writing markup and **write each step's answer down**; that list, not the markup, is this skill's output. Each step gives a default and what changes it, and where the answer is judgement it says so rather than fake a number.

## When NOT to use

- **Not this skill:** judging existing work → [reviewing-design-work](../reviewing-design-work/SKILL.md) · contrast and accessibility thresholds → [frontend-a11y](../frontend-a11y/SKILL.md), `apca-contrast`, `wcag-contrast` · empty, loading and error states, and whether the chosen steps read → [visual-polish](../visual-polish/SKILL.md).
- **Pick values from, never invent:** [spacing-system](../spacing-system/SKILL.md), `type-scale`, `component-sizing-principles`, `line-height-grid`, `oklch-color-space`.
- **REQUIRED BACKGROUND:** [designing-elite-ui](../designing-elite-ui/SKILL.md), the bar this must survive.

## The sequence

**1. Rank before you place.** *(Judgement, no threshold.)* What one task is this screen for; what must be read to *decide* to do it; what to *do* it; what only a minority asks for. **Rank 1 is one thing and one primary action.** Rank 4 and below is a disclosure *candidate* — collect them; step 9 adjudicates each. A list that won't write means too much content: cut, don't add a level.

**2. Group before you space.** Draw the boundaries as *sets*, in prose. **Name each group in three words or fewer; a group you cannot name is not a group.** Separate with space alone, escalating only on a condition: a background shift when step 4's 2× won't fit the container, a shadow only for a floating plane, a border only when two adjacent groups need one.

**3. Encode the hierarchy.** Give every level **one attribute that separates it on its own** — size, weight, colour, position, enclosure, whitespace. A second is free and helps; the failure is a level findable only by *intersecting* two that neighbouring levels each own — a conjunction, and conjunction search is far slower (~60 vs ~3 ms/item). **Default: three levels — size, then weight, then colour**; for a fourth spend position, enclosure or whitespace before you spend a conjunction. **De-emphasise before you emphasise:** if rank 1 doesn't stand out, lower 2 and 3.

**4. Space by ratio, not by pixel — proximity is relative.** Per group compute **`between ÷ within`**. **Default ≥ 2** — two distinct steps off the ladder, never one step twice. **Below 1 the grouping is inverted**: items read with the wrong neighbours. Anchor the absolutes too — 16 within / 32–48 between for content, 8 / 16–24 for dense data. Across breakpoints **multiply the ramp, never add to it**: `+8px on desktop` drags every ratio toward 1.

**5. Set the columns, then collapse the axes.** **Default: one column, body text 45–75 characters per line** — a full-viewport paragraph is the commonest agent layout defect and passes every other rule here. Then count the distinct start edges and baselines per group and drive it down. *(Judgement — no evidence backs a count.)* **Default: one axis per group**; an axis holding one element is a defect. Align to the **start**, never a hard-coded `left`, so RTL survives. Never justify body copy — a house rule, not a floor: SC 1.4.8 is **AAA** and asks only for an unjustify *mechanism* (F88). Centre nothing meant to be read. Right-align numerals **in a column**, never alone in a form.

**6. Take the conventional form — Jakob's Law.** *"Users prefer your site to work the same way as all the other sites they already know"* (Nielsen 2000). Classify each control from memory: **standard** — you cannot name three products that differ (comply; deviating is a defect); **convention** — you can name three each way (comply unless you write the reason); **confusion** — no nameable pattern (choose freely). Defaults worth taking: logo upper-left linking home; nav top or left; account far right; breadcrumbs above the H1; submit ending its form, bottom-right of its group, cancel to its left and never primary; `×` top-right. Nielsen 2004 measured search *placement* as confusion, not standard — **the class you assume is the class you get wrong**. It governs placement and behaviour, **not** typeface, palette, motion, or voice.

**7. Cut distance, then grow the target — Fitts's Law.** Movement time **rises** with the log of distance ÷ target size, and halving the distance buys about what doubling the target buys — so **cut distance first, which is free; raise size second, which costs layout**. Put the next action beside what was just touched, and **make the whole row or card the target, not the 16 px icon inside it**. **Name the input device first:** pointer → a 24 px floor, screen edges and corners effectively infinite; touch → 44 px comfortable, edges worth nothing.

**8. Clear the floors, then stop.** Computed, not judged — and *layout* decisions, so settle them now rather than retrofitting: contrast (a pass is not legibility, and colour is never the only difference between two states), 24×24 CSS px targets, reflow at 320 CSS px with no two-dimensional scroll, containers that survive text-spacing overrides, repeated nav that keeps its relative order. Every SC number and conformance level is `frontend-a11y`'s; consistency past nav order is `design-system-consistency`'s.

**9. Defer the rest — progressive disclosure.** **Default to visible** — hiding is a cost paid for a named reason. Every rank-4 candidate passes **all three** or stays on the screen:

1. **Sufficiency** — the primary task completes, correctly, without opening it.
2. **Decision-completeness** — the user can decide *whether* to do it without opening it. A hidden price or constraint fails here even when the task completes.
3. **Predictability** — the trigger names its contents: "More options" fails, "Shipping options" passes. Better, derive it from what was just selected.

Fail one and it does not get hidden. **Two levels maximum** — anything reachable only through another disclosure comes back out. **Never hide the whole navigation:** fully hidden cost ≥39% desktop task time, while a *combo* — top destinations visible, the rest behind a control — measured like fully visible, and is the mobile answer where the hamburger is standard. A wizard is *staged*, not progressive: everyone walks every stage.

## Worked example — an invoice page

Rank: 1 amount due + Pay; 2 due date and sender; 3 line items; 4 payment history → step 9. Groups: {amount, due date}, {from, to}, {line items}, {total}. Encoding: amount two size steps up and bolder, labels one weight down, nothing else coloured. Gaps: 8 within, 24 between → 3.0. Layout: one column at 60ch, one start axis, totals right-aligned. Deferred: "Payment history (3)" — passes all three.

## Verification

1. **Blur test.** Blur ~8 px and read the rank order off it. Ambiguous, or not step 1's order, means hierarchy failed.
2. **Gap ratios.** Per group print `between ÷ within`: below 1 inverted, 1–1.5 a defect, 1.5–2 a warning.
3. **Axis count.** Cluster elements by the edge their computed `text-align` uses, within 1 px, skipping centred text; a cluster of one is a stray axis.
4. **Disclosure.** Depth ≤ 2; no trigger matching `More|Advanced|Options|Details` without a noun; primary task completed without opening anything hidden.
5. **Deviations.** Every non-standard control from step 6 carries its written reason.
6. **Two gulfs (DOET rev. ed. 2013 ch. 2).** Execution: next action findable? Evaluation: result visible?

## Sources

Treisman & Gelade 1980 (the ms/item split; a continuum since Wolfe 2021) · Kubovy via Wagemans 2012 p. 1184 · Fitts 1954 · Nielsen 2000, 2004, 2006 · NN/g 2016, n=179. Scope: the grouping ratio is dot lattices transferred to UI, not measured on it — which is why 2 is a default, not a discovery.

**Do not repeat:** modular type-scale ratios (1.25, 1.618) have no empirical validation, and "80% of customers lost" for Jakob's Law is uncited by Nielsen.
