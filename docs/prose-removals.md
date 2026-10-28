# Prose removals

Declared deletions of content from a `SKILL.md`. The `check-prose-retention`
gate (`.github/scripts/check_prose_retention.py`) fails any change that takes
words out of a skill and puts nothing back, unless there is a row here.

Deleting prose is allowed and ordinary — skills get trimmed, superseded and
merged. Deleting it *silently* is what this stops. Three skills lost real
content to a link-conversion sweep that needed to fit under the 8192-byte size
gate, and every check went green, because deleting content is how they went
green.

## What the gate charges you for

Reformatting is free. Rewrapping a paragraph, reordering sections, moving a
line, bolding a phrase, converting `` `spacing-system` `` to a markdown link or
back, de-linking a reference that rotted, dropping a bare URL — all score zero.

Each part of the file is scored on its own, and a gain in one never pays for a
loss in another. Padding the `description:` does not buy the deletion of a body
section, and a sentence of filler does not buy the deletion of a worked code
example. Both of those were live evasions: the size cap only measures the body,
and fenced code costs two to three times as many bytes per word as prose, so
each was a way to free real bytes while netting a whole-file word count to zero.

A code example counts as one in either of markdown's spellings — fenced, or
indented four spaces past whatever list item it sits in. Reading only the fence
left that trade open through the other spelling, at *more* bytes per word rather
than fewer.

A block quote is not a third spelling. It is a **container**, and it hid both of
them: a `>` in front of a fenced or an indented example put that example back in
the prose scope, so the same trade went green through a marker — and, the worse
direction, wrapping an existing example in `> ` without touching a word was
charged as a removal whose only printed remedy was a row here declaring words
safe to lose that were never lost. Nothing in this file is ever the right place
for that. Quote depth is now part of a block's identity, at any nesting depth
and with or without the space after the marker.

The floors are measured, not chosen — each sits at the top of its own part's
noise in this repository's history, with the smallest real removal in that part
four times higher or more. `check_prose_retention.py` carries the distribution
and the command to re-measure it.

Splitting a file into its parts is what makes all of that work, so a `SKILL.md`
whose YAML frontmatter cannot be found gets **no verdict at all** rather than
one merged part — the gate says so and fails, the way it does when it cannot
work out what to compare against. Open with a `---` line and close the block
with another.

## How to add a row

Run the gate, or read the CI failure. Either prints the exact row:

```sh
python .github/scripts/check_prose_retention.py
```

With no `--base` it compares against the merge base with `dev`, falling back to
`main` if `dev` is not reachable. Every branch here forks from and targets
`dev`, so that is usually where CI's own merge-base comparison lands too — but
CI always computes its base from the PR's actual target, so if yours is
something else, pass `--base` explicitly rather than trust the default.
Comparing against the tip of a branch instead of its merge base charges yours
for whatever landed there since you forked.

Paste the row below and replace the placeholder with the reason. That is the
whole cost — and the placeholder is rejected unfilled, because deciding the
words are safe to lose is the one part of this that cannot be automated.

The failure is written about the ledger you actually have, so it does not always
hand you a row. Paste one and leave the placeholder in, and the next run asks
you to fill that in rather than reprinting the row you just added. Where this
file already carries a row covering your cut, it says why that row is not yours
to spend instead of offering you a second one to write underneath it.

Six rules make the row a declaration rather than a standing exemption:

- **Only a row your change adds counts.** A row that was already there is
  somebody else's declaration about somebody else's deletion. Inheriting it
  would make this file the blanket exemption the size gate deliberately
  removed. Editing one does not make it yours, and which column you edit — the
  reason, the number, even the skill name, even a column added to this table
  years from now — makes no difference: between two versions of a text file an
  edit is one row removed and one row added, and nothing says which added row
  is which removed one.
- **Nothing already here may be taken back out.** That is what makes the rule
  above true rather than merely intended. Your change is credited with what
  this file gained over what it already had, so a change that removes or
  rewrites anything in it is credited with nothing at all — including its own
  honest rows — until it puts that back. Adding a throwaway row does not buy
  the difference: the row that makes this file longer and the row that covers
  your cut have to be the same row.
- **A line the gate cannot read still takes up a line.** Every line of this
  file occupies a slot: a row by what it declares, and anything else — prose, a
  code block in either of markdown's spellings, a commented-out draft, a row
  that is missing a cell or whose count is not a number — by its own text. So a
  row parked somewhere unreadable and made readable by a later change declares
  nothing in that change: the line it vacated is a removal, and a removal
  credits you with nothing. Without this the rule above was an invariant over
  what *parses* rather than over this file, and every way of writing an
  unreadable row was somewhere to stage one.
- **The count must cover the cut.** It cannot be written blind, and it puts the
  size of the cut in the diff where a reviewer reads it. It is a floor, not an
  exact match: if a later commit in the same PR adds words back, the row you
  already wrote still stands. Understating still fails.
- **The reason must be filled in.** A row pasted straight from the failure,
  placeholder intact, declares nothing and does not count.
- **A second removal needs a second row**, even from the same skill at the same
  size. Rows are counted, not deduplicated.

Rows go in the table at the bottom of this file — the **first** such table in
it, and only that one, so an example elsewhere in the document declares nothing
and does not shadow the real table either. Code counts as an example in either
of markdown's spellings, fenced or indented four spaces, and so does a
commented-out draft. Reading the fence alone was not enough: an indented
example renders identically, its header was the first `| skill | words | why |`
in the document, and the table a reader would actually write into went dead
under it. The record is the point.

Putting an example inside a block quote changes nothing here, and that is
measured rather than assumed: a quoted line begins with `>` and never with a
pipe, so it was never a row or a header either way. The container reading moved
no slot in this file, and moved none in 40,000 generated ledgers built from
quoted rows, quoted fences and quoted indented rows — while the same 40,000 move
21,043 lines in and out of the code scope, which is what says the check looked.

Paste the row anywhere inside that table. A blank line before it is fine; the
table ends at the first line that is neither blank nor a table row, so prose
below it stays prose.

**Rows stay after they merge.** This is a record, not a queue, and the gate
fails on its own if a change takes a merged row back out — with no SKILL.md
involved and nothing else wrong. Correcting a row means adding a new one and
leaving the old one standing.

The gate is characterized against the three real deletions, vendored with their
provenance in
[tests/fixtures/prose-retention/PROVENANCE.md](../tests/fixtures/prose-retention/PROVENANCE.md).

| skill | words | why |
|---|---|---|
| empirical-design-principles | 6 | Its disclaimer said Norman's two gulfs "are in neither skill and are covered nowhere yet". `composing-a-screen` now covers them (#225), so the sentence had become false about its own catalog. Corrected rather than cut — the words went because the claim did, not to make room. |
| finding-a-catalog-skill | 12 | Generated, not authored. The directory publishes a "not here" section listing gaps the catalog does not cover, and its entry for the two gulfs was removed by `gen_skill_directory.py` because #225 filled that gap — the generator refuses to publish a "not here" claim that has become false. The removal is derived from `NOT_HERE_PROBES`; editing this file by hand is what the byte-identity gate forbids. |
| component-sizing-principles | 19 | Consumer audit #252 finding 4: this skill's own "WCAG 2.5.8 target-size floor" section fully restated the floor's value and reasoning that `spacing-system` already owns and cites — two skills asserting the same number is how one of them goes stale. Cut to a pointer at `spacing-system` in the body, `Verification` and `Sources`; the application-specific rung-placement guidance (which rung is reserved, where interactive rungs start) stays, since that half is this skill's own. |
| spacing-system | 55 | Consumer audit #252 finding 5: the border-radius ladder's formula table (`radius-sm = minor`, `radius-xl = 1.5 × major`, `radius-2xl = 2 × major`, ...) had no citation and prescribed a specific ratio as if it were universal, when radius personality — how many rungs, how fast they grow — is a design system's own call, not this skill's to dictate. Replaced with the two endpoints that are genuinely universal regardless of personality (`radius-pill`, `radius-circle`) and a pointer to `udts-spacing-defaults` for one system's worked ladder. |
| designing-elite-ui | 55 | The `## Deploying This Skill` section, addressed to the skill's AUTHOR rather than its reader ("test by retrieval + application… tighten any principle an agent reads but doesn't apply") and paid for on every load. Cut in the #252 restructure. **The gate did not demand this row** — it scores net words across three coarse scopes per file, so the five house sections added in the same change offset the deletion inside the same prose bucket. Logged anyway, because the same PR declared two other cuts and a policy applied only when a gate forces it is not a policy. |
| design-system-consistency | 26 | #256: buying room for rule 6's "filed once" dedup fix on the tightest file in the catalog (3 bytes headroom). The `Sources` section's own "House convention, not a standard" bullet was a compressed restatement of three things already stated in full in the body — `When NOT to use`'s "no system on disk, file one finding" bullet, `Establish the reference before judging` item 2's "filed once — not one finding per hue", and `Every mode needs a token path`'s "is there a path" test — under a heading it explicitly disclaimed belonging in ("not a standard"). Cut as genuine duplication, not trimmed to fit; nothing it said is now unstated elsewhere in the file. |
| token-frugal-tooling | 6 | #202: renaming `## Where to look for detail` to the house's `## Cross-references` (this file's genuine cross-reference list, just under a bespoke name) drops 4 words from the heading itself, and converting `` **`logmind` skill** `` / `` **`clud-bug-collaboration` skill** `` into real relative links (`[logmind](../logmind/SKILL.md)`) drops the now-redundant noun "skill" from each, once the link text already names the skill. No fact or instruction is lost — the two entries still say exactly what each sibling skill covers. |
| clud-bug-collaboration | 61 | House-structure gate: this file had 6 bytes of headroom under the 8192-byte cap and needed 4 new sections (`When to use`, `When NOT to use`, `Verification`, `Sources`), so every existing section was edited for redundancy before anything was added. What actually left rather than merely moved: the "Generic prose ('be careful with database code') gets ignored" framing sentence and its `lib/db/queries.ts` example path (the bad/good snippet right after it still carries the rule); the exact GitHub error string `"Workflow validation failed"` alongside the 401 it's paired with; the per-scope byte-budget preamble ("per run on diff / prior-comment / skill-content") and the `(above any realistic PR diff, below OOM)` aside; "not interactively" in the quiet-mode note; and, in the cost-control fast-paths bullet, the pinned model ID `claude-haiku-4-5-20251001`, the `classify emits model=$MODEL then exit 0` / `is_workflow_only` gating detail, and the quoted Anthropic rationale for Sonnet over Opus. No procedure, threshold or number a reader acts on was cut — the two check-status and check-secret sections were reorganised (one became `Verification`, near-zero net) rather than shortened. |
| orchestrating-agent-delegation | 34 | Local-sync merge of the CEO's October additions (UI is one `designer` lane on opus; verification isolated from file ownership; assign the tree in the brief; repo-global git commands banned), which arrived on a body with 51 bytes of headroom under the 8192-byte cap — so the existing prose was tightened to carry them. What actually left: two Failure-modes bullets that restated rules held elsewhere in the file ("agent reports clean without running the check" — Verification rule 1 and "Trust but verify"; "model wrong for the task" — the tiering table is the rule), the "no registry, no network call" gloss on role discovery, and clause-level trims in the effort/review-pass, stalled-agent, fix-agent and cross-repo-cwd passages. The brief skeleton's "if a classifier or permission blocks something" clause became "if blocked", which the Failure-modes bullet on off-brief agents still states in full. Review caught one rule the first pass dropped silently -- "check you touched the file before attributing a failure" -- restored in compressed form and paid for by cutting the redundant "Split UI drifts:" table-cell prefix (rule 3 states the split rule) and two clause tightenings. No rule is withdrawn in the final state. |
| orchestrating-elite-agent-qa | 60 | Local-sync merge of the CEO's October additions (one `designer` lane builds a UI surface; a branch is not an isolated working tree; a shared-checkout green is not evidence), which arrived on a body with 279 bytes of headroom under the 8192-byte cap, so existing prose was tightened to carry them. What left is clause-level only: "conflicting parallel edits are merge hell", the "visual-polish lens" aside in When NOT to use, "Drive the browser" in a Common Mistakes cell, the "(TDD for skills)" gloss and a clause naming the "verify done" rules in the deploy note, and wording in the Cross-references (`session-heartbeat` entry) and Copyable Prompt. Every gate, rule and cross-reference survives. |
