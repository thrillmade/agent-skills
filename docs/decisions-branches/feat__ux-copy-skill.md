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

## 2026-11-05 11:17 - feat: one writing skill per kind of copy — ux-copy renamed writing-interface-copy, writing-marketing-copy and defining-a-voice added, voice-template scaffold, brand-voice-review retired to a pointer, Thrill voice in thrill-design/references/voice.md

**Reasoning:** Owner ruling: one generic writing skill per kind of copy with review built in; voice is per brand from a template; the brand guide sets tone and the generic clarity rules always hold; a client uses the same skills with its own guide on top. Second ruling: skill bodies state rules as the catalog's opinion with no inline attribution; provenance lives in each skill's references/sources.md, verified verbatim against two research dossiers; a rare named killer quote is allowed.

**Alternatives considered:** Keep brand-voice-review as a separate voice/tone review skill — rejected: the ruling puts review inside each writing skill, and it duplicated ux-copy's wording rules (#301), Keep brand-voice-review's full text frozen during a migration window, like skillforge and component-sizing — rejected: that would leave two owners for the same wording rules; a pointer with applies_to intact routes subscribers without a second copy, Put Thrill's voice in thrill-design's SKILL.md — rejected: its body is at the 8192 cap, A new writing-review family member per kind — rejected: one skill per kind, review built in

**Implications:**
- New placement-map family 'writing' (L0) holds the three writing skills; voice-template joins 'templates'; brand-voice-review moves to 'deprecated' and keeps tokenomics as a subscriber until the follow-up lands there
- tokenomics must add writing-interface-copy, defining-a-voice and writing-marketing-copy before running npx skills update on brand-voice-review, since update never adds a skill
- Thrill's voice lives in references/voice.md, which clud-bug never reads (it reads SKILL.md only); a CI review of Thrill copy sees thrill-design principle 4 but not the voice guide
- writing-interface-copy's sources.md records the guides' disagreements (please, we in errors, blame words, your in labels, navigation labels) and the ruling the body states

---

## 2026-11-05 11:51 - fix: #302 review round — L0 pronoun policy and caption rule move to the brand/house layer; filler rules stop flagging copy where the word is the meaning

**Reasoning:** Panel findings: marketing rule 6's I/we policy and interface rule 1's caption rule were house taste in L0; 'automatically', 'not just X but Y' and 'Learn more' were flagged even when they carry meaning; the dry 404 line needed to sit beside the way out so the error still gives a next step

**Alternatives considered:** Keep the I/we split in writing-marketing-copy — rejected: no research supports it and it is a brand's call; it now lives in the voice guide, Drop the 404 example — rejected by the orchestrator: the house 404 pairs the line with the link home

**Implications:**
- Both writing skills now open by telling the writer to load the brand's voice guide; precedence is still stated only in defining-a-voice
- test_check_prose_retention's quoted-example tests are count-free; brand-voice-review left QUOTED_EXAMPLES

---

