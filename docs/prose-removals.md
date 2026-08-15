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
  fence, a commented-out draft, a row that is missing a cell or whose count is
  not a number — by its own text. So a row parked somewhere unreadable and made
  readable by a later change declares nothing in that change: the line it
  vacated is a removal, and a removal credits you with nothing. Without this
  the rule above was an invariant over what *parses* rather than over this
  file, and every way of writing an unreadable row was somewhere to stage one.
- **The count must cover the cut.** It cannot be written blind, and it puts the
  size of the cut in the diff where a reviewer reads it. It is a floor, not an
  exact match: if a later commit in the same PR adds words back, the row you
  already wrote still stands. Understating still fails.
- **The reason must be filled in.** A row pasted straight from the failure,
  placeholder intact, declares nothing and does not count.
- **A second removal needs a second row**, even from the same skill at the same
  size. Rows are counted, not deduplicated.

Rows go in the table at the bottom of this file — the **first** such table in
it, and only that one, so a fenced example or a commented-out draft elsewhere
in the document declares nothing and does not shadow the real table either. The
record is the point.

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
