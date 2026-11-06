---
version: "1.0.5"
digest: "df971df563bd"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: making-decision-artifacts
description: |
  Use before putting anything to the owner as a page: a taste call between candidates (how a part looks, a default the owner picks), an output-moving landing whose moves the owner reads before the merge, or a page to republish after a sign-in change. Holds the triage (a defect or a law question is ruled, never asked; a config question never blocks a lane; a reference page is not a decision; the owner's sketch is the idea, not the spec), the call page (one decision per screen, large same-scale candidates rendered from the real build, each a block with light beside dark, the exact token names, the reply words and nothing else), the moves page (every move since the tip the owner last read, printed from the comparison data by one grammar), and the mechanics: one designer lane builds it, published privately from a kept source, the answer recorded as a ruling. Cite when a page asks for a word before its picture, offers lettered options as text, puts all light then all dark, paraphrases a token name, or hand-writes a row.
---

# Making decision artifacts

A decision artifact is the page an orchestrator publishes when a call belongs to the
owner and not to the law. The owner decides by looking, so every rule here makes the
looking cheap and the answer unambiguous: the **call page** asks one question with
pictures; the **moves page** shows what a landing moved.

## When to use

- A call is taste: two or three lawful candidates differ in how they look or read.
- A default-config choice: bring it with pictures as it arises; it never blocks a lane.
- A landing moves output; the owner sees the moves before it merges.
- A page the owner reads is republished, or retired once its call is recorded.

## When NOT to use

Classify first; most findings are not the owner's call.

- **A defect or a law question.** It has a right answer by law or measurement: rule it
  yourself, record it as a numbered, reversible ruling, tell the owner in one sentence.
- **A reference page** (a chosen look, a specimen the owner points at) is not a
  decision. It stays when its call is recorded; deleting it is irreversible.
- **A sketch from the owner** carries an idea, not a layout. Ask what it carries before
  building its likeness; the answer may be an audit, not a page.

## The call page

1. **Pictures, after the build.** Render candidates from the real emission, never a
   mock. Never ask for a word before its picture exists, and never publish a call
   without one, even as a placeholder.
2. **One decision per screen**, with Back and Next; a follow-up question is its own
   screen.
3. **One scene, large, at one scale.** Each candidate is the same scene with one thing
   changed, cropped to the part under judgment, beside the others in one glance.
4. **One block per candidate:** a one-line name, two or three plain sentences on what
   it is and where it works or fails, then light beside dark. Never all light then all
   dark: the owner compares a candidate's two modes against each other.
5. **Exact names.** A chip under each candidate names the token and its rung in code
   style, never a paraphrase or a percentage (a rung's value can differ by mode).
   Everything on the scene is a token.
6. **The reply words.** Each candidate carries its reply word; the recommended one is
   preselected and quietly marked, with one sentence of recommendation; the chosen
   words collect into one copyable line.
7. **Nothing else.** No contact sheets, tables or ladders of rows; a number lives on a
   chip, the panel's figures in a file linked once; strip what a law decides.
8. **Frame within the law.** Offer no candidate the law refuses and no figure no rule
   asks for (a hover step owes visibility, not contrast); it reads as doubting the law.

## The moves page

A reading page a person takes in within minutes: pictures, then a digest, then one
ask. The rows are the panel's reference, linked once, never the page.

- **Since the tip the owner last read**, named in the title; the cumulative page runs
  against the bundle's base.
- **Pictures first.** The configs a person reads, rendered from the real emission at
  each tip as one scene of the parts whose tokens moved, light beside dark per tip,
  before above after; under each, chips naming the moved tokens and their values.
- **A digest of at most twenty lines**, one per class of move, each with its count
  across the store, the law it follows in a few words and one example; the counts sum
  to the comparison's summary and the page prints that check. A class whose law is not
  recorded says so.
- **One ask:** reply `seen`, or name the picture and the part that looks wrong.
- **Printed, not written.** One grammar over the comparison data writes the rows file
  (every figure move at or above the unit shown, with its ground before and after); the
  builder refuses when a count differs from the data's and prints its generation line.
- **A metadata-only landing is still shown** as "nothing a person sees moved" with its
  counts. Silence reads as unchecked.

## Building, publishing, recording

- **One designer lane on opus builds the page**, every screen, both themes, from a
  script that computes every figure; a candidate it cannot compute is left out.
  Review and QA are separate lanes; they check, they do not shape.
- **The host's page contract:** no doctype, `html`, `head` or `body` tags (the host
  wraps it); a `<title>` first, a name of two to four words; colors as prefixed
  tokens on `:root`, dark under `prefers-color-scheme` with a `data-theme` override;
  explicit background and color on `body` and color on text containers; 400 px with a
  16 px gutter and no sideways scroll; no external resources beyond the font CDN.
- **Publish privately from a source kept in the scratchpad**; link it from the pause
  pointer. A private page opens only for its publishing account: after a sign-in
  change, republish each source as a new artifact and re-link.
- **Record the answer as a numbered ruling**: the reply word quoted, the tip it was
  read at, the link. A moves page's reading is "the moves at `<sha>` are seen"; the
  next moves page runs from that tip.

## Anti-patterns

- **Lettered text options:** eight glass calls as text, "no visuals or anything"
  (10 Oct 2026).
- **The dense page:** contact sheets and tables, "hard to compare" (12 Oct); five
  questions on one page, "very confusing" (22 Oct); calls as prose (29 Oct).
- **A defect asked as taste:** a value vanishing on dark grounds asked as "ring old or
  new" over two identical pictures; a word asked before its picture (18 Oct).
- **Building the sketch:** a drawn state grid meant "follow the conventions"; a grid
  page was "not what I'm saying" (18 Oct).
- **A paraphrased name:** "the neutral palette's base surface" for
  `neutral-grey-surface-base` (10 Oct); a percentage for a rung (12 Oct).
- **Hand-written rows:** a form written part by part named one fact two ways
  (16 Oct).
- **Black text in dark mode:** color set only on `html` under the page's own wrapper,
  so the host's reset turned body text black (10 Oct).
- **A rebuild that reverts:** the prose regenerated, hand edits lost (17 Oct).
- **A reference deleted as decided:** the chosen look, among 26 pages (10 Oct).
- **Merging unseen moves:** fourteen output-moving merges seconds after their
  comparison, two before their ruling (11 Oct).
- **The row table as the reading page:** 807 rows over three configs, "massive, i
  cant really go through this manually" (6 Nov). The owner looks; the panel reads.

## Verification

Before publishing, every line holds:

- [ ] The call is taste; nothing on the page is decided by a law or a ruling.
- [ ] Every picture is from the real build at a named tip; no figure is typed.
- [ ] One decision per screen; each candidate a block, light beside dark, one scale.
- [ ] Every candidate has an exact token name and a reply word; one is preselected.
- [ ] Moves page: pictures from the real build at both tips, a digest under twenty
      lines whose counts sum to the data's, one ask; the rows linked, not shown.
- [ ] Each mode forced (headless Chrome `--blink-settings=preferredColorScheme=0` is
      dark, `=1` light; unforced follows the machine): a paragraph's computed color
      differs between them and is light in dark.
- [ ] After a lane rebuild, every hand-edited sentence is grepped in the page.
- [ ] The source is kept and the link is on the pause pointer.

## Cross-references

- [orchestrating-a-multi-agent-run](../orchestrating-a-multi-agent-run/SKILL.md): the
  family's entry; this page is how a decision that is the owner's reaches them.
- [orchestrating-agent-delegation](../orchestrating-agent-delegation/SKILL.md): the
  one-designer rule and the brief for the page's lane.
- [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md): the lanes
  that check the page without shaping it.
- [designing-elite-ui](../designing-elite-ui/SKILL.md): the bar the page is built to.
- [thrill-design](../thrill-design/SKILL.md): "decide, then ship"; this is how the
  options reach the decider.

## Sources

Why each rule holds, and the ruling or incident behind it: [sources](references/sources.md).
