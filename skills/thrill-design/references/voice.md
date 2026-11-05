# Voice: Thrill

How Thrill sounds, for anything Thrill writes or ships under its own name. It is [voice-template](../../voice-template/SKILL.md) filled in, and the writing skills apply it as [defining-a-voice](../../defining-a-voice/SKILL.md) describes. Linked from [thrill-design](../SKILL.md) principle 4.

## Scope and precedence

Thrill's site, case studies, decks, artifacts, and the interface copy of Thrill's own products. On a client's product the client's guide governs, and this one applies only where that guide is silent.

This guide sets tone. [writing-interface-copy](../../writing-interface-copy/SKILL.md) and [writing-marketing-copy](../../writing-marketing-copy/SKILL.md) hold regardless; this guide tightens them and never loosens them.

## Who we are

A designer showing his own work. He says what he made and what it did, in as few words as it takes, and gets out of the way: the work is the hero ([thrill-design](../SKILL.md) principle 3).

## Traits

| Trait | Do | Don't |
|---|---|---|
| Short, not cryptic | Booking, rebuilt in 2 steps | Booking. Two. Done. |
| Direct, not boastful | I designed the checkout and built its front end. | I single-handedly reinvented how people pay. |
| Specific, not exhaustive | Support tickets fell by a third. | Support tickets fell 33.4% across 11 weeks and 6 regions in Q3. |
| Dry, not jokey | This URL doesn't exist, or maybe it's skiing. (above the link home) | Whoops! This page took a wrong turn! |

## Tone baseline

- Formal ↔ casual: plain and conversational, never sloppy.
- Serious ↔ funny: serious, with a dry line where nothing is at stake.
- Respectful ↔ irreverent: respectful.
- Matter-of-fact ↔ enthusiastic: matter-of-fact. Outcomes carry the enthusiasm, not adjectives.
- Tone words: plain, sure, brief, dry. Anti-tone words: salesy, breathless, corporate, cute.

## Tone map

Outcomes in the examples here are illustrative. Real copy uses the project's measured number, or no number.

| Situation | Traits up / down | Example line |
|---|---|---|
| Everyday interface | All quiet. Labels say what a thing is. | Work |
| Captions | Specific up. Name the thing, don't describe what it does. | Inventory tracker |
| Case studies | Direct and specific up, first person. | I redesigned the review queue. Reviews take half the time. |
| Headlines, site, decks | Short up. | Booking, rebuilt |
| 404 | The one place the dry line may appear, and only beside the way out, never in place of it. | This URL doesn't exist, or maybe it's skiing. → home |
| Empty states | Quiet. Say what is empty and what to do. | No projects yet. Add one. |
| Errors that block a task | Neutral. No humour. | Couldn't send. Check the address and try again. |
| Legal, privacy | Neutral. No humour. | A plain statement of the fact, nothing added. |

## Humour

On, and quiet. Dry, one line, off the primary path, never pointed at, never explained ([thrill-design](../SKILL.md) principle 8). Never in an error that blocks a task, a failure, or anything that costs the reader something. On a 404 it sits beside the way home, never in place of it: the page still gives the next step. If a line needs an emoji or an exclamation mark to read as funny, it isn't the register.

## Person and pronouns

- "I" when he speaks as the designer: "I designed…", "I built…".
- "I" only for work he did. Work a team did says who did what; never a claim of credit he does not hold.
- "We": not yet ruled. Until it is, say "I" for his own work and name the team for a team's.
- The reader is "you", sparingly.

## Vocabulary

- **We say:** names over descriptions. A caption names the thing ("Inventory tracker"), not what it does ("A tool that lets teams track inventory in real time").
- **We avoid:** narration of the page or the reader ("Here you'll find", "Scroll to explore", "Let's dive in"); actorless, padded passive ("was crafted", "has been designed to"); adjectives standing in for outcomes ("seamless", "innovative", "cutting-edge", "world-class"); "not just X, but Y".
- **Fixed names:** one name per project, product and section, the same on the site, in the deck and in the case study.

## Exceptions and owners

None ruled yet. Legal and privacy text follows the tone map's neutral row.

## Mechanics

The generic rules apply. One addition: an interface label says what a thing is, never what to feel about it.

## Before and after

| Before | After | Why |
|---|---|---|
| Here you can explore a selection of my recent projects | Work | No narration; a label names the thing |
| The dashboard was redesigned to improve efficiency | I redesigned the dashboard. Reviews take half the time. | First person, active, an outcome |
| A tool that lets teams track their inventory in real time | Inventory tracker | Name, not description |
| Innovative, seamless digital experiences | Checkout in 2 steps, not 5 | An outcome, not adjectives |
| Oops! Something went wrong 😅 | Couldn't send. Check the address and try again. | No humour in an error |

## How to check it

1. Every line passes the writing skill for its kind first.
2. "Too long" is the most frequent note: for each headline and caption, try cutting a word. If the meaning survives, cut it.
3. Grep the avoid list: `grep -nEi "here you('ll| can)|scroll to|let's dive|was crafted|been designed to|seamless|innovative|cutting-edge|world-class|not just .*but" <files>`.
4. Every "I" names work he did himself.
