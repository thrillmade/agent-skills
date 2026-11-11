---
version: "1.0.2"
digest: "25e825b3cc5a"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: defining-a-voice
description: >-
  Use when a brand needs its voice written down, or when copy is being written
  or reviewed for one: before writing any interface, marketing or web copy for
  a brand, to find its voice guide and apply it; when starting a new client or
  product; when copy sounds "off-brand", "not us", too jokey, too stiff,
  robotic or like every other SaaS; when a line jokes in an error, celebrates a
  routine task, shouts with exclamation marks or ALL CAPS, drifts between "we"
  and "you", or uses a word the brand avoids; when two surfaces of one product
  sound like different companies; or when someone asks for a tone of voice,
  brand voice, voice and tone guide, VOICE.md or BRAND.md. Owns the precedence
  rule: the brand's guide sets tone, the clarity rules hold regardless. Not for
  the wording rules themselves (writing-interface-copy, writing-marketing-copy).
kind: writing
---

# Defining a voice

A voice guide says how one brand sounds. This skill says what a guide must contain, where it lives, how a writer finds it, and what wins when it collides with clarity. The fill-in scaffold is [voice-template](../voice-template/SKILL.md). Why we hold these: [references/sources.md](references/sources.md).

## When to use

- Writing or revising a brand's voice guide, or starting a client.
- Before writing copy for any brand: find its guide first.
- Reviewing copy for tone, register, shouting or pronoun drift.

## When NOT to use

- **Wording rules** — interface strings are [writing-interface-copy](../writing-interface-copy/SKILL.md); pages, decks and taglines are [writing-marketing-copy](../writing-marketing-copy/SKILL.md). Docs are [technical-writing](../technical-writing/SKILL.md).
- **A house's own filled guide** — read it from that house's L2 stance.

## Precedence

**The brand's guide sets tone. The clarity rules hold regardless.** The clarity rules are the two writing skills above plus accessibility. A guide may tighten one of them and never loosen it; where a guide is silent, the generic rule applies. When a trait, joke or flourish makes the meaning, the next step or a label less clear, cut the flourish. As Mailchimp's guide has it, "it’s always more important to be clear than entertaining."

So the calls that vary by brand (whether to say "we", whether to apologise, how much emotion to show) are made in its guide, inside the clarity rules. *Holds when:* no line of copy keeps a voice choice that breaks a clarity rule, and a review that finds one cites the clarity rule.

## Voice and tone

Voice is who the brand is, and it does not change between screens. Tone is how far each trait comes through in one moment. Key tone to the situation (an error, a first run, a milestone), with the reader's likely state as a note, not a guess at their feelings. The more serious the moment, the more neutral the tone.

## What a guide contains

Every section of [voice-template](../voice-template/SKILL.md), in that order. The ones that fail silently when skipped:

1. **Traits: three to five, each "X, not Y",** with one do and one don't example. The "not Y" is the part a reviewer can cite; "friendly" alone licenses anything. *Fix:* give every trait its boundary.
2. **A tone map,** one row per situation or channel — everyday UI, onboarding, success, celebration, minor and severe errors, bad news, legal, marketing, support — each setting how loud each trait is, with an example line. *Fix:* a guide with no error row has not been tested on the moment that matters.
3. **A baseline on four scales** — formal to casual, serious to funny, respectful to irreverent, matter-of-fact to enthusiastic — plus a few target tone words and their anti-words. Stay off the extremes. Lean conversational but credible: when friendliness and trust pull apart, choose trust.
4. **Humour: off unless the guide turns it on,** for named channels. "Humor is extremely risky, because when it fails, you annoy and alienate your users" (Kate Moran, NN/g). Never in an error that blocks a task, a failure, money or health trouble, legal, security or support; on a page like a 404, only beside the way out, never in place of it. When on: one light touch, with the reader, never at them; cut it if the line repeats often or won't survive translation.
5. **Person and pronouns,** stated outright: who "we" is, whether the brand says "I", how it addresses the reader. Brands differ on "we", so a silent guide leaves every writer guessing.
6. **Vocabulary:** words used, words avoided (the team's jargon and the industry's buzzwords), and names that never vary.
7. **Exceptions and owners:** legal, security, incidents, vulnerable customers — how far each drifts from the voice and who signs it off.

## Where the guide lives, and how a writer finds it

Look in this order and use the first guide found:

1. The house's or brand's L2 stance, if loaded, and the guide it links.
2. A voice skill copied from the template: `.claude/skills/voice-<brand>/SKILL.md` (or `.agents/skills/`).
3. `VOICE.md` or `BRAND.md` at the repo root, or `docs/voice.md`.

Prefer 2 in any repo reviewed in CI: it loads like any skill. **Found two?** Say so and ask; don't merge them. **Found none?** Write in a neutral register — plain, conversational, serious, no humour, no exclamation marks — and say in the change that no voice guide exists. Never invent a voice.

**Applying it:** read the traits and the tone-map row for this moment, write, pass the clarity skill's checks, then the checks below.

## Voice checks

These hold under any guide unless it says otherwise, and none can loosen a clarity rule.

- **Shouting.** No exclamation marks in errors, warnings or routine confirmations ("Saved!" → "Saved."); save them for a real milestone, if the guide allows them at all. No ALL CAPS for running text: it is hard to read. Acronyms and codes (USD, API) are fine. *Test:* `grep -nE '!|\b[A-Z]{4,}\b|\b[A-Z]{2,}( [A-Z]{2,})+\b' strings` (an exclamation, a long capitalised word, or a run of them); read each hit.
- **Pronoun drift.** One stance per message. "We need you to confirm before you can continue, and then we'll send you a code" → "Confirm your phone number. You'll get a code by SMS." *Test:* in each message, list the pronouns; "we" and "you" may both appear only as the guide's person rule allows.
- **Register.** Each line matches its tone-map row: no joke or "Oops!" in an error, no "Hurray!" for a routine task. *Test:* tag each string with its situation and read it against that row.
- **Avoid list.** No word from the guide's avoid list. *Test:* grep the list.

## Reviewing copy

Report a voice finding as [writing-interface-copy](../writing-interface-copy/SKILL.md) reports any copy finding — string quoted, file and line, a replacement — naming the trait or tone-map row it breaks. "Could be more on-brand" is not a finding.

## Silent failures

- **The guide the reviewer never reads.** A CI reviewer that reads only `SKILL.md` never sees a `VOICE.md` or a `references/` file: the review goes green and tone is never checked. Ship the guide as a skill, or state the rules a reviewer must hold in the stance's own `SKILL.md`.
- **Voice everywhere.** Personality in an error or a legal notice reads as flippant, and costs trust. The serious rows of the map turn it down.
- **The invented voice.** With no guide, an agent drifts to a generic "friendly, playful" voice. Use the neutral register and report the gap.

## Verification

1. The guide was found by the order above, or its absence was reported.
2. Every trait has a "not" and both examples; the tone map has error and serious rows.
3. Copy passed the clarity skill first, then its tone-map row and the voice checks.
4. A new guide was tried on readers: give them samples and ask which tone words fit.

## Cross-references

- **Owns precedence for:** [writing-interface-copy](../writing-interface-copy/SKILL.md), [writing-marketing-copy](../writing-marketing-copy/SKILL.md).
- **Scaffold:** [voice-template](../voice-template/SKILL.md). **One filled guide:** [thrill-design](../thrill-design/SKILL.md).
- **Inside another system:** [consuming-a-design-system](../consuming-a-design-system/SKILL.md) — obey its guide.
- **Review route:** [reviewing-design-work](../reviewing-design-work/SKILL.md) copy lens.

## Sources

Why we hold these: [references/sources.md](references/sources.md).
