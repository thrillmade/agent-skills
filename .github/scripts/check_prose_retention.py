#!/usr/bin/env python3
"""Fail a change that removes prose from a SKILL.md without saying so.

Called by `.github/workflows/check-prose-retention.yml` on PR + push to main.

WHY THIS EXISTS
---------------
`validate_skills.py` enforces a hard 8192-byte cap on every SKILL.md body,
in CI, with no exception path. A catalog-wide sweep that converted backticked
skill names into markdown links (#197) pushed three files past that cap, and
in all three the converting agent made room by deleting prose:

  web-interface-guidelines-review  lost Verification rule 5, requiring a
                                   review's findings to cite the skills they
                                   rest on
  clud-bug-collaboration           lost its entire `CLUD_BUG_QUIET=1` agent
                                   invocation section
  session-heartbeat                lost the two lines establishing that it is
                                   the *mechanism* and unattended-operation
                                   the *policy* layered on it

Every existing check went green, because deleting content is *how* they went
green. The size gate cannot catch it -- shrinking is what it asks for.
check-doc-links cannot -- it only proves links resolve. One of the three
deletions was justified in its own commit by the claim that check-doc-links
"enforces it mechanically"; it does not, and after the deletion the rule was
enforced nowhere. The sharpest case indicts the whole exercise: a conversion
whose purpose was strengthening cross-skill routing deleted a cross-skill
routing statement to fit.

WHAT IT DISTINGUISHES
---------------------
Reformatting is free; losing content is not.

  free      rewrapping a paragraph, reordering sections, moving a line,
            bolding a phrase, turning `spacing-system` into
            [spacing-system](../spacing-system/SKILL.md), or turning it back
  declared  words that were saying something are gone and nothing in the same
            part of the file replaced them -- legitimate and common (skills
            get trimmed, superseded, merged), but it has to be on purpose and
            on the record

Three moves make that separable, and all three are load-bearing:

1. NORMALISE LINKS FIRST. `[x](../x/SKILL.md)` tokenises to four words where
   `` `x` `` tokenises to one, so an un-normalised comparison reads the #197
   sweep as a large word *gain*. Measured on the real commit: with
   normalisation web-interface-guidelines-review scores a net loss of 13
   words; without it, a net gain of 41. The gate would have gone green on the
   file that lost the routing rule.

   Every inline link collapses to its text, not only links to a SKILL.md, and
   bare URLs drop out of the stream entirely. A URL is an address, not prose.
   Scoped to SKILL.md links alone, this gate charged 3 to 8 invented "words"
   for de-linking any of the 37 external links in this catalog even when the
   sentence around them kept every word -- punishing exactly the link
   maintenance `check-doc-links` exists to prompt.

2. COMPARE MULTISETS, NOT SEQUENCES. A line-level or sequence diff reports a
   moved paragraph as a deletion here plus an insertion there. Counting words
   makes any pure move, rewrap or reorder score zero by construction, so the
   gate has nothing to say about formatting.

3. SCORE EACH PART OF THE FILE SEPARATELY. Words arriving in one part never
   pay for words leaving another. Without this the gate is trivially evaded,
   because the pressure that causes the defect does not price every byte the
   same:

     - `validate_skills.py` measures `content[m.end():]` -- the body only. The
       frontmatter is outside the cap, so 46 words of padding in the
       `description:` bought the deletion of the entire CLUD_BUG_QUIET section
       at zero cost against the constraint that caused the defect. Reproduced:
       whole-file scoring netted that to -2 and passed it.
     - Fenced code runs 6 to 13 bytes per word against prose's 4.6, so
       deleting a worked example and adding a same-length sentence of filler
       frees real bytes and nets to zero. Reproduced on test-discipline, the
       tightest file in the catalog: 139 bytes freed, gate green, the skill's
       worked anti-pattern example gone. Markdown spells a code block two ways
       and reading only the fence left the other one wide open: an indented
       example scored as prose, so the same trade went green through the
       spelling that costs MORE bytes per word, not fewer. Both are read --
       see `Container`. A block quote then suppressed both spellings at once,
       which is a CONTAINER rather than a third spelling, so containers are
       modelled too -- see `Code`.

   Both are one defect -- a gain somewhere cheap paying for a loss somewhere
   expensive -- so both get one fix rather than a patch each.

   The split has to be findable for any of that to hold, so a file whose
   frontmatter cannot be located gets NO VERDICT rather than one merged scope.
   Merging is not the conservative default: it IS the first evasion. And the
   file that reaches it is not hypothetical -- `validate_skills.py` reads
   through `Path.read_text`, whose universal newline translation hides CRLF
   from its frontmatter regex, while this gate decodes the git blob. A CRLF
   SKILL.md therefore passed that gate and defeated this split. Line endings
   are normalised here so it does not, and the refusal stands behind that for
   whatever the next spelling turns out to be.

Stdlib only.

Inputs (main): a base and a head git revision, plus the repo at cwd.
Outputs (stdout): one `::error file=<path>::<msg>` GitHub annotation per
undeclared removal, per file that could not be read or scoped, and one against
the ledger if the change took a merged row out of it -- then a guidance block.

Exit codes:
  0  no undeclared prose removal
  1  undeclared prose removal, a merged ledger row withdrawn, or the comparison
     could not be made
"""

from __future__ import annotations

import argparse
import collections
import difflib
import re
import subprocess
import sys
import textwrap
from pathlib import Path

SKILL_GLOB_RE = re.compile(r"^skills/[^/]+/SKILL\.md$")

# Every inline markdown link and image collapses to its link text:
# `[text](url)`, `[text](url "title")`, `![alt](url)`. Deliberately NOT
# restricted to links ending in SKILL.md -- see move 1 in the module docstring.
# The target class excludes `)`, so it stops at the first one and a trailing
# title comes along for free.
LINK_RE = re.compile(r"!?\[([^\]\n]*)\]\([^)\n]*\)")

# An address is not prose. Autolinks and bare URLs leave the word stream
# entirely, so adding, removing or repointing one is free in both directions.
URL_RE = re.compile(r"<https?://[^>\s]+>|\bhttps?://\S+")

# A word is alphanumerics plus internal apostrophes/hyphens, so `apca-contrast`
# is one token and `don't` is one token. Everything else -- backticks,
# asterisks, pipes, list bullets, heading hashes -- is separator, which is what
# makes bold/italic/code-span formatting changes free.
WORD_RE = re.compile(r"[A-Za-z0-9_]+(?:['’-][A-Za-z0-9_]+)*")

# `validate_skills.py`'s own frontmatter boundary, character for character --
# see split_scopes. Applied to text with its line endings normalised, which
# that gate gets for free from `Path.read_text` and this one does not.
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

# A byte-order mark is not content. Left in place it sits before the opening
# `---` and the frontmatter stops being locatable.
BOM = "﻿"

# ```lang or ~~~ , indented or not, with whatever follows the run of fence
# characters captured separately -- a closing fence carries nothing but the
# fence.
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")

# A list item's marker, with the indent before it and the run of spaces after it
# captured -- together they give the column the item's CONTENT starts in, which
# is where the four spaces of an indented code block are measured from. At least
# one space is required after the marker, or the marker ends the line: `-foo` is
# a paragraph, not a list. `\d{1,9}` is CommonMark's own bound on an ordered
# marker, so a bare year at the start of a line is not one.
LIST_ITEM_RE = re.compile(r"^( *)([-*+]|\d{1,9}[.)])( +|$)")

# A block quote's marker: CommonMark's up-to-three spaces of indent, the `>`,
# and ONE optional space that belongs to the marker rather than to the content.
# Both bounds carry a rule that would otherwise need writing out:
#
#   `{0,3}` is why four spaces before a `>` is a code block and not a quote --
#   an over-indented `>` inside an indented example is content, and no separate
#   rule says so.
#
#   the single trailing space is why `>     x` leaves four spaces and opens an
#   indented block INSIDE the quote, while `>```` leaves the run itself and
#   opens a fence. The no-space spelling is not a special case; it is what
#   happens when there is no space to eat.
QUOTE_RE = re.compile(r"^ {0,3}> ?")

# CommonMark's indent for a code block, and its tab stop. Tabs are expanded
# before the indent is measured: a tab-indented block is the same block, and
# leaving it unmeasured would be the same hole in a third spelling.
CODE_INDENT = TAB_STOP = 4

# The three parts of a SKILL.md, scored separately and never netted against
# each other.
SCOPES = ("frontmatter", "prose", "code")

SCOPE_LABEL = {
    "frontmatter": "frontmatter",
    "prose": "prose",
    "code": "code examples",
}

# Net words each part may lose without a ledger row.
#
# MEASURED, not chosen -- and measured PER SCOPE, because each part has its own
# word economy and therefore its own noise floor. Replaying this detector over
# every revision of every SKILL.md reachable from ANY ref -- `--all`, the scope
# in the command below, because the three #197 deletions live on the topic
# branch PROVENANCE.md records rather than on a trunk -- gives, per scope, these
# loss values and nothing in between:
#
#   prose        1, 2   ... then 13, 44, 49, 79, 283, 323, 408, 1364
#                       nothing in 3..12 -- the band is empty
#   frontmatter  2, 3   ... then 12
#                       nothing in 4..11
#   code         3      ... then 59, 73, 192, 197
#                       nothing in 4..58
#
# Each floor sits at the top of its scope's noise and below the smallest real
# removal in it, with 4x margin or better in every case. The noise is
# mechanical and identifiable: the 2s are one sweep dropping the retired
# `review_mode:` key across the catalog, and the code 3s are a one-line JSON
# snippet replaced by the command that superseded it. Everything above each
# floor is a genuine content removal -- including one that whole-file scoring
# masked behind body additions: a 12-word cut to semver-design-tokens'
# `description:` that deleted its "cite when an agent classifies a pre-1.0
# rename as major" trigger outright.
#
# Re-run the replay before moving any of these -- and after any change to the
# SPLIT, because the split is what puts a loss in a scope and every band above
# is a property of one scope. Teaching it markdown's second spelling of a code
# block was such a change: re-derived over `--all` afterwards the three bands
# come back identical, and the control that says the replay would have noticed
# is a naive four-spaces-is-code rule, under which prose's largest real removal
# drops 408 -> 302 and code's smallest rises 59 -> 165.
#
# The argument is the empty band, not the digit -- and not the tally either.
# How many file-revisions the replay
# compares, and how many of them fire, is a function of which refs a given
# checkout happens to have: measured at 19 fires over 170 file-revisions from
# `--all` and 7 over 99 from `origin/dev`, same detector, same run. A checkout
# with two more branch tips in it gave 172 for the same 19. The bands are what
# reproduce, so those are what is quoted:
#
#   git log --all --format=%H -- 'skills/*/SKILL.md'   # then diff each parent
#
# Three words is also about the shortest span that can carry a claim in prose;
# in frontmatter and in code, three tokens is still routinely one retired key
# or one deleted call.
FLOOR = {
    "prose": 2,
    "frontmatter": 3,
    "code": 3,
}

LEDGER = Path("docs/prose-removals.md")


def normalise(text: str) -> str:
    """Strip the formatting that carries no prose. See move 1 above."""
    return URL_RE.sub(" ", LINK_RE.sub(lambda m: m.group(1), text))


def words(text: str) -> list[str]:
    """The word stream a fragment reduces to, links and URLs normalised."""
    return WORD_RE.findall(normalise(text))


def unwrap(text: str) -> str:
    """One spelling of a line break and no byte-order mark.

    This gate decodes the git blob itself, so it sees the bytes that are in the
    tree. `validate_skills.py` reads through `Path.read_text`, whose universal
    newline translation turns CRLF into LF before its frontmatter regex ever
    runs. A CRLF SKILL.md therefore satisfies that gate and arrived here with a
    frontmatter block this one could not find -- and an unfound frontmatter
    used to mean one merged scope, which is the exact configuration in which
    padding a `description:` pays for a deleted body section. Reproduced on all
    three of the historical cases: every one of them goes green.
    """
    return text.lstrip(BOM).replace("\r\n", "\n").replace("\r", "\n")


def lines_of(text: str) -> list[str]:
    """The file's lines, one per line break, with no phantom last line.

    Deliberately not `splitlines()`, which also breaks on form feed, vertical
    tab and U+2028 -- none of which git, markdown or a diff treats as a line.
    """
    out = unwrap(text).split("\n")
    if out and out[-1] == "":
        out.pop()
    return out


class Fence:
    """Fenced-code state, one line at a time, honouring the fence's LENGTH.

    CommonMark: a run of N backticks or tildes opens a block, and only a run of
    the same character, at least N long, carrying nothing else, closes it.
    Normalising every fence to three characters -- as this did -- let a ``` line
    *inside* a ```` block close it. Everything below that line then changed
    scope, in a SKILL.md and in the ledger both, without anybody editing it:
    the same shape as the acceptance flips the ledger's slot accounting exists
    to stop, reached through the fence instead.
    """

    def __init__(self) -> None:
        self._open: tuple[str, int] | None = None

    @property
    def open(self) -> bool:
        """Whether a fenced block is currently open.

        `Container` has to know before it feeds a line, because a fence outranks
        an indented block in both directions: an indented block cannot open
        inside a fence, and a fence cannot open inside an indented block -- a
        ``` line indented into a code block is content, and feeding it here
        would open a block that swallows the rest of the file. `Code` reads it
        through `Container.fenced` for the same reason one step out: a `>` on a
        line inside a fence is content too.
        """
        return self._open is not None

    def feed(self, line: str) -> bool:
        """Advance one line. True if the line is part of a fenced block, the
        opening and closing fences included.
        """
        m = FENCE_RE.match(line)
        if self._open is None:
            if m:
                self._open = (m.group(1)[0], len(m.group(1)))
                return True
            return False
        char, length = self._open
        if (
            m
            and m.group(1)[0] == char
            and len(m.group(1)) >= length
            and not m.group(2).strip()
        ):
            self._open = None
        return True


class Container:
    """Code-block state inside ONE container, for BOTH of markdown's spellings.

    A container is the document itself, or one block quote inside it. `Code`
    owns one of these per quote depth and hands each line to the one it belongs
    to; everything below is about a single container and measures from ITS left
    margin, which is what makes that ownership the only thing quote depth has
    to change.

    `Fence` reads one spelling. The other is the four-space indented block, and
    reading only fences left it open in two places at once -- one root cause,
    both reproduced:

      IN A SKILL.md it scored as prose, so deleting an indented worked example
      and adding a same-length sentence of filler netted to zero and the gate
      went green. That is the byte arbitrage move 3 exists to stop, reached
      through the spelling this gate did not read -- and the incentive was
      intact rather than reduced, because an indented block costs MORE bytes per
      word than a fence, not fewer.

      IN THE LEDGER it read as a live table. An indented example row is the
      first `| skill | words | why |` in the document, so the parser latched
      onto the example and the real table below it was dead: a row added exactly
      where that file instructs declared nothing, and the failure reprinted the
      row the author had just written. An escape hatch that cannot be opened is
      a bypass with extra steps, which this module names twice as its own reason
      for existing.

    Two CommonMark rules keep this off ordinary prose, and a rule that read
    four spaces as code without them would rescope real content:

      AN INDENTED BLOCK CANNOT INTERRUPT A PARAGRAPH -- it opens only after a
      blank line.

      THE FOUR SPACES ARE MEASURED FROM THE ENCLOSING LIST ITEM'S CONTENT
      COLUMN, not from the left margin, so a nested bullet's continuation is
      that bullet's prose however deep it sits.

    Measured before this was written: 41 lines across this catalog's SKILL.md
    files are indented four or more spaces outside a fence. 38 are inside a
    frontmatter block, which is its own scope and never reaches the prose/code
    split; the other 3 are wrapped continuations of a nested bullet in
    reviewing-design-work, and EITHER rule alone keeps all 3 prose -- measured
    by dropping each in turn, which rescopes nothing, and both together, which
    rescopes that one file. So this reclassification moves nothing that ships.

    Even where it did move something it could not cost a false positive on an
    unchanged file: base and head are split by the same rules, so a line nobody
    edited lands in the same scope on both sides and nets to zero there.
    """

    def __init__(self) -> None:
        self._fence = Fence()
        self._lists: list[int] = []
        self._indented = False
        self._after_blank = True

    @property
    def fenced(self) -> bool:
        """Whether a fenced block is open here.

        `Code` asks before it peels a block-quote marker. Everything inside a
        fenced block is literal, so a `>` on a line inside one is the author's
        own text -- a quoted markdown example -- and not a container.
        """
        return self._fence.open

    @property
    def paragraph(self) -> bool:
        """Whether a paragraph is open here -- the one block that can be LAZILY
        continued.

        CommonMark ends a block quote at the first line carrying no marker,
        with one exception: a line that would not start a block of its own
        continues the quote's open paragraph instead, marker or no marker.
        `Code` asks the container that is ending, because the answer decides
        what the next line may open in the container underneath it.
        """
        return not self._after_blank and not self._indented and not self._fence.open

    def reopen(self, lazy: bool) -> None:
        """A child container just ended. Take up where this one left off.

        The INDENTED block goes unconditionally. Whatever was open here, the
        `>` that opened the child sat at this container's own margin, and a
        marker at the margin is a block start: it closed the block under it.

        Whether a new block may OPEN on the next line is the lazy-continuation
        question, and it is why `lazy` is passed in rather than assumed. A quote
        whose last block was a fence or a list leaves nothing to continue, so
        the line after it starts a block and four spaces there are a code
        block. A quote whose last block was a PARAGRAPH is continued by that
        line instead, and the same four spaces are the paragraph's own wrapped
        text. Assuming either way costs a real disagreement with CommonMark:
        measured over 20,000 generated documents, always reopening scores 3467
        disagreements and never reopening 3485, against 2755 for asking.

        The LIST nesting stays either way, because a list item that contained a
        quote still contains the lines after it, and its content column is the
        only thing keeping their continuations out of the code scope -- dropping
        it would rescope a nested bullet's own paragraph the moment somebody
        quoted something above it, which is the false positive the second
        CommonMark rule above exists to stop.
        """
        self._indented = False
        if not lazy:
            self._after_blank = True

    def _threshold(self) -> int:
        """The column at which an indented code block starts here -- four past
        the innermost open list item's content, or four past the margin."""
        return (self._lists[-1] if self._lists else 0) + CODE_INDENT

    def feed(self, line: str) -> bool:
        """Advance one line. True if the line is part of a code block of either
        spelling, the opening and closing fences included.

        The line arrives with its tabs already expanded and its block-quote
        markers already peeled off by `Code`, so every column measured below is
        a column inside THIS container.
        """
        if self._fence.open:
            self._fence.feed(line)
            # A closing fence ends a block rather than a paragraph, so the line
            # after it may open an indented one without a blank line between.
            self._after_blank = not self._fence.open
            return True

        if not line.strip():
            # A gap ends nothing. An indented block survives a blank line
            # between its chunks, and a list item survives one between its
            # paragraphs -- but a blank line is what lets the NEXT one open a
            # block, which is the first rule above.
            self._after_blank = True
            return self._indented

        indent = len(line) - len(line.lstrip(" "))

        if self._indented and indent >= self._threshold():
            self._after_blank = False
            return True
        self._indented = False

        # A line shallower than an open item's content column is outside it.
        while self._lists and indent < self._lists[-1]:
            self._lists.pop()

        opens_block = self._after_blank and indent >= self._threshold()
        self._after_blank = False
        if opens_block:
            self._indented = True
            return True

        if self._fence.feed(line):
            return True

        m = LIST_ITEM_RE.match(line)
        if m:
            gap = len(m.group(3))
            # More than four spaces after the marker is an indented block INSIDE
            # the item rather than a wider marker, so the content starts one
            # column on. So does an item with nothing on its opening line.
            self._lists.append(
                len(m.group(1))
                + len(m.group(2))
                + (gap if 1 <= gap <= CODE_INDENT else 1)
            )
        return False


class Code:
    """Code-block state across markdown's CONTAINERS, one line at a time.

    `Container` reads both spellings of a code block. This decides WHICH
    container a line belongs to first, because a block quote is not a third
    spelling -- it is a container that suppressed both of the other two at once:

        > ```
        > the worked example
        > ```

    `Container` allows only whitespace before a fence and measures every indent
    from its own left margin, so a `>` in front hid the fenced spelling and the
    indented one together. It shipped in 4 of this catalog's 49 skills, and both
    failure directions fired on real files:

      GREEN ON A REAL CUT. Deleting test-discipline's closing 41-word paragraph
      and putting a block-quoted worked example in its place scored the example
      as prose, the two netted, and the gate passed the cut it exists to catch.
      Byte for byte the same example spelled as a plain fence fires. That is
      move 3's byte arbitrage reached through a container instead of through a
      spelling, and a SMALLER quoted block than the cut did not even go red --
      it went quiet, understating a 41-word removal as 8 and letting a row
      declaring 8 cover it.

      RED ON A LAYOUT-ONLY CHANGE. Wrapping api-contract-enforcement's existing
      fenced example in `> ` and changing nothing else -- 1020 words either
      side, the same word stream -- moved 15 of them from one scope to the
      other, and the only remedy the failure could print was a ledger row
      declaring 15 words safe to lose when none were lost. Following the printed
      instruction meant writing a false entry into a permanent append-only
      record: an escape hatch that cannot be opened HONESTLY is a bypass with
      extra steps, which this module names twice as its own reason for existing.

    So the container is modelled rather than the marker matched. Quote depth is
    part of a block's identity: each depth owns its own `Container`, the markers
    are peeled off a line before any block rule reads it, and the containers
    deeper than the line's depth are DELETED rather than left dormant. A fence
    opened inside a quote cannot extend past it and one opened outside cannot
    reach in -- not because either is checked for, but because at the other
    depth that state is not reachable at all. Nothing else in this class reads
    `self._containers` at any index but the line's own.

    Two rules fall out of that rather than being added to it:

      A FENCE OUTRANKS A MARKER. While one is open here nothing is peeled, so a
      markdown example quoting `> ` inside a fence stays what the author typed
      -- the same precedence `Fence.open` already gives it over an indented
      block, for the same reason.

      FOUR SPACES BEFORE A `>` IS CODE, NOT A QUOTE. `QUOTE_RE`'s own indent
      bound is CommonMark's three, so an over-indented `>` inside an indented
      example is content and needs no rule of its own.

    Nesting and the no-space spelling come along with it: `> > ` peels twice and
    `>` peels once, because peeling is a loop over one marker rather than a set
    of shapes.
    """

    def __init__(self) -> None:
        self._containers = [Container()]

    def feed(self, raw: str) -> bool:
        """Advance one line. True if the line is part of a code block of either
        spelling, in whatever container it sits in.
        """
        line = raw.expandtabs(TAB_STOP)

        depth = 0
        while depth >= len(self._containers) or not self._containers[depth].fenced:
            m = QUOTE_RE.match(line)
            if not m:
                break
            line = line[m.end() :]
            depth += 1

        if depth != len(self._containers) - 1:
            # A depth change is a container boundary. Quotes deeper than this
            # line closed, and their block state goes with them rather than
            # waiting to be consulted from a depth it does not describe. What
            # the innermost of them left open is the one thing that outlives it
            # -- see `Container.reopen`.
            lazy = (
                depth < len(self._containers) - 1
                and self._containers[-1].paragraph
            )
            del self._containers[depth + 1 :]
            while len(self._containers) <= depth:
                self._containers.append(Container())
            self._containers[depth].reopen(lazy)

        return self._containers[depth].feed(line)


class Unscopable(Exception):
    """A SKILL.md whose frontmatter block cannot be delimited.

    Raised rather than silently returning one merged scope. Scoring the parts
    separately is the whole of move 3, and a file whose parts cannot be told
    apart is a file this gate has nothing to say about -- so it says that,
    the way it already refuses when it cannot resolve a base.
    """

    def __init__(self, side: str = "") -> None:
        self.side = side
        super().__init__("the frontmatter block could not be located")


def split_scopes(text: str) -> dict[str, str]:
    """Cut a SKILL.md into the three parts that are scored separately.

    The frontmatter boundary is `validate_skills.py`'s own -- it measures the
    body as `content[m.end():]` against the size cap, so that is exactly where
    the byte pressure stops and the free-padding surface begins.

    Raises `Unscopable` when that boundary cannot be found. A merged scope is
    not a conservative default here, it is the evasion: with the frontmatter
    counted as prose, 46 words of padding in a `description:` net a deleted
    body section to nothing. Refusing costs a red run on a file that
    `validate-skills` rejects anyway; merging costs a green one on a file it
    accepts.
    """
    text = unwrap(text)
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise Unscopable()
    frontmatter, body = text[: m.end()], text[m.end() :]

    prose: list[str] = []
    code: list[str] = []
    block = Code()
    for line in body.split("\n"):
        (code if block.feed(line) else prose).append(line)

    return {
        "frontmatter": frontmatter,
        "prose": "\n".join(prose),
        "code": "\n".join(code),
    }


class Loss:
    """What a single file's edit did to its word supply, part by part.

    Each scope's loss is (words only in `before`) minus (words only in
    `after`), counted with multiplicity, within that scope alone. A rewrite
    that says the same thing differently scores near zero; a rewrap or a
    reorder scores exactly zero. A gain in one scope is NOT allowed to offset
    a loss in another -- see move 3 in the module docstring.

    `net` is the total that left the file and was not replaced where it left
    from: the sum of the scopes that lost words, ignoring those that gained.
    That is the number the ledger row carries.
    """

    def __init__(self, before: str, after: str) -> None:
        self._before, self._after = before, after
        scopes = {}
        for side, text in (("base", before), ("head", after)):
            try:
                scopes[side] = split_scopes(text)
            except Unscopable:
                raise Unscopable(side) from None
        b_scopes, a_scopes = scopes["base"], scopes["head"]

        self.scopes: dict[str, int] = {}
        self.gone: collections.Counter[str] = collections.Counter()
        for name in SCOPES:
            b = collections.Counter(words(b_scopes[name]))
            a = collections.Counter(words(a_scopes[name]))
            self.gone += b - a
            self.scopes[name] = sum((b - a).values()) - sum((a - b).values())

        self.over = {n: v for n, v in self.scopes.items() if v > FLOOR[n]}
        self.net = sum(v for v in self.scopes.values() if v > 0)

    def __bool__(self) -> bool:
        """True when some part of the file lost more than its floor allows."""
        return bool(self.over)

    def breakdown(self) -> str:
        """Which parts lost the words, for the error message.

        Every part that lost words, not only the parts that lost more than
        their floor -- otherwise the breakdown does not add up to the total the
        author is being asked to write into the ledger, and a reader is left to
        wonder which of the two numbers is the real one.
        """
        return ", ".join(
            f"{v} from its {SCOPE_LABEL[n]}"
            for n, v in sorted(self.scopes.items(), key=lambda kv: -kv[1])
            if v > 0
        )

    def excerpt(self, limit: int = 160) -> str:
        """The passage the loss came from, for the error message.

        Presentation only -- the verdict above is the multiset, which has no
        order and would otherwise report a bag of connective words that mean
        nothing to a reader. So take a line diff purely to recover candidate
        passages, and score each by how many of the genuinely-vanished words it
        holds. A rewrapped or reordered block scores zero by construction,
        because its words are still in the document.

        Two rules keep the word "Gone" true, and both exist because the message
        was caught being wrong about the reader's own diff -- which is how a
        gate stops being read:

          Only blocks that were DELETED are candidates, never blocks that were
          replaced. A replaced block is by definition not gone; quoting one
          meant quoting a passage still present verbatim in the file. Measured
          on the three real deletions, each is a delete block whose words are
          100% vanished, while an ordinary scattered copy-edit produces no
          delete block at all.

          Deletions have to account for at least half of what went. Otherwise
          the honest answer is that no single passage explains it, and the
          author is better served by the diff than by a confident excerpt.
        """
        before_lines = normalise(self._before).splitlines()
        after_lines = normalise(self._after).splitlines()
        ops = difflib.SequenceMatcher(
            a=before_lines, b=after_lines, autojunk=False
        ).get_opcodes()

        best, best_score, deleted = "", 0, 0
        for tag, i1, i2, _j1, _j2 in ops:
            if tag != "delete":
                continue
            block = [ln for ln in before_lines[i1:i2] if ln.strip()]
            score = sum(self.gone[w] > 0 for ln in block for w in WORD_RE.findall(ln))
            deleted += score
            if score > best_score:
                best, best_score = " ".join(ln.strip() for ln in block), score

        if not best or deleted * 2 < self.net:
            return "(no single passage accounts for it -- read the diff)"
        return best[:limit] + (" ..." if len(best) > limit else "")


# --- the escape hatch -------------------------------------------------------
#
# A row in the table in docs/prose-removals.md:
#
#   | skill-name | 44 | why the words are gone |
#
# Four rules keep it a declaration rather than a standing exemption, and each
# one is a hole somebody drove through in review:
#
#   ONLY A ROW THE CHANGE ITSELF ADDS COUNTS. A row inherited from the base is
#   somebody else's declaration about somebody else's deletion, and honouring
#   it rebuilds exactly the standing blanket exemption this repository already
#   removed once from the size gate: a grandfather row exempts one skill
#   visibly in review, but `limitBytes` was one line and exempted all 46 at
#   once, silently.
#
#   THE LEDGER IS APPEND-ONLY, AND A CHANGE THAT TAKES A ROW BACK OUT OF IT
#   DECLARES NOTHING. This is the rule above made true rather than intended.
#   Between two snapshots of a text file there is no such thing as an edited
#   row: an edit is one row removed and one row added, and nothing in the two
#   ledgers says which added row is which removed one. So an edit to an
#   inherited row could read as a fresh declaration, and twice did -- editing
#   the REASON, then editing the COUNT, each caught in review and each fixed in
#   that column alone. The count is far the worse of the two: a forged reason
#   could only ever cover a cut as large as the number already sitting there,
#   while `| alpha | 4 |` -> `| alpha | 54 |` is one character and covers any
#   number the author cares to type.
#
#   Column-by-column patching cannot close that, because the next column
#   reopens it. What does: every row the base ledger had must still be in the
#   head ledger, and the declarations this change made are the surplus on top.
#   Cardinality is the one thing an edit cannot forge -- editing any field of
#   any row, in any column, including a column added to this table years from
#   now, leaves a ledger with exactly as many rows as it started with and
#   therefore no surplus at all. Nor does a throwaway row bought to make the
#   total grow: the row that grows the total and the row that covers the cut
#   have to be the same row, and the inherited one it was laundering through is
#   missing.
#
#   CARDINALITY COUNTS THE FILE, NOT THE PARSE. That is the rule above made
#   true a second time, and it is the whole of this round. Counted over PARSED
#   rows, the invariant has one route out: a line whose ACCEPTANCE flips
#   without any line being added or removed. Every rule that made the parser
#   drop a line was therefore a staging slot -- park a row in a fence, in an
#   indented block, in an HTML comment, above the header, under a placeholder
#   reason, behind a malformed row, in a count that is not a number, in a second
#   table -- let
#   that change merge, and then make it readable here. The ledger gains a
#   declaration, the covering row sits in this change's diff as unchanged
#   context, and cardinality never notices because the row was never counted
#   at base. Eight predicates did it, and patching eight predicates would have
#   been the fifth round of patching whichever hole the last review happened to
#   try.
#
#   So every LINE occupies a slot, whether or not it parses: an accepted row is
#   keyed by (skill, count), and anything else by its own text. The total is
#   then the ledger's non-blank line count, which no change to what parses can
#   move, and the invariant follows from arithmetic rather than from the list
#   of predicates: `withdrawn` empty means head holds at least as many slots of
#   every identity as base, so with equal totals the two are the same multiset
#   and there is no surplus at all. A line that flips from inert to accepted
#   withdraws its own text-keyed slot on the way, which is a withdrawal, which
#   voids the change -- and the only way to put that slot back is to add a line
#   carrying the row verbatim, which is a declaration in the diff where a
#   reviewer reads it. That is the property this rule was always claiming.
#
#   THE COUNT HAS TO COVER THE CUT. That is not busywork -- it is what stops a
#   row being written blind, and it puts the magnitude in the diff where a
#   reviewer reads it. It is a floor, not an equality: a later commit in the
#   same PR that ADDS words shrinks the net, and demanding a fresh number on
#   every review round would make the ordinary life of a pull request the thing
#   that breaks the gate. Understating still fails -- you cannot declare 5 to
#   cover a cut of 500. The floor is only defensible because of the rule above.
#   A floor over a number the author can edit into a row that was already there
#   is what made the count hole worth driving through; over a row that is
#   provably surplus it is just a number somebody wrote in this diff, next to a
#   reason, where a reviewer reads both.
#
#   ROWS COUNT WITH MULTIPLICITY, ON (SKILL, COUNT) -- NOT ON THE REASON TEXT.
#   Two removals of the same size from the same skill are two declarations, so
#   a row keyed as a SET on (skill, count) alone deadlocked the second one:
#   the author followed the printed instruction exactly, the row was visibly
#   added by their change, and the gate failed anyway and reprinted the same
#   instruction. An escape hatch that cannot be opened is a bypass with extra
#   steps -- and this was the default case, not an exotic one, since 35 of the
#   49 skills carry two or more bullets of identical word length. The reason
#   cannot be part of the KEY either, and under the append-only rule that now
#   cuts both ways: keyed on the whole row, a one-character fix to an inherited
#   row's wording reads as that row withdrawn and an unrelated one added, which
#   once manufactured a declaration and would now void the change's own genuine
#   ones. Dropping the reason before comparing prices a copyedit at zero in
#   both directions, which is what it costs.
#
# The failure prints the exact row to paste, so paying it costs one copy plus a
# reason.

LEDGER_ROW_RE = re.compile(r"^\|([^|]+)\|([^|]+)\|(.+?)\|?\s*$")

# Anchored to the three columns it needs and open at the right-hand end, so a
# fourth column added to the table years from now still opens it. Closed with
# `\s*$`, adding one to the HEADER stopped the parser finding the table at all
# -- every row in it went silent and nobody could open the hatch, which is the
# opposite failure to the one this anchor is for.
LEDGER_HEADER_RE = re.compile(r"^\|\s*skill\s*\|\s*words\s*\|\s*why\s*\|", re.I)
LEDGER_RULE_RE = re.compile(r"^\|[\s:|-]+\|\s*$")

COMMENT_OPEN, COMMENT_CLOSE = "<!--", "-->"

# The reason field the error message hands you, unfilled. Rejected on sight:
# the hatch is meant to be cheap, not automatic, and the one thing it has to
# cost is somebody deciding the words are safe to lose. A row pasted straight
# from the failure declares nothing.
REASON_PLACEHOLDER = "<why these words are gone>"

# A reason that is not the placeholder, stood into a copy of the ledger to TEST
# the remedy before printing it rather than assert it -- see hatch_state. Never
# written to a file, and never shown to anybody.
FILLED_PROBE = "the reason those words are safe to lose"


def _comment_state(line: str, inside: bool) -> tuple[bool, bool]:
    """(did this line start inside an HTML comment, does the next one).

    A row with a trailing `<!-- note -->` is still a row -- the line starts
    outside the comment -- while every line of a commented-out draft table
    starts inside one and declares nothing.
    """
    started = inside
    i = 0
    while i < len(line):
        marker = COMMENT_CLOSE if inside else COMMENT_OPEN
        j = line.find(marker, i)
        if j < 0:
            break
        inside, i = not inside, j + len(marker)
    return started, inside


def _declaration(line: str) -> tuple[str, str, int] | None:
    """The row a table line declares, or None if it declares nothing.

    Keyed on (skill, count) and NOT on the reason. Two removals of the same
    size from the same skill are two rows, so multiplicity has to survive; the
    wording must not, or a one-character fix to an inherited row's reason reads
    as that row withdrawn and voids the change's own genuine declarations.
    Dropping the reason before comparing prices a copyedit at zero in both
    directions, which is what it costs.
    """
    m = LEDGER_ROW_RE.match(line)
    if not m:
        return None
    skill, count, reason = (g.strip().strip("`") for g in m.groups())
    if not reason.strip("- ") or REASON_PLACEHOLDER in reason:
        return None
    try:
        return ("row", skill, int(count))
    except ValueError:
        return None


def ledger_slots(text: str) -> collections.Counter[tuple]:
    """Every non-blank LINE of the ledger, as a slot with an identity.

    A declaration is keyed by what it declares; the table's header and rule row
    by what they are, so widening the table costs nothing; and every other line
    -- prose, a fenced or indented code block, a commented draft, a malformed
    row, a row parked above the header -- by its own text. Nothing is dropped.
    See the fourth rule above: the total has to be a property of the file, or a
    line becoming readable is a free declaration.

    Code is read in BOTH of markdown's spellings and in either container,
    `Code` rather than `Fence`, and the indented one is not a rounding error
    here: an indented example row is the first `| skill | words | why |` in the
    document, so it took `seen_table` and the real table under it went dead. See
    `Container`. This does not change what a SLOT is -- every non-blank line
    takes exactly one either way -- only whether an example's row is keyed by
    what it declares or by its own text, which is the point of counting lines
    rather than parses.

    The table runs from its header to the first non-blank line that does not
    begin with `|`, and there is only ever one table. Three choices, and each
    one is a defect that was reproduced:

      A LINE THAT DOES NOT PARSE DOES NOT END THE TABLE. It ends where markdown
      ends it -- at something that is not a table row -- rather than where the
      parser gives up. Ending on an unparsable line made a malformed row hide
      every row beneath it, so fixing that row's third cell published all of
      them at once.

      A BLANK LINE DOES NOT END IT EITHER. The table is the last thing in the
      file and appending is what an author does, so a blank separator before a
      pasted row is the ordinary case, not an exotic one. Ending on a blank
      left a correctly written row unread and the failure reprinting the row
      the author had just added -- an escape hatch that cannot be opened is a
      bypass with extra steps. Refusing to end the table at all is the other
      way to get this wrong: a pipe-shaped sentence in the prose below is not a
      declaration.

      ONLY THE FIRST TABLE COUNTS. A second `| skill | words | why |` header
      re-opened parsing, so any table anywhere in the document was live and the
      ledger's own "that table only" was false.
    """
    slots: collections.Counter[tuple] = collections.Counter()
    code = Code()
    in_comment = False
    in_table = seen_table = False

    for raw in lines_of(text):
        line = raw.strip()
        coded = code.feed(raw)
        commented, in_comment = _comment_state(line, in_comment)

        if not line:
            continue  # a blank line carries no identity and declares nothing
        if in_table and not line.startswith("|"):
            in_table = False  # the table ended; what follows it is prose
        if coded or commented:
            slots[("line", line)] += 1
        elif not in_table:
            if not seen_table and LEDGER_HEADER_RE.match(line):
                in_table = seen_table = True
                slots[("header",)] += 1
            else:
                slots[("line", line)] += 1
        elif LEDGER_RULE_RE.match(line):
            slots[("rule",)] += 1
        else:
            slots[_declaration(line) or ("line", line)] += 1

    return slots


def parse_ledger(text: str) -> collections.Counter[tuple[str, int]]:
    """The declarations the ledger's table carries, counted with multiplicity.

    The readable half of `ledger_slots`: what a reader of the ledger would see
    as a row. The gate compares slots, not these -- a declaration a reader
    would never see is not one, and a line that is not a declaration still has
    to occupy a slot.
    """
    return collections.Counter(
        {(s[1], s[2]): n for s, n in ledger_slots(text).items() if s[0] == "row"}
    )


def ledger_row(skill: str, net: int) -> str:
    return f"| {skill} | {net} | {REASON_PLACEHOLDER} |"


class LedgerDiff:
    """What a change did to `docs/prose-removals.md`, slot by slot.

    `added` is what the change may spend: the declarations it is credited with.
    `lost_rows` is a finding in its own right -- the ledger says a row stays
    after it merges, and that was asserted and enforced nowhere, so a change
    that wiped every row while touching no SKILL.md went green.
    """

    def __init__(self, before: str, after: str) -> None:
        base, head = ledger_slots(before), ledger_slots(after)
        self.surplus = head - base
        self.withdrawn = base - head
        self.lost_rows = collections.Counter(
            {s: n for s, n in self.withdrawn.items() if s[0] == "row"}
        )
        # A change that took ANY slot out is credited with nothing: an edit is a
        # withdrawal plus an addition, so crediting the addition while ignoring
        # the withdrawal is exactly what let an edit to any one column -- or a
        # line made readable that had been parked unreadable -- declare on its
        # own.
        self.declared = collections.Counter(
            {(s[1], s[2]): n for s, n in self.surplus.items() if s[0] == "row"}
        )
        self.added = (
            collections.Counter() if self.withdrawn else self.declared
        )


def declares(
    added: collections.Counter[tuple[str, int]], skill: str, net: int
) -> bool:
    """Does a row this change added cover a loss of `net` words from `skill`?"""
    return any(s == skill and c >= net for s, c in added)


# How far this skill's declaration has got in the ledger as the change leaves
# it. The failure's remedy is chosen from this and from nothing else, because
# the defect it exists to fix was a remedy that was a CONSTANT: the message
# printed `| session-heartbeat | 49 | <why these words are gone> |` and closed
# with "add the row printed above ... and this gate passes", while
# `_declaration` rejects precisely that row for precisely that placeholder. An
# author who did exactly what the message said got the same failure back, byte
# for byte, with nothing in it naming the placeholder or the word "replace".
# That is the "escape hatch that cannot be opened is a bypass with extra steps"
# failure this module names twice as its own reason for existing -- reached on
# the path every first-time failure takes, rather than on an exotic one.
ABSENT, DRAFTED, STANDING = "absent", "drafted", "standing"


def hatch_state(before: str, after: str, skill: str, net: int) -> str:
    """Where the declaration for a `net`-word cut from `skill` has got to.

      ABSENT    nothing in the ledger speaks to this cut, so the failure hands
                over the row to write.
      DRAFTED   the row the failure printed is sitting in the ledger with its
                placeholder unfilled. Filling it in is the remedy, and it is
                the remedy because it was TESTED: a copy of the head ledger
                with a real reason stood into that row is run back through the
                same credit rules the verdict came from. A remedy this gate
                asserts rather than checks is how it came to print one that
                could not work.
      STANDING  the ledger already shows a reader a row covering this cut, and
                this change is not credited with it -- inherited from the base,
                or voided by a withdrawal. Printing "add this row" over one is
                the message being wrong about the reader's own diff, which
                `Loss.excerpt` already names as how a gate stops being read.

    DRAFTED is tried first: when both could describe the ledger, the tested
    remedy is the one that is known to reach green.
    """
    printed = ledger_row(skill, net)
    if printed in after:
        filled = after.replace(printed, f"| {skill} | {net} | {FILLED_PROBE} |")
        if declares(LedgerDiff(before, filled).added, skill, net):
            return DRAFTED
    if declares(parse_ledger(after), skill, net):
        return STANDING
    return ABSENT


# The one phrase that identifies each failure mode's annotation, owned here so
# the message and the guidance `main` prints under it cannot drift apart --
# `run` also annotates the ledger itself and any file it could not scope, and
# `main` annotates any blob that would not come back. Those are four different
# findings and they do not share a remedy. LOST_PROSE additionally carries the
# count of undeclared removals.
LOST_PROSE = "::this SKILL.md lost "
UNSCOPABLE_FILE = "::this SKILL.md's YAML frontmatter could not be located"
UNREADABLE_BLOB = "::git lists this file as changed"
LEDGER_REWOUND = "::this change takes "
SLOTS_WITHDRAWN = f"back OUT of {LEDGER}"

# How an undeclared-removal annotation told its author to open the hatch: one
# of these three ends every one of them, chosen by `hatch_state`. `main` reads
# the phrase back off the annotation it is about to print rather than working
# the state out a second time -- a second computation is a second place for the
# message and the remedy under it to disagree, and disagreeing is the defect.
ROW_INTRO = (
    f"add this row to {LEDGER} in this same change, with "
    f"{REASON_PLACEHOLDER} replaced by the reason those words are safe to "
    f"lose -- a row pasted unedited declares nothing: "
)
DRAFT_INTRO = f"{LEDGER} already carries that row, with "
STANDING_INTRO = f"{LEDGER} already shows a row covering this cut, but "

# The tail STANDING takes when the covering row was inherited rather than
# voided by a withdrawal, and the only one of the two with a remedy of its own.
# When a withdrawal is what voided the row, putting the ledger back is the whole
# remedy -- telling that author to write a second row is telling them to write
# one that will not count either.
INHERITED_ROW = "not one this change added"


def run(
    cases: dict[str, tuple[str, str]],
    ledger_before: str = "",
    ledger_after: str = "",
) -> list[str]:
    """Check every (path -> (before, after)) pair. Returns error annotations.

    `cases` carries every SKILL.md modified between the two revisions, renames
    included, keyed by its path at head. Whole-file additions and deletions are
    deliberately out of scope: git renders those as a file appearing or
    disappearing, which review cannot miss, and `main` says out loud how many
    it skipped. This gate exists for the removal that hides inside an
    otherwise-ordinary edit -- which is how all three historical cases got
    through.
    """
    ledger = LedgerDiff(ledger_before, ledger_after)
    errors: list[str] = []

    if ledger.lost_rows:
        rows = ", ".join(
            f"`| {skill} | {count} |`"
            for _kind, skill, count in sorted(ledger.lost_rows)
        )
        errors.append(
            f"::error file={LEDGER}{LEDGER_REWOUND}"
            f"{sum(ledger.lost_rows.values())} declared row(s) back out of the "
            f"ledger: {rows}. A row stays after it merges -- this file is the "
            f"record, and a change that empties it erases somebody else's "
            f"declaration about somebody else's deletion. Correcting a row "
            f"means adding a new one and leaving the old one standing, because "
            f"between two snapshots an edit is a removal plus an addition and "
            f"nothing says which added row is which removed one."
        )

    for path in sorted(cases):
        before, after = cases[path]
        skill = Path(path).parent.name
        try:
            loss = Loss(before, after)
        except Unscopable as e:
            errors.append(
                f"::error file={path}{UNSCOPABLE_FILE} at the {e.side} "
                f"revision, so its frontmatter, prose and code cannot be told "
                f"apart and no verdict is reported for it. A SKILL.md opens "
                f"with a `---` line and closes the block with another. "
                f"Scoring the parts separately "
                f"is what stops words added to a `description:` paying for "
                f"prose deleted from the body, so a file whose parts cannot be "
                f"separated is one this gate has nothing to say about."
            )
            continue
        if not loss:
            continue

        if declares(ledger.added, skill, loss.net):
            continue

        # Printed whenever a withdrawal stands, not only when a surplus row
        # would otherwise have covered the cut. While anything is missing from
        # the ledger no row this change adds counts at all, so "add the row
        # printed above and this gate passes" is false for every one of these
        # authors, and the sentence that explains why was the one being
        # withheld.
        rewritten = (
            f" This change also takes {sum(ledger.withdrawn.values())} line(s) "
            f"that were already there {SLOTS_WITHDRAWN}, and while it does "
            f"that no row it adds counts: between two snapshots an edit to an "
            f"inherited row is a removal plus an addition, so any edit at all "
            f"would otherwise declare on its own. Put back what it removed and "
            f"add yours as a new row."
            if ledger.withdrawn
            else ""
        )

        # The one sentence an author acts on, and the only part of this message
        # that is about their ledger rather than about their diff. It has to be
        # true of the ledger they are actually looking at: "add this row" is a
        # loop when the row is already there under the placeholder, and it is
        # wrong about their own diff when a row covering the cut is on screen.
        state = hatch_state(ledger_before, ledger_after, skill, loss.net)
        if state == DRAFTED:
            hatch = (
                f"{DRAFT_INTRO}{REASON_PLACEHOLDER} still in it, so it declares "
                f"nothing. Deciding the words are safe to lose is the one thing "
                f"this hatch costs and the one thing it cannot do for you: "
                f"replace the placeholder with the reason."
            )
        elif state == STANDING and ledger.withdrawn:
            hatch = f"{STANDING_INTRO}not one this change is credited with."
        elif state == STANDING:
            hatch = (
                f"{STANDING_INTRO}{INHERITED_ROW}, and only a row the "
                f"change itself adds counts. An inherited row is somebody "
                f"else's declaration about somebody else's deletion, and "
                f"honouring it would make that file the standing exemption this "
                f"repository already removed once from the size gate. Declare "
                f"this cut as a new row of your own."
            )
        else:
            hatch = (
                f"If the removal is deliberate, {ROW_INTRO}"
                f"{ledger_row(skill, loss.net)}"
            )

        errors.append(
            f"::error file={path}{LOST_PROSE}{loss.net} words that "
            f"nothing in the same part of it replaced ({loss.breakdown()}). "
            f"Rewrapping, reordering, moving a line and converting `{skill}` "
            f"to a markdown link all score zero here, so this is content, not "
            f"layout. Each part is scored on its own, so words added to the "
            f"frontmatter or to a code block cannot pay for prose that went "
            f"missing. Gone: {loss.excerpt()}. {hatch}{rewritten}"
        )

    return errors


# Every failure mode, and the closing line that is true of THAT mode. One block
# closed all of them with "Add the row printed above ... and this gate passes",
# and it was false on every mode but one: no row is printed for a file whose
# frontmatter cannot be located, none for a blob that would not come back, none
# for a ledger a change rewound -- and on the mode that did print one, the row
# carried the placeholder `_declaration` rejects, so pasting it reproduced the
# failure byte for byte.
#
# `promises` is whether the line may end in "and this gate passes". A withdrawal
# voids every row a change adds, so nothing may promise green while one stands.
REMEDIES = [
    (
        ROW_INTRO,
        f"Add the row printed above to {LEDGER} in this same change, with "
        f"{REASON_PLACEHOLDER} replaced by the reason those words are safe to "
        f"lose.",
        True,
    ),
    (
        DRAFT_INTRO,
        f"Replace {REASON_PLACEHOLDER} on the row already in {LEDGER} with the "
        f"reason those words are safe to lose. Until somebody writes that down "
        f"the row declares nothing.",
        True,
    ),
    (
        INHERITED_ROW,
        f"Declare the cut named above as a NEW row in {LEDGER}. The row already "
        f"there was inherited from the base, and is not this change's to spend.",
        True,
    ),
    (
        UNSCOPABLE_FILE,
        "Open each file named above with a `---` line and close the block with "
        "another, so this gate can tell its frontmatter from its body. Until it "
        "can, it reports no verdict on that file rather than a merged one.",
        False,
    ),
    (
        UNREADABLE_BLOB,
        "Each file named above was listed as changed and could not be read at "
        "one of the two revisions, so it was never compared. Check the checkout "
        "step sets `fetch-depth: 0`.",
        False,
    ),
    (
        SLOTS_WITHDRAWN,
        f"Put back every line this change took out of {LEDGER}. While anything "
        f"is missing from that file, no row the change adds counts at all.",
        False,
    ),
    (
        LEDGER_REWOUND,
        f"Put the row(s) named above back into {LEDGER}. A row stays after it "
        f"merges; correcting one means adding a new row and leaving the old one "
        f"standing.",
        False,
    ),
]

PASSES = " That is the whole cost, and this gate passes."

# Appended in place of PASSES when a failure this line does not answer is also
# being printed. "and this gate passes" is a claim about the RUN, not about one
# finding, and the run exits 1 while any of them stands. What to do about the
# other one is the remedy printed beside this one, which is why this line points
# rather than repeating it.
HELD = (
    " It is not the whole cost: this gate stays red until the other findings "
    "above are cleared too."
)

# Printed when nothing above matches, which nothing this gate emits should
# reach. A guidance block that closes with a remedy for a failure that did not
# happen is the defect; closing with nothing at all is the same defect quieter.
NO_REMEDY = (
    "Read the annotations above: each one names the file it is about and what "
    "this gate could not do with it."
)


def remedies(errors: list[str]) -> list[str]:
    """The closing lines that are true of the failures being printed.

    Read off the annotations themselves rather than recomputed from the ledger.
    The guidance and the annotation above it then cannot describe two different
    failures, which they did: the block asked every author to add a row printed
    above, including the three modes that print no row.
    """
    # A line may only end in "and this gate passes" when every failure being
    # printed has a remedy that reaches green, because that promise is about the
    # run. Read off REMEDIES' own `promises` flag rather than enumerated:
    # computed from the ledger's two modes alone it promised green to an author
    # whose change also carried a file this gate could not scope -- they did
    # exactly what the line said and got exit 1 -- and every mode added after
    # would have reopened it again.
    held = any(
        marker in e
        for marker, _line, promises in REMEDIES
        if not promises
        for e in errors
    )
    lines = [
        line + (HELD if held else PASSES) if promises else line
        for marker, line, promises in REMEDIES
        if any(marker in e for e in errors)
    ]
    return lines or [NO_REMEDY]


# --- git plumbing -----------------------------------------------------------


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], capture_output=True, text=True, check=False
    )


class Undecodable(Exception):
    """A git blob at `rev:path` is not valid UTF-8.

    Raised rather than left to `subprocess`'s own `text=True` decoding, which
    throws a bare `UnicodeDecodeError` with no file attached to it. This gate
    already fails closed on that -- the process exits non-zero either way --
    but a stack trace carries no `::error file=...::` annotation, so CI shows
    no file annotation for a real failure. `main` catches this and turns it
    into one.
    """

    def __init__(self, rev: str, path: str) -> None:
        self.rev, self.path = rev, path
        super().__init__(f"{path} at {rev} is not valid UTF-8")


def _show(rev: str, path: str) -> str | None:
    """File content at `rev`, or None if it does not exist there.

    Decoded by hand rather than via `_git`'s `text=True`, so an invalid byte
    raises `Undecodable` -- naming the file -- instead of `subprocess`'s own
    unannotated `UnicodeDecodeError`.
    """
    got = subprocess.run(
        ["git", "show", f"{rev}:{path}"], capture_output=True, check=False
    )
    if got.returncode != 0:
        return None
    try:
        return got.stdout.decode("utf-8")
    except UnicodeDecodeError:
        raise Undecodable(rev, path) from None


class Diff:
    """What changed between two revisions, split into what this gate can judge.

    `cases` are the modified and renamed SKILL.md files, keyed by their path at
    head. `added` and `deleted` are counted but not compared, and `main` says
    so out loud: a gate that prints OK without mentioning what it left out is
    reporting success over a comparison it did not make.
    """

    def __init__(self) -> None:
        self.cases: dict[str, tuple[str, str]] = {}
        self.added: list[str] = []
        self.deleted: list[str] = []
        self.renamed: list[tuple[str, str]] = []
        self.unreadable: list[tuple[str, str]] = []

    def pair(self, base: str, old: str, head: str, new: str) -> None:
        """Record one before/after comparison, whatever the paths were called.

        One site, so the rename branch and the ordinary-modification branch
        cannot drift apart -- and so "did this file actually change?" is a
        single decision rather than a promise made twice.

        git named these two revisions of this path itself, so a blob that will
        not come back is a comparison this gate could not make. Recorded rather
        than dropped: dropping it printed OK over a file that was never opened
        and never mentioned, which is the exact thing this class says out loud
        it does not do.
        """
        before, after = _show(base, old), _show(head, new)
        for rev, path, got in ((base, old, before), (head, new, after)):
            if got is None:
                self.unreadable.append((rev, path))
        if before is None or after is None:
            return
        if before != after:
            self.cases[new] = (before, after)


def _name_status(out: str) -> list[tuple[str, list[str]]]:
    """Parse `git diff --name-status -z` into (status, paths) records.

    NUL-separated, because the tab-and-newline format QUOTES any path carrying
    a byte outside printable ASCII -- `skills/\\316\\261-skill/SKILL.md`, with
    the quotes -- and a quoted path matches no glob here, so the file dropped
    out of the comparison and the run printed "OK: 0 changed SKILL.md file(s)"
    over a real deletion. Reproduced. A status starting R or C carries two
    paths; everything else carries one.
    """
    fields = [f for f in out.split("\0") if f]
    records: list[tuple[str, list[str]]] = []
    i = 0
    while i < len(fields):
        status = fields[i]
        n = 2 if status[:1] in ("R", "C") else 1
        records.append((status, fields[i + 1 : i + 1 + n]))
        i += 1 + n
    return records


def collect(base: str, head: str) -> Diff:
    """Pair every changed SKILL.md across the two revisions.

    Pairing is by git's own rename detection, not by path. Renaming a skill is
    documented ordinary practice here, and it is exactly the moment prose goes
    missing -- but a path-keyed comparison drops a renamed file out of both
    sides at once and then prints "0 changed SKILL.md file(s)" over a deletion
    it never looked at. Reproduced: renaming clud-bug-collaboration while
    deleting its CLUD_BUG_QUIET section passed a path-keyed gate green.

    The similarity threshold is lowered from git's default 50% because the
    change this gate hunts is precisely a rename that ALSO cut content, and a
    large enough cut drops a real rename below the default, turning it back
    into an add plus a delete.

    A cut deep enough to fall below 25% still lands there, and this gate does
    not compare it -- but `main` prints the count of files added and deleted
    whole rather than a bare OK, so the run says what it did not look at. At
    that depth git itself renders the change as a file disappearing, which is
    the out-of-scope class review cannot miss.
    """
    diff = Diff()
    got = _git(
        "diff", "--name-status", "-z", "--find-renames=25%", base, head, "--", "skills"
    )
    if got.returncode != 0:
        return diff

    for status, paths in _name_status(got.stdout):
        skill_paths = [p for p in paths if SKILL_GLOB_RE.match(p)]
        if not skill_paths:
            continue

        if status.startswith("R") and len(paths) == 2:
            old, new = paths
            if not (SKILL_GLOB_RE.match(old) and SKILL_GLOB_RE.match(new)):
                continue
            diff.renamed.append((old, new))
            diff.pair(base, old, head, new)
        elif status.startswith("A"):
            diff.added.append(skill_paths[0])
        elif status.startswith("D"):
            diff.deleted.append(skill_paths[0])
        else:  # M, and anything else git reports as a content change
            path = skill_paths[0]
            diff.pair(base, path, head, path)

    return diff


def _merge_base() -> str | None:
    """The default base: where this branch left the trunk.

    NOT the trunk's tip. Comparing against a moving tip attributes main's own
    edits to this branch -- prose added on main after the fork reads as prose
    this branch deleted.

    Tries `dev` before `main`. Every branch in this repository forks from and
    targets `dev` (docs/decisions-branches/docs__dev-branch-convention.md);
    `main` only receives `dev` in batches, so `dev` routinely carries prose
    `main` does not have yet. A default that only ever reached `main` compared
    against an older snapshot -- a real cut on the branch could net to a GAIN
    against `main`'s stale copy while it was a real loss against the actual
    fork point, which is the dangerous direction: it prints OK where CI, which
    merge-bases against the PR's actual base, fires. Falls back to `main` so
    this still runs on a checkout of only `main`, or a branch cut from it
    directly; pass --base explicitly if this branch targets neither.
    """
    for trunk in ("origin/dev", "dev", "origin/main", "main"):
        if _git("rev-parse", "--verify", f"{trunk}^{{commit}}").returncode != 0:
            continue
        got = _git("merge-base", trunk, "HEAD")
        if got.returncode == 0 and got.stdout.strip():
            return got.stdout.strip()
    return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--base",
        help="revision to compare against (default: merge base with dev, "
        "falling back to main)",
    )
    ap.add_argument("--head", default="HEAD", help="revision under review")
    args = ap.parse_args(argv)

    base = args.base or _merge_base()
    if base is None:
        print(
            "::error::no --base was given and there is no dev or main to take "
            "a merge base from, so no comparison was made. Pass --base "
            "explicitly."
        )
        return 1

    # Refuse to report success over a comparison that did not happen. A gate
    # that cannot resolve its base has not checked anything, and saying so is
    # cheaper than a green tick over nothing.
    for label, rev in (("base", base), ("head", args.head)):
        if _git("rev-parse", "--verify", f"{rev}^{{commit}}").returncode != 0:
            print(
                f"::error::cannot resolve the {label} revision '{rev}', so no "
                "comparison was made. This gate needs the full history: check "
                "the checkout step sets `fetch-depth: 0`."
            )
            return 1

    try:
        diff = collect(base, args.head)
        ledger_before = _show(base, str(LEDGER)) or ""
        ledger_after = _show(args.head, str(LEDGER)) or ""
    except Undecodable as e:
        print(
            f"::error file={e.path}::cannot read this file at {e.rev} -- it is "
            "not valid UTF-8, so no prose comparison could be made. Fix the "
            "encoding and this gate can run again."
        )
        return 1

    errors = [
        f"::error file={path}{UNREADABLE_BLOB} between the two "
        f"revisions, but its content at {rev} could not be read, so it was not "
        f"compared and no verdict is reported for it."
        for rev, path in diff.unreadable
    ]
    errors += run(diff.cases, ledger_before, ledger_after)

    if errors:
        for e in errors:
            print(e)
        undeclared = sum(1 for e in errors if LOST_PROSE in e)
        if undeclared:
            print(f"::error::{undeclared} SKILL.md file(s) lost prose undeclared")

        # The last sentence has to be true of the failure the reader is looking
        # at. It said "add the row printed above and this gate passes" over
        # every failure -- over the one where a withdrawal from the ledger means
        # no row they add can count, over the three that print no row at all,
        # and over the one where the row it printed carried the placeholder that
        # makes the row declare nothing.
        remedy = "\n\n".join(
            textwrap.fill(line, 84) for line in remedies(errors)
        )
        print(
            f"\nA size limit and a link sweep both push in the same direction: "
            f"delete something.\nThat is how three skills lost real content on "
            f"a change whose whole purpose\nwas strengthening the links between "
            f"them, with every check green.\n\nWhat genuinely scores zero here: "
            f"rewrapping a paragraph, reordering sections, moving\na passage "
            f"within the same part of the file (prose stays prose, code stays "
            f"code), and\nrewording at a similar length. Tightening does not -- "
            f"this gate counts words, so a\nshorter passage that says the same "
            f"thing has a smaller count, and it fires like any\nother cut. "
            f"That is not a bypass: a genuine tightening is a declared "
            f"removal, same as a\ndeletion, and costs exactly one ledger row. "
            f"That row is the whole point of the ledger,\nnot a way around "
            f"it.\n\nDeleting prose is allowed. Doing it silently is not.\n\n"
            f"{remedy}"
        )
        return 1

    skipped = ""
    if diff.added or diff.deleted:
        skipped = (
            f", plus {len(diff.added)} added and {len(diff.deleted)} deleted "
            "whole, which this gate does not compare"
        )
    print(
        f"OK: {len(diff.cases)} changed SKILL.md file(s){skipped}. "
        "No undeclared prose removal."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
