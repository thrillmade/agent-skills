---
version: "1.0.8"
digest: "696134bd49f7"  # is your copy current? github.com/thrillmade/thrill-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/thrill-skills"
name: making-decision-artifacts
description: |
  Use before putting anything to the owner as a page: a taste call between candidates (how a part looks, a default the owner picks), an output-moving landing whose moves the owner reads before the merge, or a page to republish after a sign-in change. Holds the triage (a defect or a law question is ruled, never asked; a config question never blocks a lane; a reference page is not a decision; the owner's sketch is the idea, not the spec), the call page (one decision per screen, large same-scale candidates rendered from the real build, each a block with light beside dark, the exact token names, the reply words and nothing else), the moves page (since the tip the owner last read: pictures of the parts that moved first, a digest of at most twenty lines, one ask, the rows only linked), and the mechanics: one designer lane builds it, published privately from a kept source, the answer recorded as a ruling. Cite when a page asks for a word before its picture, offers lettered options as text, puts all light then all dark, paraphrases a token name, hand-writes a row, or hands the owner the row table to read.
---

# Making decision artifacts

A decision artifact is the page an orchestrator publishes when a call is the owner's,
not the law's. The owner decides by looking, so every rule here makes the looking
cheap and the answer unambiguous: the **call page** asks one question with pictures;
the **moves page** shows what a landing moved.

## When to use

- A call is taste: two or three lawful candidates differ in how they look or read.
- A default-config choice: bring it with pictures as it arises; it never blocks a lane.
- A landing moves output; the owner sees the moves before it merges.
- A page the owner reads is republished, or retired once its call is recorded.

## When NOT to use

Classify first; most findings are not the owner's call.

- **A defect or a law question** has a right answer by law or measurement: rule it
  yourself, record it as a numbered, reversible ruling, tell the owner in one sentence.
- **A reference page** (a chosen look, a specimen the owner points at) is not a
  decision. It stays when its call is recorded; deleting it is irreversible.
- **A sketch from the owner** carries an idea, not a layout. Ask what it carries before
  building its likeness; the answer may be an audit, not a page.
- **A direction not yet built** belongs to [thrill-design](../thrill-design/SKILL.md)'s
  principle 9 and its cheap mock; this skill is for candidates the build already emits.

## The call page

1. **Pictures, after the build.** Render candidates from the real emission, never a
   mock. Never ask for a word before its picture, nor publish a call without one, even
   as a placeholder.
2. **One decision per screen**, with Back and Next; a follow-up is its own screen.
3. **One scene, large, at one scale.** Each candidate is the same scene with one thing
   changed, cropped to the part under judgment, beside the others in one glance.
4. **One block per candidate:** a one-line name, two or three plain sentences on what
   it is and where it works or fails, then light beside dark. Never all light then all
   dark: the owner compares each candidate's two modes.
5. **Exact names.** A chip under each candidate names the token and its rung in code
   style, never a paraphrase or a percentage (a rung's value can differ by mode).
   Everything on the scene is a token.
6. **The reply words.** Each candidate carries its reply word; the recommended one is
   preselected and quietly marked, with one sentence of recommendation; the chosen
   words collect into one copyable line.
7. **Nothing else.** No status (a move list, launch steps), contact sheets, tables or
   ladders of rows; a number lives on a chip, the panel's figures in a file linked
   once; strip any item a law or ruling decides.
8. **Frame within the law.** Offer no candidate the law refuses and no figure no rule
   asks for; it reads as doubting the law.

## The moves page

A reading page taken in within minutes. The rows are the panel's reference, linked
once, never the page.

- **Since the tip the owner last read**, named in the title; the cumulative page runs
  against the bundle's base.
- **Pictures first.** The configs a person reads (the default and the examples),
  rendered from the real emission at each tip as one scene of the parts whose tokens
  moved, light beside dark per tip, before above after; under each, chips naming the
  moved tokens and their values.
- **A digest of at most twenty lines**, one per class of move, each with its count
  across the store, the law it follows in a few words and one example; the counts sum
  to the comparison's summary and the page prints that check. A class whose law is not
  recorded says so.
- **One ask:** reply `seen`, or name the picture and the part that looks wrong.
- **Printed, not written.** One grammar over the comparison data writes the rows file
  (fixed columns and order, absence printed "none"; every figure move at or above the
  unit shown, with its ground before and after); the builder refuses when a count
  differs from the data's and prints its generation line.
- **A metadata-only landing is still shown** as "nothing a person sees moved" with its
  counts. Silence reads as unchecked.

## Building, publishing, recording

- **One designer lane on opus builds the page**, every screen, both themes, from a
  script that computes every figure; a candidate it cannot compute is left out.
- **The host's page contract:** no doctype, `html`, `head` or `body` tags (the host
  wraps it); a `<title>` first, of two to four words; colors as prefixed tokens on
  `:root`, dark under `prefers-color-scheme` with a `data-theme` override;
  explicit background and color on `body` and color on text containers; 400 px with a
  16 px gutter and no sideways scroll; no external resources beyond the font CDN.
- **Publish privately from a source kept in the scratchpad**; link it from the
  checkpoint, creating one where the repository keeps none. A private page opens
  only for its publishing account: after a sign-in change, republish each source as a
  new artifact and re-link.
- **Record the answer as a numbered ruling**: the reply word quoted, the tip it was
  read at, the link. A moves page's reading is "the moves at `<sha>` are seen"; the
  next moves page runs from that tip.

## Anti-patterns

- **Lettered text options:** looks offered as words; nothing to judge.
- **The dense page:** sheets, tables, several questions or prose on one page; nothing
  compares.
- **A defect asked as taste:** a value lost on dark grounds put as a choice over
  identical pictures; the owner cannot see the question and the defect waits.
- **Building the sketch:** a drawn grid copied as a layout; it carried a convention, so
  the build answered the wrong question.
- **A paraphrased name:** a description for a token, a percentage for a rung; the reply
  maps to no code.
- **Hand-written rows:** a form written part by part named one fact two ways.
- **Black text in dark mode:** color only on `html`; the host's reset turned the text
  black.
- **A rebuild that reverts:** the prose regenerated, hand edits lost.
- **A reference deleted as decided:** the chosen look, gone with decided pages; later
  calls lose their anchor for good.
- **Merging unseen moves:** merges the owner never saw, some ahead of their ruling; a
  move they would refuse ships first.
- **The row table as the reading page:** too long to read by hand.

## Verification

Before publishing, every line holds:

- [ ] The call is taste; no item on the page is one a law or ruling decides.
- [ ] Every picture is from the real build at a named tip; no figure is typed.
- [ ] One decision per screen; each candidate a block, light beside dark, one scale.
- [ ] Every candidate has an exact token name and a reply word; one is preselected.
- [ ] Moves page: pictures from the real build at both tips, a digest of at most
      twenty lines whose counts sum to the data's, one ask; the rows linked, not shown.
- [ ] Each mode forced (headless Chrome `--blink-settings=preferredColorScheme=0` is
      dark, `=1` light; unforced follows the machine): a paragraph's computed color
      differs between them and is light in dark.
- [ ] After a lane rebuild, every hand-edited sentence is grepped in the page.
- [ ] The source is kept; once published, its link is recorded on the checkpoint.

## Cross-references

- [orchestrating-a-multi-agent-run](../orchestrating-a-multi-agent-run/SKILL.md): the
  family's entry.
- [orchestrating-agent-delegation](../orchestrating-agent-delegation/SKILL.md): the
  one-designer rule and the lane's brief.
- [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md): review
  and QA as separate lanes that check, never shape.
- [designing-elite-ui](../designing-elite-ui/SKILL.md): the bar the page is built to.
- [thrill-design](../thrill-design/SKILL.md): "decide, then ship".
- [session-heartbeat](../session-heartbeat/SKILL.md): owns the checkpoint.
- [retiring-a-superseded-decision](../retiring-a-superseded-decision/SKILL.md): landing
  the ruling wherever the old value still stands.

## Sources

Why each rule holds, and the ruling or incident behind it: [sources](references/sources.md).
