"""Prove `test_check_prose_retention.py` can fail.

A check that has never failed on demand is not proven. This file breaks the
detector on purpose, one way per entry in MUTATIONS below, and asserts the suite
goes red each time -- committed, so the proof re-runs on every PR rather than
living in somebody's recollection of a terminal session.

How it works: copy the real detector into a scratch tree, apply one textual
mutation, copy the real suite in beside it, and run pytest there in a
subprocess. Red means the suite noticed. Every mutation also asserts it
*landed* -- a find-and-replace that silently matched nothing would otherwise
"prove" the suite works by testing an unmodified file, which is the same
mistake as a control-free grep.

`test_control_the_unmutated_detector_is_green` is the other half. Without it,
"the suite went red" could just mean the scratch harness is broken and would
report red for any input at all. Two ways of breaking THIS file -- a scratch
conftest that does not expose the mutated module, and fixtures that fail to
copy -- make every mutation test pass vacuously, and the control is the only
thing that catches either.

Every mutation carries the consequence it reintroduces. A mutation nobody can
name the defect for is not worth committing, and a mutation caught only by some
unrelated test proves less than it looks: each of these dies on the test that is
about its behaviour.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DETECTOR = REPO_ROOT / ".github" / "scripts" / "check_prose_retention.py"
SUITE = Path(__file__).parent / "test_check_prose_retention.py"
FIXTURES = Path(__file__).parent / "fixtures" / "prose-retention"
LEDGER = REPO_ROOT / "docs" / "prose-removals.md"
SKILLS = REPO_ROOT / "skills"

# Each entry: a name, the exact source text to replace, and what to replace it
# with.
MUTATIONS = [
    # -- the thresholds -----------------------------------------------------
    (
        # The gate stops firing on prose at all. Every historical case walks
        # through, because all three cut prose.
        "prose_floor_disabled",
        '    "prose": 2,',
        '    "prose": 999,',
    ),
    (
        # Off by one. The boundary pair either side of the measured prose noise
        # floor is what should catch this, not the large historical cases.
        "prose_floor_off_by_one",
        '    "prose": 2,',
        '    "prose": 3,',
    ),
    (
        # Gutting a `description:` stops being content loss, so a skill can be
        # made undiscoverable without a word of explanation.
        "frontmatter_floor_disabled",
        '    "frontmatter": 3,',
        '    "frontmatter": 999,',
    ),
    (
        # Worked examples stop being content, which reopens the byte arbitrage:
        # delete a code block, add filler prose, keep the gate green.
        "code_floor_disabled",
        '    "code": 3,',
        '    "code": 999,',
    ),
    # -- normalisation ------------------------------------------------------
    (
        # The load-bearing move deleted. Without it the #197 sweep reads as a
        # word gain and web-interface-guidelines-review goes green.
        "normalisation_removed",
        '    return URL_RE.sub(" ", LINK_RE.sub(lambda m: m.group(1), text))',
        "    return text",
    ),
    (
        # Narrowed back to links that end in SKILL.md, as it originally shipped.
        # De-linking any of the catalog's 37 external links then costs 3-8
        # invented words while the sentence keeps every real one -- the
        # false-positive direction, on the repo's own routine link maintenance.
        "link_pattern_narrowed_to_skill_files",
        r'LINK_RE = re.compile(r"!?\[([^\]\n]*)\]\([^)\n]*\)")',
        r'LINK_RE = re.compile(r"\[([^\]\n]+)\]\([^)\s]*?SKILL\.md(?:#[^)\s]*)?\)")',
    ),
    (
        # URLs become prose again, so dropping a rotted reference is charged as
        # a deletion of however many path segments it happened to have.
        "urls_counted_as_words",
        '    return URL_RE.sub(" ", LINK_RE.sub(lambda m: m.group(1), text))',
        "    return LINK_RE.sub(lambda m: m.group(1), text)",
    ),
    # -- the scopes ---------------------------------------------------------
    (
        # All three parts collapse into one, restoring whole-file scoring.
        # Padding the `description:` then pays for a deleted body section, and
        # filler prose pays for a deleted code example -- both reproduced, both
        # green, on the file that really did lose its CLUD_BUG_QUIET section.
        "scopes_netted_together",
        '    return {\n        "frontmatter": frontmatter,\n'
        '        "prose": "\\n".join(prose),\n        "code": "\\n".join(code),\n    }',
        '    return {"frontmatter": "", "prose": text, "code": ""}',
    ),
    (
        # The frontmatter folds into the prose scope, which is the specific
        # half of the evasion above: the size cap excludes the frontmatter, so
        # padding there is free against the constraint that caused the defect.
        "frontmatter_folded_into_the_body",
        "    frontmatter, body = text[: m.end()], text[m.end() :]",
        '    frontmatter, body = "", text',
    ),
    (
        # The refusal deleted, so a file whose frontmatter cannot be located
        # silently gets one merged scope instead of no verdict -- which is the
        # same evasion, reached without anybody having to edit the split.
        "unlocatable_frontmatter_merged_instead_of_refused",
        "    if not m:\n        raise Unscopable()",
        "    if not m:\n        return {"
        '"frontmatter": "", "prose": text, "code": ""}',
    ),
    (
        # Line endings stop being normalised. A SKILL.md with CRLF then passes
        # `validate-skills` -- which reads through `Path.read_text` and never
        # sees them -- and arrives here with no frontmatter this gate can find.
        # Measured: all three historical deletions go green.
        "line_endings_not_normalised",
        '    return text.lstrip(BOM).replace("\\r\\n", "\\n").replace("\\r", "\\n")',
        "    return text",
    ),
    (
        # A fence closes on any run of three, so a ``` line inside a ````
        # block ends it. Everything below changes scope without being edited.
        "fence_length_ignored",
        "            and len(m.group(1)) >= length",
        "            and len(m.group(1)) >= 3",
    ),
    (
        # Markdown's second spelling of a code block stops being read, which is
        # the whole class: an indented worked example scores as prose, so
        # deleting one and adding a same-length sentence of filler nets to zero
        # and the gate goes green. Same byte arbitrage as the fenced case above,
        # through the spelling that costs MORE bytes per word.
        "indented_code_blocks_not_read",
        "        if not self._paragraph and indent >= self._threshold():",
        "        if False and indent >= self._threshold():",
    ),
    (
        # The false-positive direction of the same reading. An indented block
        # may interrupt a paragraph again, so every wrapped list continuation in
        # the catalog moves into the code scope -- real prose, charged against
        # the wrong floor and payable by the wrong additions.
        "an_indented_block_may_interrupt_a_paragraph",
        "        if not self._paragraph and indent >= self._threshold():",
        "        if indent >= self._threshold():",
    ),
    (
        # The four spaces are measured from the left margin rather than from the
        # enclosing list item's content column, so a nested bullet's second
        # paragraph reads as code. The same false positive, reached through the
        # other CommonMark rule.
        "the_list_content_column_is_ignored",
        "        return (self._lists[-1] if self._lists else 0) + CODE_INDENT",
        "        return CODE_INDENT",
    ),
    (
        # An open fence stops being advanced, so it never closes: every line
        # after the catalog's first ``` reads as code, in files nobody edited.
        "an_open_fence_stops_being_advanced",
        "        if self._fence.open:\n            self._fence.feed(line)",
        "        if False:\n            self._fence.feed(line)",
    ),
    (
        # An indented block ends after its first line, so its remaining lines go
        # back to being read as markdown -- and a ``` quoted inside one then
        # opens a fenced block that swallows every line to the end of the file.
        # That is worse than not reading indented blocks at all: text nobody
        # edited changes scope.
        #
        # Reached by claiming a paragraph is open INSIDE the block, which is the
        # only way left: continuing a block and opening one are now one
        # condition, so there is no separate continuation branch to delete.
        "an_indented_block_ends_after_its_first_line",
        "            self._indented = True\n            return True",
        "            self._indented = True\n"
        "            self._paragraph = True\n            return True",
    ),
    (
        # Tabs stop being expanded before the indent is measured, leaving the
        # same hole in a third spelling: a tab-indented block is four columns to
        # CommonMark and zero to `lstrip(" ")`.
        "tabs_not_expanded_before_measuring_the_indent",
        "        line = raw.expandtabs(TAB_STOP)",
        "        line = raw",
    ),
    # -- a block quote is a container, not a third spelling -----------------
    (
        # Block quotes stop being containers, which is how it shipped: a `>` in
        # front hid BOTH spellings of a code block at once, so a quoted worked
        # example scored as prose. Deleting a paragraph and putting one in its
        # place then netted to zero and the gate passed a cut it fires on when
        # the same example is spelled as a plain fence.
        "quoted_code_blocks_not_read",
        r'QUOTE_RE = re.compile(r"^ {0,3}> ?")',
        r'QUOTE_RE = re.compile(r"^(?!)")',
    ),
    (
        # The marker matches at any indent, so a `>` quoted INSIDE an indented
        # example is peeled into a container of its own and the example's own
        # content moves back to the prose scope -- the founding evasion, reached
        # by writing a block quote inside the block.
        "a_quote_marker_matches_at_any_indent",
        r'QUOTE_RE = re.compile(r"^ {0,3}> ?")',
        r'QUOTE_RE = re.compile(r"^ *> ?")',
    ),
    (
        # The marker requires a space after it, so `>```` is not a container and
        # the same evasion is open one character in.
        "a_quote_marker_requires_a_space_after_it",
        r'QUOTE_RE = re.compile(r"^ {0,3}> ?")',
        r'QUOTE_RE = re.compile(r"^ {0,3}> ")',
    ),
    (
        # A fence stops outranking a marker, so a `>` on a line INSIDE a fenced
        # block -- a markdown example, which this catalog is full of -- is
        # peeled into a container that does not exist. The real fence never
        # closes and every line below it changes scope.
        "a_fence_does_not_outrank_a_quote_marker",
        "        while depth >= len(self._containers) or not "
        "self._containers[depth].literal:",
        "        while True:",
    ),
    (
        # A closed container's blocks are left dormant instead of discarded, so
        # a fence opened inside a quote is still open when a LATER quote starts
        # and swallows it -- text nobody edited, rescoped by a blank line
        # somewhere above it.
        "a_closed_container_keeps_its_open_blocks",
        "            del self._containers[depth + 1 :]",
        "            del self._containers[len(self._containers) :]",
    ),
    (
        # The container boundary stops being one: a quote whose last block was a
        # fence leaves nothing to continue, so four spaces under it are a code
        # block, and this reads them as the previous paragraph's wrapped text.
        "a_container_boundary_never_reopens_the_parent",
        "        self._indented = False\n        self._paragraph = lazy",
        "        self._indented = False",
    ),
    (
        # The other half: every container boundary is assumed to be one, so a
        # line lazily continuing a quote's open PARAGRAPH opens an indented code
        # block instead. Real prose, rescoped, charged against the wrong floor.
        "a_container_boundary_always_reopens_the_parent",
        "        self._indented = False\n        self._paragraph = lazy",
        "        self._indented = False\n        self._paragraph = False",
    ),
    (
        # The indented block open OUTSIDE the quote survives it, so the lines
        # after a quote resume a code block the marker already closed.
        #
        # What that costs shrank when the paragraph model landed, and the
        # comment says so rather than the name outliving the defect: a
        # WORD-BEARING line after the quote is now decided by whether a
        # paragraph is open, not by the leaked flag, so what leaks is the blank
        # line's own scope. Measured: 4380 of 60000 quote-heavy documents read
        # differently and NONE of them differ on a line carrying words. The
        # test below pins the one thing left.
        "the_parents_indented_block_survives_a_closed_quote",
        "        self._indented = False\n        self._paragraph = lazy",
        "        self._paragraph = lazy",
    ),
    # -- the paragraph model: a blank line is one boundary, not the only one --
    (
        # The whole of it: no leaf block closes a paragraph any more, so the
        # blank line goes back to being the only boundary. An indented example
        # written directly under a heading then scores as PROSE and nets against
        # deleted prose -- reproduced on the real file, deleting
        # web-interface-guidelines-review's Verification rule 5 while the file
        # SHRANK, with every check green.
        "no_leaf_block_closes_a_paragraph",
        "        if ATX_RE.match(body) or BREAK_RE.match(body):\n"
        "            return True",
        "        if False:\n            return True",
    ),
    (
        # Only the heading half. The same evasion one construct along, and the
        # reason the set is a set: patching the shape the last review happened
        # to try is what this module names as the fifth round of patching.
        "an_atx_heading_does_not_close_a_paragraph",
        r'ATX_RE = re.compile(r"^#{1,6}(?:[ \t].*)?$")',
        r'ATX_RE = re.compile(r"^(?!)")',
    ),
    (
        # A heading needs whitespace after its hashes, so `##Heading` and seven
        # hashes are paragraphs. Dropped, an ordinary `#comment` line inside a
        # worked example would close a paragraph that is still open.
        "a_heading_does_not_need_whitespace_after_its_hashes",
        r'ATX_RE = re.compile(r"^#{1,6}(?:[ \t].*)?$")',
        r'ATX_RE = re.compile(r"^#{1,6}.*$")',
    ),
    (
        # The thematic break half.
        "a_thematic_break_does_not_close_a_paragraph",
        r'BREAK_RE = re.compile(r"^([-*_])[ \t]*(?:\1[ \t]*){2,}$")',
        r'BREAK_RE = re.compile(r"^(?!)")',
    ),
    (
        # A break stops requiring the same character throughout, so `- * -` is
        # one -- and so is the start of any list whose marker repeats.
        "a_thematic_break_may_mix_its_characters",
        r'BREAK_RE = re.compile(r"^([-*_])[ \t]*(?:\1[ \t]*){2,}$")',
        r'BREAK_RE = re.compile(r"^[-*_][ \t]*(?:[-*_][ \t]*){2,}$")',
    ),
    (
        # The setext half -- which is also the `- ` case, because an empty item
        # cannot interrupt a paragraph and CommonMark reads that line as an
        # underline rather than as a marker.
        "a_setext_underline_does_not_close_a_paragraph",
        r'SETEXT_RE = re.compile(r"^(?:=+|-+)[ \t]*$")',
        r'SETEXT_RE = re.compile(r"^(?!)")',
    ),
    (
        # A setext underline stops needing a paragraph above it, so `===` with a
        # blank line over it -- a paragraph of its own to CommonMark -- closes
        # something that was never open and rescopes the line under it.
        "a_setext_underline_needs_no_paragraph_above_it",
        "        return self._paragraph and SETEXT_RE.match(body) is not None",
        "        return SETEXT_RE.match(body) is not None",
    ),
    (
        # The HTML blocks that begin and end on one line stop closing anything,
        # which is the heading evasion spelled `<!-- x -->`. Reached now by
        # denying types 1 to 5 their own end condition, so the block that a
        # `<!-- x -->` opens never closes and swallows every line after it back
        # into the prose scope.
        "a_one_line_html_block_does_not_close_a_paragraph",
        "        return closer.search(body) is not None",
        "        return False",
    ),
    (
        # The other direction: an HTML block stops having to CLOSE on its line,
        # so `<div>` closes the paragraph and the indented line under it -- the
        # HTML block's own content to CommonMark -- moves into the code scope.
        # Reached now by ending types 6 and 7 on their opening line instead of
        # at the blank line that really ends them.
        "an_html_block_need_not_close_on_its_own_line",
        "            return not body.strip()",
        "            return True",
    ),
    (
        # THE ROUND-9 REGRESSION ITSELF: only the OPENER is modelled and the
        # block is not, so every line inside an open `<table>` or `<div>` still
        # reaches the paragraph rules. A `<!-- x -->` or a `## heading` in there
        # closes a paragraph CommonMark says is not there, and the indented line
        # under it moves into the code scope -- so a change that ADDED a line
        # and removed none fires the gate, whose only remedy is a ledger row
        # asserting N words are safe to lose when none were lost. A false entry
        # in a permanent append-only record is the one thing the hatch must
        # never require.
        "an_html_block_that_stays_open_is_not_modelled",
        "                self._html = None if self._html_ends(kind, body) else kind",
        "                self._html = None",
    ),
    (
        # An open HTML block stops outranking a quote marker, so a `> ` line
        # inside a `<div>` -- that block's own HTML to CommonMark -- is peeled
        # into a container that does not exist, and the rest of the block is
        # read at a depth that does not describe it.
        "an_open_html_block_does_not_outrank_a_quote_marker",
        "        return self._fence.open or self._html is not None",
        "        return self._fence.open",
    ),
    (
        # Type 7 stops being the exception, so a complete tag alone on a line
        # interrupts a paragraph. Every line under an ordinary sentence that
        # happens to end in a tag is then swallowed into a block that CommonMark
        # never opened.
        "every_html_block_may_interrupt_a_paragraph",
        "            return kind if interrupts or not self._paragraph else None",
        "            return kind",
    ),
    (
        # The other half: NOTHING may interrupt a paragraph, so the five blocks
        # that begin and end on one line stop closing one when it is open --
        # the same defect as the first entry above, reached through the rule
        # that is about the line rather than the rule that is about the block.
        "no_html_block_may_interrupt_a_paragraph",
        "            return kind if interrupts or not self._paragraph else None",
        "            return kind if not self._paragraph else None",
    ),
    (
        # Start condition 6 stops being CommonMark's list of tag names, so any
        # tag at all opens a block that runs to the next blank line -- and the
        # lines under `<span> and more words here` leave the code scope.
        "any_tag_name_opens_a_type_6_block",
        r'    (re.compile(rf"^</?(?:{HTML_BLOCK_NAMES})(?=\s|/?>|$)", re.I), None, True),',
        r'    (re.compile(r"^</?[A-Za-z]", re.I), None, True),',
    ),
    (
        # Start condition 7 stops requiring the tag to be the WHOLE line, so an
        # ordinary sentence ending in `<span>x</span>` opens a block and every
        # line under it is read as that block's HTML.
        "a_complete_tag_need_not_be_alone_on_its_line",
        r'    (re.compile(rf"^(?:{HTML_TAG})[ \t]*$"), None, False),',
        r'    (re.compile(rf"^(?:{HTML_TAG})"), None, False),',
    ),
    (
        # The lazy-continuation guard. A line indented past the threshold with a
        # paragraph open is that paragraph's wrapped text, and no block can be
        # spelled inside one -- so `    ## H` under a paragraph is four words of
        # prose, not a heading, and `    <!-- x -->` is three. Dropped, both
        # close the paragraph and rescope everything under it.
        "a_leaf_block_may_be_spelled_inside_a_wrapped_line",
        "        if indent < self._threshold():\n            body = line[indent:]",
        "        if True:\n            body = line[indent:]",
    ),
    (
        # An item with nothing on its opening line opens a paragraph again, so a
        # code block indented under `- ` reads as that item's wrapped text.
        "an_empty_list_item_opens_a_paragraph",
        "            self._paragraph = not empty",
        "            self._paragraph = True",
    ),
    (
        # ...and the column half of the same rule: an empty item's content
        # column stops being the marker plus one, so `-    ` measures the four
        # spaces from column 5 and hides a block that CommonMark reads at 6.
        "an_empty_list_items_content_column_follows_its_gap",
        "                + (1 if empty or not 1 <= gap <= CODE_INDENT else gap)",
        "                + (gap if 1 <= gap <= CODE_INDENT else 1)",
    ),
    (
        # A line that closed a paragraph goes on to be read as a list marker
        # too, so `- ` under a paragraph pushes a content column that raises the
        # threshold and re-hides the block the setext rule just exposed.
        "a_closing_leaf_block_is_also_read_as_a_list_marker",
        "            if self._closes(body):\n                self._paragraph = False\n"
        "                return False\n        self._paragraph = True",
        "            if self._closes(body):\n                self._paragraph = False\n"
        "            else:\n                self._paragraph = True\n"
        "        else:\n            self._paragraph = True",
    ),
    (
        # Replacements stop offsetting removals, so every reword and typo fix
        # scores as loss. This is the false-positive direction: the gate turns
        # into noise and people route around it.
        "gains_ignored",
        "            self.scopes[name] = sum((b - a).values()) - sum((a - b).values())",
        "            self.scopes[name] = sum((b - a).values())",
    ),
    # -- scope of the gate --------------------------------------------------
    (
        # Every markdown file becomes a SKILL.md. A trimmed README then fails
        # the gate with a message calling it a SKILL.md and a ledger row for a
        # skill named "" -- unusable, and the false-positive direction again.
        "skill_glob_matches_any_md",
        r'SKILL_GLOB_RE = re.compile(r"^skills/[^/]+/SKILL\.md$")',
        r'SKILL_GLOB_RE = re.compile(r".*\.md$")',
    ),
    (
        # Renames stop being paired, so a skill renamed in the same change that
        # cuts it drops out of both sides of the comparison and the gate prints
        # OK over a deletion it never looked at.
        "rename_pairing_removed",
        '        "diff", "--name-status", "-z", "--find-renames=25%", base, head, "--", "skills"',
        '        "diff", "--name-status", "-z", "--no-renames", base, head, "--", "skills"',
    ),
    (
        # Paths come back quoted, as the tab-and-newline format delivers any
        # path with a byte outside printable ASCII. A quoted path matches no
        # glob here, so the file leaves the comparison and the run prints OK
        # over a deletion it never opened and never named. Written as the
        # quoting rather than as the missing `-z`, so only the behaviour is
        # mutated and not the parser around it.
        "quoted_paths_drop_out_of_the_comparison",
        '    fields = [f for f in out.split("\\0") if f]',
        '    fields = [f if f.isascii() else \'"%s"\' % f for f in out.split("\\0") if f]',
    ),
    (
        # A blob git named that will not come back is dropped in silence again,
        # so the count in the success line stops meaning what it says.
        "unreadable_blobs_dropped_in_silence",
        "            if got is None:\n                self.unreadable.append((rev, path))",
        "            if False:\n                self.unreadable.append((rev, path))",
    ),
    (
        # Unchanged files enter the comparison, so the success line reports
        # every skill in the repo as changed on a one-file pull request.
        "collect_includes_unchanged_files",
        "        if before != after:\n            self.cases[new] = (before, after)",
        "        self.cases[new] = (before, after)",
    ),
    (
        # The base becomes the trunk TIP rather than the merge base, so main's
        # own edits are charged to this branch and the number the author is
        # told to declare is not the number CI will demand.
        "base_defaults_to_the_trunk_tip",
        '        got = _git("merge-base", trunk, "HEAD")',
        '        got = _git("rev-parse", trunk)',
    ),
    # -- the escape hatch ---------------------------------------------------
    (
        # The ledger becomes a standing exemption: a row merged to main once
        # excuses every later deletion from that skill, silently.
        "ledger_not_scoped_to_the_change",
        "        self.added = (\n"
        "            collections.Counter() if self.withdrawn else self.declared\n"
        "        )",
        "        self.added = collections.Counter(\n"
        '            {(s[1], s[2]): n for s, n in head.items() if s[0] == "row"}\n'
        "        )",
    ),
    (
        # The append-only rule deleted, so a row taken back out of the ledger
        # costs nothing. An edit is a withdrawal plus an addition, so this
        # hands a free declaration to an edit of ANY column of an inherited
        # row -- the count worst of all, where one character covers any number
        # the author cares to type.
        "ledger_credits_rows_a_change_withdrew",
        "        self.added = (\n"
        "            collections.Counter() if self.withdrawn else self.declared\n"
        "        )",
        "        self.added = self.declared",
    ),
    (
        # The append-only rule narrowed to "the ledger got longer", which is
        # the near-miss fix: it stops a bare edit, and one throwaway row buys
        # it back. The row that grows the total and the row that covers the cut
        # are then allowed to be different rows.
        "ledger_void_replaced_by_a_growing_row_count",
        "        self.added = (\n"
        "            collections.Counter() if self.withdrawn else self.declared\n"
        "        )",
        "        self.added = (\n"
        "            self.declared\n"
        "            if sum(head.values()) > sum(base.values())\n"
        "            else collections.Counter()\n        )",
    ),
    (
        # THE CLASS, as a mutation. Slots stop being total: a line the parser
        # cannot read stops occupying one, so the cardinality is a property of
        # the parse again and every acceptance predicate is a staging slot --
        # park a row where it does not parse, make it parse here, get a free
        # declaration while the covering row sits in the diff as context.
        "inert_lines_stop_occupying_a_slot",
        '            slots[_declaration(line) or ("line", line)] += 1',
        "            row = _declaration(line)\n"
        "            if row:\n"
        "                slots[row] += 1",
    ),
    (
        # The other half of the same class: lines OUTSIDE the table stop being
        # slots, so the table's extent becomes free to move. Deleting the prose
        # line that ended it publishes every row below at no cost.
        "lines_outside_the_table_stop_occupying_a_slot",
        "            else:\n"
        '                slots[("line", line)] += 1\n'
        "        elif LEDGER_RULE_RE.match(line):",
        "            else:\n"
        "                pass\n"
        "        elif LEDGER_RULE_RE.match(line):",
    ),
    (
        # A line the parser cannot read ends the table again, so a malformed
        # row hides every row beneath it and fixing its third cell publishes
        # all of them at once.
        "an_unparsable_row_ends_the_table",
        '        if in_table and not line.startswith("|"):',
        "        if in_table and not _declaration(line) and not "
        "LEDGER_RULE_RE.match(line):",
    ),
    (
        # A second header re-opens parsing, so a table anywhere in the document
        # is live and the ledger's own "that table only" is false again.
        "a_second_header_reopens_the_table",
        "            if not seen_table and LEDGER_HEADER_RE.match(line):",
        "            if LEDGER_HEADER_RE.match(line):",
    ),
    (
        # The header anchor closes at three columns again. Adding a fourth to
        # the table then stops the parser finding it at all -- every row goes
        # silent and nobody can open the hatch.
        "header_anchor_closed_at_three_columns",
        r'LEDGER_HEADER_RE = re.compile(r"^\|\s*skill\s*\|\s*words\s*\|\s*why\s*\|", re.I)',
        r'LEDGER_HEADER_RE = re.compile(r"^\|\s*skill\s*\|\s*words\s*\|\s*why\s*\|\s*$", re.I)',
    ),
    (
        # The reason goes back into the row's identity. Under the append-only
        # rule that no longer manufactures a declaration -- it voids one: a
        # typo fix to an inherited row reads as that row withdrawn, so a
        # copyedit to somebody else's old row kills the author's own genuine
        # declaration in the same pull request.
        "ledger_rows_keyed_on_their_reason_again",
        '        return ("row", skill, int(count))',
        '        return ("row", skill, int(count), reason)',
    ),
    (
        # The failure stops naming the withdrawal that caused it. The author is
        # then looking at a ledger row that covers their cut and a gate that
        # fails anyway with no reason given -- which is how a gate stops being
        # read and starts being routed around.
        "withdrawal_not_explained_in_the_message",
        "            if ledger.withdrawn\n            else \"\"",
        '            if False\n            else ""',
    ),
    (
        # "Rows stay after they merge" goes back to being asserted and enforced
        # nowhere, so a change that empties the ledger while touching no
        # SKILL.md is green.
        "removed_rows_stop_being_a_finding",
        "    if ledger.lost_rows:",
        "    if False:",
    ),
    (
        # The count stops binding. A row can then be written blind, and the
        # size of the cut never reaches the reviewer's eye.
        "ledger_count_ignored",
        "    return any(s == skill and c >= net for s, c in added)",
        "    return any(s == skill for s, c in added)",
    ),
    (
        # The count binds exactly instead of as a floor, so any later commit in
        # the pull request that ADDS words invalidates a correct declaration and
        # demands a fresh number -- a review round breaks the gate.
        "ledger_count_must_match_exactly",
        "    return any(s == skill and c >= net for s, c in added)",
        "    return any(s == skill and c == net for s, c in added)",
    ),
    (
        # Rows lose their multiplicity and their reason, so a skill that has
        # already declared a cut of this size can never declare another. The
        # author follows the printed instruction, git shows the row added by
        # their change, and the gate fails anyway -- an escape hatch that
        # cannot be opened is a bypass with extra steps.
        "ledger_rows_lose_their_multiplicity",
        '            slots[_declaration(line) or ("line", line)] += 1',
        '            slots[_declaration(line) or ("line", line)] = 1',
    ),
    (
        # An undeclared declaration starts counting -- a row with no reason.
        "ledger_reason_not_required",
        '    if not reason.strip("- ") or REASON_PLACEHOLDER in reason:',
        "    if False:",
    ),
    (
        # The unfilled placeholder starts counting, so the hatch becomes
        # automatic: paste the row the failure printed, ship, say nothing.
        "ledger_placeholder_accepted",
        'if not reason.strip("- ") or REASON_PLACEHOLDER in reason:',
        'if not reason.strip("- "):',
    ),
    (
        # Code stops being read in the ledger, in either spelling, so its own
        # worked example -- a filled-in table printed in a fence or indented --
        # parses as a live declaration. The hatch could then be used while the
        # table a reader actually reads stayed empty, which is the whole point
        # of it.
        "ledger_code_not_read",
        "        if coded or commented:",
        "        if commented:",
    ),
    (
        # Only the fenced spelling is read, which is how it shipped. An indented
        # example carries the FIRST `| skill | words | why |` in the document,
        # so it takes the table and the real one below it goes dead -- a row
        # added exactly where the ledger says declares nothing.
        "ledger_indented_code_not_read",
        "    code = Code()",
        "    code = Fence()",
    ),
    (
        # HTML comments stop being read, so a commented-out draft of the table
        # declares for real.
        "ledger_comments_not_read",
        "        if coded or commented:",
        "        if coded:",
    ),
    (
        # Parsing stops being anchored to the table, so any pipe-shaped line
        # anywhere in the document declares a removal.
        "ledger_not_anchored_to_the_table",
        "        elif not in_table:",
        "        elif False:",
    ),
    (
        # A blank line ends the table again. The ledger's table is the last
        # thing in the file, so a row pasted after a blank separator goes
        # unread and the failure reprints the row the author just wrote -- an
        # escape hatch that cannot be opened is a bypass with extra steps.
        "a_blank_line_ends_the_table",
        "        if not line:\n"
        "            continue  # a blank line carries no identity and declares "
        "nothing",
        "        if not line:\n            in_table = False\n            continue",
    ),
    # -- the message --------------------------------------------------------
    (
        # Replaced blocks become quotable again, so "Gone:" starts quoting
        # passages that are still in the file. An author whose first encounter
        # with a gate is a message wrong about their own diff routes around it.
        "excerpt_quotes_replaced_blocks",
        '            if tag != "delete":',
        '            if tag not in ("delete", "replace"):',
    ),
    (
        # The breakdown lists only the parts that fired, so it no longer sums
        # to the total the author is told to write into the ledger -- leaving
        # two numbers in one message and no way to tell which is real.
        "breakdown_omits_parts_below_their_floor",
        "            for n, v in sorted(self.scopes.items(), key=lambda kv: -kv[1])",
        "            for n, v in sorted(self.over.items(), key=lambda kv: -kv[1])",
    ),
    (
        # The paste-the-row loop, restored. The failure hands over a row whose
        # reason is the placeholder `_declaration` rejects; with the drafted
        # state unreachable, an author who pastes it gets the same run back
        # BYTE FOR BYTE, with nothing in it naming the placeholder. An escape
        # hatch that cannot be opened is a bypass with extra steps, and this is
        # the path every first-time failure takes.
        "a_pasted_placeholder_row_is_not_noticed",
        "    if printed in after:",
        "    if False:",
    ),
    (
        # The drafted remedy stops being tested and goes back to being
        # asserted, so "replace the placeholder with the reason" is offered to
        # an author for whom it clears nothing -- one whose change also took a
        # line out of the ledger, where no row they add counts at all. That is
        # the same defect one layer along: an instruction that does not reach
        # green.
        "the_drafted_remedy_is_asserted_rather_than_tested",
        "        if declares(LedgerDiff(before, filled).added, skill, net):\n"
        "            return DRAFTED",
        "        return DRAFTED",
    ),
    (
        # The failure goes back to printing "add this row" over a ledger that
        # already shows the reader a row covering the cut -- the message being
        # wrong about the reader's own diff, which `Loss.excerpt` names as how
        # a gate stops being read.
        "a_row_is_printed_over_one_the_ledger_already_shows",
        "    if declares(parse_ledger(after), skill, net):\n"
        "        return STANDING",
        "    if False:\n        return STANDING",
    ),
    (
        # The guidance stops being read off the failures being printed and
        # closes with the first remedy every time, which is the defect as it
        # shipped: "Add the row printed above ..." over a file whose
        # frontmatter could not be located, over a blob that would not come
        # back, and over a ledger the change rewound -- none of which print a
        # row at all.
        "the_guidance_closes_the_same_way_whatever_failed",
        "        for marker, line, promises in REMEDIES\n"
        "        if any(marker in e for e in errors)",
        "        for marker, line, promises in REMEDIES[:1]\n        if True",
    ),
    (
        # The promise stops being held back. "and this gate passes" is then
        # printed to an author whose change took something out of the ledger,
        # for whom no row they add counts at all -- the false remedy this block
        # already had one branch to avoid, on a second mode.
        "green_is_promised_while_a_withdrawal_stands",
        "        line + (HELD if held else PASSES) if promises else line",
        "        line + PASSES if promises else line",
    ),
    (
        # The promise is held back for the ledger's two modes alone, as it
        # shipped, so "and this gate passes" is printed to an author whose run
        # also carries a file this gate could not scope or could not read. They
        # add the row, the second file still fails, and they get exit 1 for
        # doing exactly what the guidance said.
        "green_is_promised_over_a_failure_the_remedy_does_not_answer",
        "        for marker, _line, promises in REMEDIES\n        if not promises",
        "        for marker, _line, promises in REMEDIES\n"
        "        if marker in (SLOTS_WITHDRAWN, LEDGER_REWOUND)",
    ),
    (
        # The two ways a covering row can fail to count collapse into one
        # remedy, so an author whose own row was voided by a withdrawal is told
        # to write a second row -- which is voided too. Putting the ledger back
        # is the only thing that clears it.
        "a_voided_row_and_an_inherited_row_share_one_remedy",
        "        INHERITED_ROW,\n"
        "        f\"Declare the cut named above as a NEW row in {LEDGER}. The row already \"",
        "        STANDING_INTRO,\n"
        "        f\"Declare the cut named above as a NEW row in {LEDGER}. The row already \"",
    ),
]


def _scratch(tmp_path: Path, source: str) -> Path:
    """A runnable copy of the suite against `source` as the detector."""
    tests = tmp_path / "tests"
    tests.mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "check_prose_retention.py").write_text(
        source, encoding="utf-8"
    )

    # The suite asserts the shipped ledger declares nothing; it resolves that
    # path relative to itself, so the scratch tree needs the real file.
    (tmp_path / "docs").mkdir()
    shutil.copy(LEDGER, tmp_path / "docs" / "prose-removals.md")

    # And it asserts that reading indented code moves no line in any SKILL.md
    # this catalog ships, resolved the same way. Copied rather than skipped when
    # absent: a case that skips itself when its subject is missing reports green
    # over a comparison it did not make, which is the defect the detector under
    # test exists to stop.
    shutil.copytree(SKILLS, tmp_path / "skills")

    shutil.copy(SUITE, tests / SUITE.name)
    shutil.copytree(FIXTURES, tests / "fixtures" / "prose-retention")
    (tests / "conftest.py").write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))\n",
        encoding="utf-8",
    )
    return tests


def _run_suite(tests: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(tests),
            "-q",
            "-p",
            "no:cacheprovider",
            *extra,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=tests.parent,
    )


def test_control_the_unmutated_detector_is_green(tmp_path):
    """The scratch harness can report success. Without this, every red below
    is equally explained by a broken harness.
    """
    tests = _scratch(tmp_path, DETECTOR.read_text(encoding="utf-8"))
    result = _run_suite(tests)
    assert result.returncode == 0, (
        "the unmutated suite is not green in the scratch tree, so nothing "
        f"below is evidence:\n{result.stdout}\n{result.stderr}"
    )


def test_every_mutation_is_named_once():
    """Two entries under one name would report as one parametrized case and
    quietly halve the evidence.
    """
    names = [m[0] for m in MUTATIONS]
    assert len(names) == len(set(names)), sorted(
        n for n in names if names.count(n) > 1
    )


@pytest.mark.parametrize("name,old,new", MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_mutation_turns_the_suite_red(tmp_path, name, old, new):
    source = DETECTOR.read_text(encoding="utf-8")

    assert source.count(old) == 1, (
        f"mutation {name!r} does not match the detector exactly once "
        f"({source.count(old)} matches). The detector changed shape; update "
        "the mutation so it keeps testing what it claims to."
    )
    mutated = source.replace(old, new)
    assert mutated != source, f"mutation {name!r} did not land"

    tests = _scratch(tmp_path, mutated)
    result = _run_suite(tests, "-x")
    assert result.returncode != 0, (
        f"mutation {name!r} was applied and the suite still passed, so nothing "
        f"in it constrains that behaviour:\n{result.stdout}"
    )
