---
version: "1.0.1"
digest: "9211a67b1846"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: writing-marketing-copy
description: >-
  Use when writing, editing or reviewing marketing, brand or web copy — a
  landing page, homepage hero, case study, portfolio project page, About page,
  pitch or sales deck, tagline, headline, product page or launch post — and
  when that copy reads vague, salesy, padded, generic or like AI slop:
  adjectives instead of results ("world-class", "innovative", "seamless",
  "cutting-edge", "leverage", "robust", "empower"), claims with no proof, a
  headline that opens with "Introducing" or "Welcome to", a clever headline
  that hides what is below it, triads of abstractions ("fast, flexible and
  scalable"), "not just X but Y", "In today's fast-paced world", narration of
  the reader's experience ("As you scroll, you'll discover…"), passive lines
  that hide who did the work, or one product called three names. Also when
  asked to make page copy shorter, punchier, clearer or more credible. Not for
  interface strings (writing-interface-copy) or a brand's tone
  (defining-a-voice).
kind: writing
---

# Writing marketing copy

**Before writing or reviewing, find and load the brand's voice guide** (discovery order: [defining-a-voice](../defining-a-voice/SKILL.md)). Readers scan, give a page a fraction of its words, and discount boasting, so every rule below spends words on information. Why we hold these: [references/sources.md](references/sources.md).

## When to use

- Writing or reviewing any page, deck or line that sells, introduces or explains a brand or its work.
- Copy called vague, salesy, long or "AI slop".

## When NOT to use

- **Interface strings** — buttons, labels, errors: [writing-interface-copy](../writing-interface-copy/SKILL.md).
- **Tone, humour, we/you policy** — the brand's guide, per [defining-a-voice](../defining-a-voice/SKILL.md).
- **Docs and changelogs** — [technical-writing](../technical-writing/SKILL.md). **Layout of the page** — [composing-a-screen](../composing-a-screen/SKILL.md).

## The rules

**1. Put the point first.** In the page, each section, each paragraph and each heading. A reader who sees only the first two words of a heading, card or bullet should still get its gist. No throat-clearing: "Introducing", "Welcome to", "Here are", "In today's…". *Holds when:* reading only the first two words of every heading and card still tells you what each covers, and each section's first sentence carries its point.

**2. Specific over vague.** Replace any claim a competitor could also make with a fact only you can state: a number, a name, a date, a before and after. Write numbers as numerals. The number must be real and checkable; a precise-looking guess reads as a trick to the sceptical reader you most need. *Holds when:* no sentence would be equally true on a rival's page.

**3. Proof over claims.** Show the result, not the adjective: who did what, for whom, and what changed, with a link to evidence where there is one. Self-praise and hand-picked quotes are weak proof; a named client, a measured outcome and plain disclosure are strong. As David Ogilvy put it, "The more informative your advertising, the more persuasive it will be." *Holds when:* every evaluative adjective ("powerful", "award-winning", "best") is backed by a fact in the same sentence, or is gone.

**4. One idea per line.** A headline says what is below it, works out of context, and carries one idea. No pun, teaser or in-joke unless the plain meaning survives it, and the page delivers what the headline promises. A tagline says who you are and what you do. *Holds when:* each headline, read alone, predicts its section, and splitting it at an "and" or a comma never leaves two claims that stand alone.

**5. Headlines as short as the meaning allows.** Cut every word that carries nothing; keep every word that carries information, even if the line runs long. Keep a page title within about 65 characters, where search results cut it off. *Holds when:* no word can leave a headline without losing meaning, and no `<title>` passes 65 characters.

**6. Active voice, a named actor, and own the work.** Say who did what, in the pronoun your voice guide sets. Passive is allowed to put the key word first or when the actor truly doesn't matter. *Holds when:* each passive meets one of those two, and every claim about the work names who did it, in the guide's person.

**7. Cut filler and machine-made patterns.** Each class, and its fix:
- *Buzzwords* — "leverage", "synergize", "seamless", "cutting-edge", "enterprise-grade", "robust", "empower", "streamline", "world-class": say what actually happens.
- *Intensifiers* — "very", "really", "extremely": delete.
- *Stock openers* — "In today's fast-paced world", "We understand that…": start at the point.
- *Triads of abstractions* — "fast, flexible and scalable": keep the one you can prove, and prove it.
- *"Not just X, but Y"*, "It's not X, it's Y", where X is a strawman nobody claimed: say Y. Keep it when both halves are facts.
- *Significance claims* — "pivotal", "a testament to", "plays a crucial role", "evolving landscape", "showcasing": state the fact.
- *Narrating the reader* — "As you scroll, you'll discover…", "Imagine…": give them the thing.

Use this as a self-edit list, never as proof of who or what wrote a page. *Holds when:* the quick pass finds no unexplained hit.

**8. One name per thing.** A product, client, feature or role keeps one name on every page, slide and caption. Don't vary it for style. Give an invented or branded term a plain gloss at first use. *Holds when:* listing the nouns and clustering synonyms leaves one term per cluster.

## Case studies and project pages

Answer the reader's questions in order: the problem, your role, what you did and why, what you rejected, what changed (with the number), what you learned. Fewer, deeper projects beat many thin ones. Long copy is fine when it is front-loaded and scannable; concision means every word tells, not few words.

## Before and after

| | Before | After |
|---|---|---|
| 1 | Introducing our new approach to onboarding | Onboarding in 3 steps, not 9 |
| 2 | We help businesses grow faster | Clinics on Acme book 30% more visits |
| 3 | Our award-winning team delivers world-class results | Our checkout redesign halved abandoned carts |
| 4 | Fast, flexible and built for teams that move | Scheduling for clinics |
| 5 | How we completely reimagined the end-to-end booking experience | Booking, rebuilt |
| 6 | The platform was designed and launched in 2025 | Acme's team of 4 designed and launched the platform in 2025 |
| 7 | Leverage our enterprise-grade authentication for frictionless onboarding | Sign in with Google or GitHub. No password to manage. |
| 7 | It's not just a tool, it's a partner | Sends your invoices and chases the late ones |
| 8 | the Dashboard, the Console, the Hub (one product) | Dashboard |

Numbers in these rows are illustrative. Real copy uses the measured figure, or none.

## Quick pass

Over page copy, slides or rendered text. Hits are candidates; read each. Irregular participles ("built") need a read. Plant a bad line first.

```sh
grep -nEi "leverag|synergi|seamless|cutting.edge|enterprise.grade|state.of.the.art|best.in.class|world.class|robust|empower|streamlin|innovative|revolutionar|game.chang|frictionless|\bvery\b|\breally\b|extremely|in today.{1,3}s|we understand that|pivotal|testament|crucial role|evolving landscape|tapestry|showcas|\bdelv" copy
grep -nEi "not (just|only|merely) [^.]*but|it.{1,3}s not [^.]*, it.{1,3}s|isn.{1,3}t just|more than just" copy
grep -nEi "(^|[>#\"][[:space:]]*)(introducing|welcome to|here (is|are)|imagine|as you (scroll|explore)|you.{1,3}ll (discover|find))" copy
grep -nEi "\b(is|are|was|were|been|be|being|get|got)( [a-z]+ly)? ([a-z]{2,}ed|[a-z]{3,}en)\b" copy
```

Then read together: headlines' first two words (1, 4), every adjective (2, 3), each passive and pronoun (6), the nouns (8). The read keeps a "not just X, but Y" whose X is a real fact.

## Reviewing copy

Report findings the way [writing-interface-copy](../writing-interface-copy/SKILL.md) does: the string quoted, its file and line, the rule number, and a replacement.

## Silent failures

- **The specific lie.** A precise number nobody measured passes every check here and costs the most trust when caught. Ask where each number came from.
- **Cut to the bone.** Shortening a case study until the role and the outcome are gone passes rule 5 and fails 2 and 3.

## Verification

1. The quick pass ran after a planted control; each hit is fixed or justified.
2. Headlines were read alone, first two words first.
3. Every number traces to a source, and every pronoun follows the voice guide.

## Cross-references

- **Tone and precedence:** [defining-a-voice](../defining-a-voice/SKILL.md). **Interface strings:** [writing-interface-copy](../writing-interface-copy/SKILL.md).
- **House calls:** [thrill-design](../thrill-design/SKILL.md) 4. **Review route:** [reviewing-design-work](../reviewing-design-work/SKILL.md) copy lens.

## Sources

Why we hold these, rule by rule, with the research behind each: [references/sources.md](references/sources.md).
