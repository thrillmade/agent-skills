---
version: "1.0.0"
digest: "4d8e7119bc99"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: ux-copy
description: >-
  Use when writing, editing or reviewing the words inside a product interface —
  buttons, links, field labels, placeholders, headings, status badges, empty
  states, toasts, captions, confirmations and error messages — and when UI copy
  reads padded, wordy, robotic or like AI slop: the screen narrating itself
  ("Here you can see…", "You are now viewing…"), a status written as a sentence
  ("Waiting for you"), a label wrapped in a frame ("At the date", "Your current
  status is"), passive or actorless lines, filler ("simply", "just", "in order
  to", "please note"), a subtitle repeating its title, one thing called by two
  names, "OK" or "Submit" where a specific action exists, an error that blames
  or gives no next step. Also when asked to make interface copy shorter,
  cleaner or more minimal. Not for brand voice and tone (brand-voice-review) or
  documentation (technical-writing).
kind: writing
---

# UX copy

Where a system's own content guide decides, obey it. House calls: [thrill-design](../thrill-design/SKILL.md).

**[source]**: quoted from a guide in Sources. An untagged sentence is this skill's resolution of those sources; an untagged table row is an invented example.

## When to use

- Writing or reviewing any string a user reads in a product.
- Copy called wordy, robotic or "AI slop".

## When NOT to use

- **Voice and tone** — [brand-voice-review](../brand-voice-review/SKILL.md).
- **Testing accessible names** — [frontend-a11y](../frontend-a11y/SKILL.md).
- **Not interface strings** — docs, marketing pages, user-written text, logs.

## The rules

**1. Name it; don't narrate it.** "If you find yourself having to explain how the user interface works, that’s a sign something has gone wrong" [source: GOV.UK]; "Edit out *you can* when it isn't necessary" [source: Microsoft]. Captions too: name the thing, not the process. *Holds when:* no label, heading or caption describes the screen or what the user does.

**2. A label is the noun, not a frame.** "“Favorites” conveys the same message as “Your Favorites”" [source: Apple]; Material prefers "you". So: no possessives in noun labels; action labels and sentences may say "your". *Holds when:* cutting all but the noun phrase loses nothing.

**3. Status is a state word.** "Use a single word… Only use two words if you need to describe a complex state"; "Always describe the tone in the past tense" [source: Polaris]. *Holds when:* each status is one or two words, no pronoun, past tense for a finished action.

**4. Name the user's situation, not the system's category.** "Use words, phrases, and concepts familiar to the user, rather than internal jargon" [source: NN/g h2]; GOV.UK names services by "a task, not a technology". Keep a domain's term of art ("Action items" in a meeting tool). *Holds when:* each heading answers "what is this to me?" and keeps one name everywhere (rule 7).

**5. Say it once.** "Avoid duplicating content, such as adding a page title under the page Title bar" [source: Shopify]. Keep the visible label; placeholders vanish [source: NN/g], so one holds a hint like "name@example.com" [source: Apple]. Exempt: an error naming its field ("Enter an email address" under "Email"); a dialog naming an object nothing else on screen names. *Holds when:* no child string repeats its parent's entity, bar those; every field has a visible label.

**6. Active voice; name the actor.** "Keep it active whenever you can" [source: Microsoft; GOV.UK, Mailchimp agree]; actorless passive is "even harder for readers to understand" [source: NN/g]. Allowed: avoiding "blaming the customer" (Microsoft), stressing the action (Mailchimp), a keyword first (NN/g). *Holds when:* each `be`- or `get`-passive names its actor or meets an exception.

**7. One name per thing.** "Users should not have to wonder whether different words… mean the same thing" [source: NN/g h4]. *Holds when:* listing the nouns in headings, buttons and errors and clustering synonyms leaves one term per cluster.

**8. Cut filler.** "Omit unnecessary adverbs" ("successfully", "automatically"); "use", not "utilize" [source: Microsoft]; "in order to… do not use it" [source: GOV.UK]. On "please": Microsoft allows it for "something inconvenient" or when the product "is to blame"; GOV.UK ("it implies a choice") and Atlassian avoid it. No "Learn more", "Click here" or "More" unless context names the destination: "Learn More" is "a crutch" [source: NN/g]. *Holds when:* the quick pass finds no unexplained hit.

**9. Buttons and links say what they do.** "When labeling buttons and links, it’s almost always best to use a verb"; avoid OK "unless the alert is purely informational" [source: Apple]. Polaris: "View" or "Go" are "often unnecessary", so a navigating control may name its destination; a data-changing one names the change. A radio "No" or status "OK" is not an action. *Holds when:* no button or link reads OK, Submit, Yes or No outside an informational alert; each predicts its result.

**10. Errors: what happened, what to do, no blame.** "Describe what has happened and tell them how to fix it" [source: GOV.UK]. On blame words: GOV.UK's service manual says "Say ‘Wrong password’"; its Design System avoids "valid" and "invalid"; NN/g avoids "invalid, illegal, or incorrect". On "we": Apple avoids it, Atlassian prefers it to "you", Polaris allows it if "Shopify caused the problem". Resolution: the thing is the subject, never the person; "we" only when the product failed; never invent a cause or requirement ("don’t make one up" [source: Atlassian]). Keep a real cause ("Your card was declined") or requirement ("The selected file must be a PNG" [source: GOV.UK], not "Make sure…"). *Holds when:* each error has a next step, or is inline on the field it names ("Wrong password"), and never "you" as the cause.

## Before and after

| | Before | After |
|---|---|---|
| 1 | Here you can see your projects | Projects |
| 1 | you can add apps | add apps (Polaris) |
| 2 | At the date | Date |
| 2 | This is the total cost | Total cost (GOV.UK) |
| 3 | Waiting for you | Pending |
| 3 | refund | refunded (Polaris) |
| 4 | Fee remission | Get help with court fees (GOV.UK) |
| 5 | Invoice 1042 · Pay invoice 1042 by June 3 | Invoice 1042 · Due June 3 |
| 5 | Placeholder "Email" under label "Email" | Placeholder "name@example.com" |
| 6 | Social security taxes must be paid monthly | Employers must pay social security taxes monthly (NN/g) |
| 6 | Your changes have been saved | Saved |
| 7 | Workspace, Team, Org (one object) | Workspace |
| 7 | Delete on the row, Remove in the dialog | Delete |
| 8 | Simply drag files here to easily upload them | Drag files here to upload |
| 8 | Thank you for your application | Application complete (GOV.UK) |
| 9 | Submit | Send invoice |
| 9 | OK (deleting a project) | Delete (Apple) |
| 10 | That password is too short | Choose a password with at least 8 characters (Apple) |
| 10 | Oops! Something went wrong | Couldn't save. Retry, or contact support if it keeps failing |

## Quick pass

Over locale files or rendered text. Hits are candidates ("just now", "is green"); irregular participles ("sent") need a read. Plant a bad string first.

```sh
grep -nEi "here you can|you can now|you are now|this is (the|your)|click here|learn more|please|simply|\bjust\b|easily|seamlessly|successfully|automatically|utili[sz]e|in order to|make sure" strings
grep -nEi "\b(is|are|was|were|been|be|being|get|gets|got|gotten)( (not|now|yet|then|still|[a-z]+ly))* ([a-z]{2,}ed|[a-z]{3,}en)\b" strings
grep -nEi "(^|[\"'>])[[:space:]]*(ok|okay|submit|yes|no|more)[.!?…]?[[:space:]]*([\"'<]|,?$)" strings
```

Then list together: statuses (3), headings (4), titles and subtitles (5), nouns (7), errors (10).

## Silent failures

- **Visible label edited, `aria-label` not**: WCAG 2.5.3 requires that "the name contains the text that is presented visually" [source: W3C]. "Save" shown, "Submit form" named fails: a voice user says "Save" and nothing happens.

## Verification

1. The quick pass ran after a planted control; each hit is fixed or justified.
2. Each string kind read as a list against its rule.
3. Edited labels' accessible names re-checked.

## Cross-references

- [brand-voice-review](../brand-voice-review/SKILL.md), voice; [designing-elite-ui](../designing-elite-ui/SKILL.md) 12; [thrill-design](../thrill-design/SKILL.md) 4.
- [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md) §4; [frontend-a11y](../frontend-a11y/SKILL.md), names.
- [reviewing-design-work](../reviewing-design-work/SKILL.md) runs this as its copy lens.

## Sources

Every quotation, with its page: [references/sources.md](references/sources.md). [Further reading](references/further-reading.md).
