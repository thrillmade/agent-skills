# Sources: making-decision-artifacts

Why [making-decision-artifacts](../SKILL.md) holds what it holds: the research trail for maintainers. Each rule below names the kind of source behind it:

- **House ruling:** the owner's decision on a page they were shown. It binds the orchestrators of the organization that made it, and nothing outside it. Those decisions live in that organization's private records, so none is linked or quoted here; each is stated as the point it made.
- **Incident:** something that went wrong in practice, described by what failed and what the rule prevents.
- **Specification or observation:** an external source with its URL and its true status, or a measurement, labelled with how far it reaches.

Two entries are neither. A **catalog boundary** names the skill that owns a neighbouring question, and a **stated rule** is an instruction not yet backed by practice. Each says which it is.

## The opening paragraph

- Taste calls reach the owner as rendered pictures, light beside dark, after the build, and how they are put is a matter for the working method, not for the design system. House ruling.

## When to use

- A taste call between lawful candidates goes to the owner as pictures. House ruling (as above).
- A default-config choice is still a call and still brought with pictures, but it never blocks a lane, because a config change is cheap to make later. House ruling.
- A landing that moves output is seen by the owner before it merges. Incident: output-moving changes merged automatically before the owner saw what they moved, some ahead of the ruling they depended on.
- A page the owner reads is republished after a sign-in change, or retired once its call is recorded. Incident (see the publishing entry below).

## When NOT to use (the triage)

- A defect or a law question is ruled, recorded as a reversible ruling and reported in one sentence, never asked. House ruling, made after an incident: a defect was put to the owner as a taste choice over two pictures that showed no difference, and the owner could not tell what was being asked.
- A reference page is not a decision and stays when its call is recorded. Incident: a batch of decided pages was deleted, the chosen reference among them, and a deletion cannot be undone.
- An owner's sketch carries an idea, not a layout. House ruling, made after an incident: a drawn grid was copied as a layout when it was pointing at existing conventions.
- A direction not yet built belongs to the cheap-mock stage of [thrill-design](../../thrill-design/SKILL.md) (principle 9); this skill begins once the build emits candidates. Catalog boundary, set so the two skills do not contradict each other.

## The call page

- Rule 1, pictures after the build, from the real emission, never a word before its picture, never a call published without one: house ruling, made after an incident where calls went out as lettered text the owner could not judge.
- Rule 2, one decision per screen with Back and Next: house ruling, made after several questions on one page confused the owner; a follow-up question gets its own screen even when it follows from an earlier answer.
- Rule 3, one scene, large, at one scale: house ruling, made after small, dense comparisons were hard to read; the confirmed shape is each candidate as its own instance of the same scene with one thing changed, cropped to the part that matters. Supporting, advisory and secondhand: Tufte's principle that compared items belong within a single glance, as summarised in a course outline ([UWO lecture notes](https://publish.uwo.ca/~pazner/180/lecture6.html)); not checked against the book, and not the basis of the rule.
- Rule 4, one block per candidate with light beside dark: house ruling; the owner asked for each candidate explained simply, with its two modes next to each other, and not all light followed by all dark.
- Rule 5, exact names: house ruling, made after a paraphrased token name confused the owner. A step on a scale is named, never given as a percentage, because the same step can resolve to different values in each mode; everything on the scene is a token.
- Rule 6, reply words: house ruling, confirming a page layout the owner found easy to use: the recommended choice preselected and quietly marked, one sentence of recommendation, the chosen words collected into one copyable line.
- Rule 7, nothing else: house ruling. Figures live in a file linked once; contact sheets and measurement tables stay with the panel. Status items (a move list, launch steps) never appear on a call page. An item a law or a prior ruling already decides is not a call and is stripped.
- Rule 8, frame within the law: house ruling, made after the owner read an unrequested figure as the page second-guessing a settled law.

## The moves page

- Why it exists: incident, as under "When to use": output-moving merges the owner never saw.
- The page as it now stands (pictures first, then a digest of at most twenty lines, then one ask, with the rows linked once as the panel's reference): house ruling, re-ruling the earlier form after a full table of rows proved too long to read by hand. A class whose law is not recorded says so: house ruling, part of the same re-ruling.
- The configs a person reads, the default and the examples, rendered from the real emission at each tip: house ruling, part of the same re-ruling.
- Since the tip the owner last read, named in the title, and the reading recorded as the moves at that tip being seen: house ruling.
- Printed, not written, by one grammar with fixed columns and order and absence printed as "none": house ruling, made after an incident in which a form written part by part named one fact two ways. The builder checks every count against the data so that no figure on the page is typed.
- A metadata-only landing shown as "nothing a person sees moved": a stated rule, not a measured practice.

## Building, publishing, recording

- One designer lane builds the page: house ruling, made because lanes splitting one surface go down different paths and the seams show. The catalog's owner of the rule is [orchestrating-agent-delegation](../../orchestrating-agent-delegation/SKILL.md); review and QA as separate lanes are owned by [orchestrating-elite-agent-qa](../../orchestrating-elite-agent-qa/SKILL.md). The lane builds from a script that computes every figure, and leaves out a candidate it cannot compute rather than typing one: house ruling, the same one that keeps every figure on a page read from the data.
- The host's page contract: specification, the publishing host's own constraints on a page it wraps; it is the host's document, read when the page is built, so no URL is fixed here. The explicit body and text-container colours come from an incident: a page set its text colour only on `html` under its own wrapper, the host's reset won, and dark mode showed black text.
- The colour-scheme media feature, `prefers-color-scheme`, is defined in [Media Queries Level 5](https://www.w3.org/TR/mediaqueries-5/#prefers-color-scheme), a W3C Working Draft: not a Recommendation, though browsers ship the feature.
- The forced-mode check in Verification rests on a single observation, on one machine set to dark, in headless Chrome 157: an unforced render followed the machine's scheme, so an unforced dark check on a dark machine proves nothing; `--blink-settings=preferredColorScheme=0` forced dark and `=1` forced light. The check was planted both ways on a test page: with text colour only on `html` under a body reset, a paragraph read black in both forced modes (the check fires); with explicit colours on `body` and `p`, it read light in dark and dark in light (silent). Other browsers and versions are not measured.
- Grep every hand-edited sentence after a lane rebuild: incident, in which a lane regenerated the page's prose and hand edits were lost.
- Publish privately from a kept source, and republish after a sign-in change: incident, in which a private page opened only for the account that published it and a publish to the old path was refused under the new account. The link goes on the checkpoint, the note a resuming session reads first, owned by [session-heartbeat](../../session-heartbeat/SKILL.md); where a repository keeps none, the rule is to create it.
- Record the answer as a numbered ruling, with the reply word, the tip it was read at and the link: house ruling. Landing that ruling wherever the old value still stands is owned by [retiring-a-superseded-decision](../../retiring-a-superseded-decision/SKILL.md).

## Anti-patterns

Each is an incident named above, stated by its failure: lettered text options (rule 1), the dense page (rules 2, 3 and 7), a defect asked as taste (the triage), building the sketch (the triage), a paraphrased name (rule 5), hand-written rows (the moves page), black text in dark mode (the page contract), a rebuild that reverts (Verification), a reference deleted as decided (the triage), merging unseen moves (the moves page), and the row table as the reading page (the moves page).
