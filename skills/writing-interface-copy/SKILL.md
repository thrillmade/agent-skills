---
version: "1.0.3"
digest: "2d2d0dc59dad"  # is your copy current? github.com/thrillmade/thrill-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/thrill-skills"
name: writing-interface-copy
description: >-
  Use when writing, editing or reviewing the words inside a product interface —
  buttons, links, field labels, placeholders, headings, status badges, empty
  states, toasts, captions, confirmations and error messages — and when UI copy
  reads padded, wordy, robotic or like AI slop: the screen narrating itself
  ("Here you can see…", "You are now viewing…"), a status written as a sentence
  ("Waiting for you"), a label wrapped in a frame ("At the date", "Your current
  status is"), passive or actorless lines, filler ("simply", "just", "easy",
  "in order to", "make sure", "please note", "you should"), "click here" or
  "Learn more" links, a subtitle repeating its title, one thing called by two
  names, title-case drift, "OK" or "Submit" where a specific action exists, an
  error that blames, says "Please try again later" or gives no next step. Also
  when asked to make interface copy shorter, cleaner or more minimal. Not for
  voice and tone (defining-a-voice), marketing pages (writing-marketing-copy)
  or documentation (technical-writing).
kind: writing
---

# Writing interface copy

**Before writing or reviewing, find and load the brand's voice guide** (discovery order: [defining-a-voice](../defining-a-voice/SKILL.md)). A system's own content guide decides style and tone calls within these rules.

## When to use

- Writing or reviewing any string a user reads in a product.
- Copy called wordy, robotic or "AI slop".

## When NOT to use

- **Voice and tone** — shouting, register, we/you drift: [defining-a-voice](../defining-a-voice/SKILL.md).
- **Marketing, brand and web pages** — [writing-marketing-copy](../writing-marketing-copy/SKILL.md).
- **Testing accessible names** — [frontend-a11y](../frontend-a11y/SKILL.md). **Docs** — [technical-writing](../technical-writing/SKILL.md).
- **Not product copy** — internal identifiers, logs, user-written text, and a flagged A/B variant testing wording on purpose.

## The rules

**1. Name it; don't narrate it.** A screen that needs explaining needs fixing. Cut "here you can", "you can now", "you are now viewing". *Holds when:* no label, heading or caption describes the screen or what the user does on it.

**2. A label is the noun, not a frame.** "Favorites", not "Your favorites". Action labels and sentences may say "your". *Holds when:* cutting a noun label to its noun phrase loses nothing.

**3. Status is a state word.** One word; two only for a state one word cannot hold; past tense for a finished action ("Shipped", not "Ship"). No pronouns. *Holds when:* each status is one or two words, and every finished action reads as done.

**4. Name the user's situation, not the system's category.** Use the words users already have, not the team's; name a service by the task, not the technology. Keep a domain's term of art ("Action items" in a meeting tool). *Holds when:* each heading answers "what is this to me?" and keeps one name everywhere (rule 7).

**5. Say it once.** No subtitle restating its title, no page heading repeating the title bar. Every field keeps a visible label; a placeholder vanishes on typing, so it carries only a hint ("name@example.com"). Exempt: an error naming its field ("Enter an email address" under "Email"), and a dialog naming an object nothing else on screen names. *Holds when:* no child string repeats its parent's entity, bar those, and no field relies on a placeholder for its label.

**6. Active voice; name the actor.** A passive with no actor is the hardest sentence to parse. Passive is allowed to avoid blaming the user, to stress the action over the actor, or to put the keyword first. *Holds when:* each `be`- or `get`-passive names its actor or meets one of those three.

**7. One name per thing, one case style.** Two words must never leave a user wondering if they mean one thing. Follow the project's case pattern for buttons and labels — sentence case unless the project consistently uses title case — and flag a new label that drifts. *Holds when:* clustering the nouns in headings, buttons and errors leaves one term per cluster, and no label breaks the case pattern.

**8. Cut filler.** By class, with the fix:
- *Empty adverbs* — "successfully", "quickly", "automatically" where nothing manual was expected: delete. Keep one that is the meaning ("Renew automatically").
- *Words that judge the task* — "just", "simply", "easy", "quick": delete; they insult whoever finds it hard.
- *Stage directions and hedges* — "make sure", "be sure to", "go ahead", "feel free", "you should", "might want to", "it may be possible to": give the instruction ("Save your work") or "you can".
- *Long forms* — "utilize", "in order to": "use", "to".
- *"Please"* — only when asking for something inconvenient, or when the product is at fault.
- *Vague links* — "click here", "more", a bare "Learn more": name the destination ("Learn more about data retention", "Read the migration guide"). "Click" names the hardware, not the intent.

*Holds when:* the quick pass finds no unexplained hit.

**9. Buttons and links say what they do.** A control that changes data starts with the verb naming the change ("Send invitation", "Save profile"); one that only navigates may name its destination ("Settings"). OK belongs only on a purely informational alert. A radio "No" or a status "OK" is not an action. No emoji in a button or link label; a screen reader reads its name aloud. *Holds when:* no button or link reads OK, Submit, Yes or No outside an informational alert, each predicts its result, and the emoji check finds none.

**10. Errors: what happened, what to do, no blame.** The thing is the subject, never the person. "We" only when the product failed. Never invent a cause or a requirement; state a real one plainly ("Your card was declined", "The file must be a PNG", not "Make sure…"). No "invalid", "illegal" or "incorrect"; no "Please try again later" — give the next step or the live state ("Connection lost. Reconnecting…"). *Holds when:* each error has a next step, or sits inline on the field it names ("Wrong password"), and never makes "you" the cause.

## Before and after

| | Before | After |
|---|---|---|
| 1 | Here you can see your projects | Projects |
| 2 | At the date | Date |
| 3 | Waiting for you | Pending |
| 4 | Deferral request | Pay later |
| 5 | Invoice 1042 · Pay invoice 1042 by June 3 | Invoice 1042 · Due June 3 |
| 6 | Payroll taxes must be paid monthly | Employers pay payroll taxes monthly |
| 7 | Workspace, Team, Org (one object) | Workspace |
| 7 | "Edit Profile Settings" in a sentence-case app | Edit profile settings |
| 8 | Simply drag files here to easily upload them | Drag files here to upload |
| 9 | Submit | Send invoice |
| 9 | OK (deleting a project) | Delete project |
| 10 | Upload failed | Couldn't upload: the file is over 10 MB. Choose a smaller one |
| 10 | Oops! Something went wrong | Couldn't save. Retry, or contact support if it keeps failing |

## Quick pass

Over locale files or rendered text. Hits are candidates: the read keeps "Renew automatically", "just now", "is green", and checks irregular participles ("sent"). Plant a bad string first.

```sh
grep -nEi "here you can|you can now|you are now|this is (the|your)|click here|learn more( about (it|this|that))?[[:space:]]*([^[:alnum:][:space:]]|$)|please|simply|\bjust\b|\beasy\b|easily|\bquick(ly)?\b|seamlessly|successfully|automatically|utili[sz]e|in order to|might want|may want|may be possible|where possible|make sure|be sure|go ahead|feel free|you should|try again later|\b(invalid|illegal|incorrect)\b" strings
grep -nEi "\b(is|are|was|were|been|be|being|get|gets|got|gotten)( (not|now|yet|then|still|[a-z]+ly))* ([a-z]{2,}ed|[a-z]{3,}en)\b" strings
grep -nEi "(^|[\"'>])[[:space:]]*(ok|okay|submit|yes|no|more)[.!?…]?[[:space:]]*([\"'<]|,?$)" strings
perl -CSD -ne 'print "$.: $_" if /\p{Extended_Pictographic}/' labels
```

Then list together and read: statuses (3), headings (4), titles and subtitles (5), nouns and case (7), errors (10).

## Reviewing copy

One finding per string: the file and line, the string quoted, the rule number, and a replacement. If the change touches no user-facing string, say so in one line and stop; don't invent findings.

## Silent failures

- **Visible label edited, accessible name not.** "Save" shown, "Submit form" named: a voice user says "Save" and nothing happens. The name must contain the visible text; [frontend-a11y](../frontend-a11y/SKILL.md) owns the test.

## Verification

1. The quick pass ran after a planted control; each hit is fixed or justified.
2. Each string kind was read as a list against its rule.
3. Edited labels' accessible names were re-checked.

## Cross-references

- **Voice:** [defining-a-voice](../defining-a-voice/SKILL.md). **Marketing:** [writing-marketing-copy](../writing-marketing-copy/SKILL.md).
- [designing-elite-ui](../designing-elite-ui/SKILL.md) 12; [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md) §4; [reviewing-design-work](../reviewing-design-work/SKILL.md) runs this as its copy lens.

## Sources

Why we hold these, rule by rule, with the guides behind each: [references/sources.md](references/sources.md). [Further reading](references/further-reading.md).
