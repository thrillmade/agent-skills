---
version: "1.0.2"
digest: "61e0306e7f65"  # is your copy current? github.com/thrillmade/thrill-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/thrill-skills"
name: voice-template
description: Template for one brand's voice guide - scope and precedence, who we are, three to five "X, not Y" traits with examples, a tone baseline, a tone map by situation, humour, person and pronouns, vocabulary, exceptions and owners, mechanics, before/after rewrites and how to check it. Copy to .claude/skills/voice-<brand>/SKILL.md, fill it in, and the writing skills apply it per defining-a-voice.
kind: writing
applies_to:
  author: _REPLACE_ME_
---

# Voice: <BRAND>

How <BRAND> sounds, for anyone writing its interface, marketing or web copy. The writing skills find this file and apply it as [defining-a-voice](https://github.com/thrillmade/thrill-skills/blob/main/skills/defining-a-voice/SKILL.md) describes.

## How to use this template

1. **Copy the directory** to `.claude/skills/voice-<brand>/` and set `name: voice-<brand>` to match. Keep one guide per brand.
2. **Rewrite `description:` for the brand,** so the guide loads on that brand's copy: "Use when writing or reviewing any copy for <BRAND> — interface strings, pages, decks, email — or when copy sounds off-brand. <BRAND>'s traits, tone map, words and pronouns."
3. **Fill in every section below.** Replace each `<…>` and delete the guidance lines in italics. A section that does not apply says so in one line; a missing section reads as forgotten.
4. **When the guide is complete, delete both lines** — `applies_to:` and `author: _REPLACE_ME_` beneath it. The placeholder fails the slug check on purpose, so a half-filled guide never loads; leave it in and the skill stays silent. Don't put your login there: that scopes the voice to your own pull requests.
5. **Keep it under the size cap.** A CI reviewer reads this file and nothing else, so everything a reviewer must hold goes here, not in a linked file.

## Scope and precedence

<What this guide governs: which products, surfaces and channels.>

This guide sets tone. The generic clarity rules — [writing-interface-copy](https://github.com/thrillmade/thrill-skills/blob/main/skills/writing-interface-copy/SKILL.md), [writing-marketing-copy](https://github.com/thrillmade/thrill-skills/blob/main/skills/writing-marketing-copy/SKILL.md) and accessibility — hold regardless. This guide may tighten them, never loosen them; where it is silent, they apply.

## Who we are

<One short paragraph: the brand's role toward the reader — a guide, a partner, a craftsman, a referee — and what the reader comes to it for.>

## Traits

*Three to five. Each is "X, not Y", with one line that does it and one that overdoes it.*

| Trait | Do | Don't |
|---|---|---|
| <X>, not <Y> | <a real line from the product> | <the same line, overdone> |
| <X>, not <Y> | <…> | <…> |
| <X>, not <Y> | <…> | <…> |

## Tone baseline

*Where the brand sits by default. Stay off the ends of every scale.*

- Formal ↔ casual: <position>
- Serious ↔ funny: <position>
- Respectful ↔ irreverent: <position>
- Matter-of-fact ↔ enthusiastic: <position>
- Tone words: <three to five words the copy should fit>. Anti-tone words: <the ones it must never fit>.

## Tone map

*One row per situation. The more serious the moment, the more neutral the tone. Every guide has the error rows.*

| Situation | Reader is likely | Traits up / down | Example line |
|---|---|---|---|
| Everyday interface | <…> | <…> | <…> |
| Onboarding, learning | <…> | <…> | <…> |
| Success, routine | <…> | <…> | <…> |
| Celebration, real milestone | <…> | <…> | <…> |
| Minor error | <…> | <…> | <…> |
| Severe error, data or money at risk | <…> | <…> | <…> |
| Bad news | <…> | <…> | <…> |
| Legal, security | <…> | <…> | <…> |
| Marketing, web | <…> | <…> | <…> |
| Support | <…> | <…> | <…> |

## Humour

*Off unless this section turns it on.* <Off. — or — On in: <channels>. Never in errors, failures, money or health trouble, legal, security or support. Size: <one light touch per surface>. Target: with the reader, never at them.>

## Person and pronouns

- "We" means <the company / the team / never used>.
- The brand <does / does not> speak as "I"; <when>.
- The reader is <"you" / named by role>.
- Possessives in labels: <rule>.

## Vocabulary

- **We say:** <word> (not <word>), <…>
- **We avoid:** <jargon, buzzwords, words that judge the task>
- **Fixed names:** <product, feature and action names that never vary>

## Exceptions and owners

| Content | How far it drifts from the voice | Signed off by |
|---|---|---|
| <Legal> | <…> | <…> |
| <Security, incidents> | <…> | <…> |

## Mechanics

*Only the choices the generic rules leave open.*

- Contractions: <…>
- Exclamation marks: <never / only for a real milestone>
- Emoji: <…>
- "Sorry": <only when we are at fault, once, with what happened>
- Case for buttons and headings: <sentence case / title case>

## Before and after

*Three to six real rewrites, at least one an error.*

| Before | After | Why |
|---|---|---|
| <…> | <…> | <trait or row> |

## How to check it

1. Each new line was read against its tone-map row.
2. The vocabulary's avoid list was grepped.
3. When the guide changes, readers are given samples and asked which tone words fit.
