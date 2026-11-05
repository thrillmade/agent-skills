← back to [docs/timeline.md](../timeline.md)

## 2026-11-05 07:22 - feat: ux-copy skill — interface wording rules (L0, design-primitives)

**Reasoning:** The catalog had no owner for interface wording: brand-voice-review owns voice, designing-elite-ui 12 and thrill-design 4 state the bar in one line, and web-interface-guidelines-review §4 restated action labels. ux-copy states the ten wording rules the published content guides share (GOV.UK, Microsoft, Apple, NN/g, Polaris, Atlassian, Mailchimp, Material), each quoted verbatim with a test, and states where the sources disagree and which way it lands.

**Alternatives considered:** Extend brand-voice-review — rejected: voice and wording are separate jobs, and the size gate leaves no room to carry ten sourced rules there, Move brand-voice-review §§1, 3, 4, 6 into ux-copy now — deferred to its own PR (owner ruling R3): tokenomics subscribes to brand-voice-review, and nothing subscribes to or triggers ux-copy yet

**Implications:**
- brand-voice-review §6 narrowed to data-changing controls so it no longer contradicts ux-copy rule 9; WIG §4 routes action-label wording to ux-copy rule 9; designing-elite-ui 12 and thrill-design 4 route wording to ux-copy
- test_the_ceiling_matches_an_independent_arithmetic_model now runs on a fixed 20-skill slice: on the full catalog the ±1 tolerance swallowed the growth_prices_owns_below_the_cap mutation once one more skill landed
- Follow-up issue: complete the brand-voice-review/ux-copy split once a subscriber or trigger covers ux-copy

---

## 2026-11-05 08:10 - fix: ux-copy is L0 — house copy calls move to thrill-design; copy lens wired into reviewing-design-work

**Reasoning:** Audit ruling: L0 skills carry no house taste. ux-copy's [house] items (count in a chip, by/due not through, the narrower please rule, Needs a look and the scoped empty state) are one studio's calls, so they now live in thrill-design principle 4 with a test; ux-copy keeps sourced, universal rules and points at thrill-design for house calls.

**Alternatives considered:** Keep [house]-tagged items in ux-copy — rejected: an L0 primitive that carries one house's lean reads as universal to every other system

**Implications:**
- reviewing-design-work gains a copy lens: ux-copy (kind: writing) in the prose pass, brand-voice-review (no kind, so rule) in the code pass, per SPEC §2.2 and motion-continuity as a fourth rendered lens; WIG drops verb-noun and its tone-drift bullet; brand-voice-review §4 no longer recommends 'Click Continue'
- ux-copy's quotation index moves to references/sources.md so every quote can be checked against its page

---

