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
       worked anti-pattern example gone.

   Both are one defect -- a gain somewhere cheap paying for a loss somewhere
   expensive -- so both get one fix rather than a patch each.

Stdlib only.

Inputs (main): a base and a head git revision, plus the repo at cwd.
Outputs (stdout): one `::error file=<path>::<msg>` GitHub annotation per
undeclared removal, then a guidance block.

Exit codes:
  0  no undeclared prose removal
  1  undeclared prose removal, or the comparison could not be made
"""

from __future__ import annotations

import argparse
import collections
import difflib
import re
import subprocess
import sys
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

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

# ```lang or ~~~ , indented or not. A block closes on the same character.
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})")

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
# every revision of every SKILL.md in this repository's history (159
# file-revisions, across every commit touching one) gives, per scope, these
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
# Re-run the replay before moving any of these. The argument is the empty band,
# not the digit:
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


def split_scopes(text: str) -> dict[str, str]:
    """Cut a SKILL.md into the three parts that are scored separately.

    The frontmatter boundary is `validate_skills.py`'s own -- it measures the
    body as `content[m.end():]` against the size cap, so that is exactly where
    the byte pressure stops and the free-padding surface begins.
    """
    m = FRONTMATTER_RE.match(text)
    frontmatter, body = (text[: m.end()], text[m.end() :]) if m else ("", text)

    prose: list[str] = []
    code: list[str] = []
    fence: str | None = None
    for line in body.splitlines():
        marker = FENCE_RE.match(line)
        if fence is None:
            if marker:
                fence = marker.group(1)[0] * 3
                code.append(line)
            else:
                prose.append(line)
        else:
            code.append(line)
            if marker and marker.group(1)[0] * 3 == fence:
                fence = None

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
        b_scopes, a_scopes = split_scopes(before), split_scopes(after)

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
# Three rules keep it a declaration rather than a standing exemption, and each
# one is a hole somebody drove through in review:
#
#   ONLY A ROW THE CHANGE ITSELF ADDS COUNTS. A row inherited from the base is
#   somebody else's declaration about somebody else's deletion, and honouring
#   it rebuilds exactly the standing blanket exemption this repository already
#   removed once from the size gate: a grandfather row exempts one skill
#   visibly in review, but `limitBytes` was one line and exempted all 46 at
#   once, silently.
#
#   THE COUNT HAS TO COVER THE CUT. That is not busywork -- it is what stops a
#   row being written blind, and it puts the magnitude in the diff where a
#   reviewer reads it. It is a floor, not an equality: a later commit in the
#   same PR that ADDS words shrinks the net, and demanding a fresh number on
#   every review round would make the ordinary life of a pull request the thing
#   that breaks the gate. Understating still fails -- you cannot declare 5 to
#   cover a cut of 500.
#
#   ROWS COUNT WITH MULTIPLICITY, ON (SKILL, COUNT) -- NOT ON THE REASON TEXT.
#   Two removals of the same size from the same skill are two declarations, so
#   a row keyed as a SET on (skill, count) alone deadlocked the second one:
#   the author followed the printed instruction exactly, the row was visibly
#   added by their change, and the gate failed anyway and reprinted the same
#   instruction. An escape hatch that cannot be opened is a bypass with extra
#   steps -- and this was the default case, not an exotic one, since 35 of the
#   49 skills carry two or more bullets of identical word length. But the
#   reason cannot be part of the KEY either: keyed on the whole row, editing an
#   inherited row's wording -- a typo fix, a trailing full stop -- gave it a
#   fresh key, so the edit alone read as a declaration and covered an
#   unrelated cut nobody wrote a reason for. What has to grow between the two
#   ledgers is the COUNT of rows at that size, not the text of any one of
#   them, which is why the multiset is counted on (skill, count) with the
#   reason dropped, rather than on the full (skill, count, reason) tuple.
#
# The failure prints the exact row to paste, so paying it costs one copy plus a
# reason.

LEDGER_ROW_RE = re.compile(r"^\|([^|]+)\|([^|]+)\|(.+?)\|?\s*$")
LEDGER_HEADER_RE = re.compile(r"^\|\s*skill\s*\|\s*words\s*\|\s*why\s*\|\s*$", re.I)
LEDGER_RULE_RE = re.compile(r"^\|[\s:|-]+\|\s*$")

# The reason field the error message hands you, unfilled. Rejected on sight:
# the hatch is meant to be cheap, not automatic, and the one thing it has to
# cost is somebody deciding the words are safe to lose. A row pasted straight
# from the failure declares nothing.
REASON_PLACEHOLDER = "<why these words are gone>"


def _uncode(text: str) -> str:
    """Drop fenced blocks and HTML comments from the ledger before parsing.

    The ledger documents its own row format, in a fence, directly above the
    table. Without this that example parsed as a live declaration -- so the
    hatch could be used while the table a reader actually reads stayed empty,
    which defeats the entire point of leaving a record.
    """
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    out: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        marker = FENCE_RE.match(line)
        if fence is None:
            if marker:
                fence = marker.group(1)[0] * 3
                continue
            out.append(line)
        elif marker and marker.group(1)[0] * 3 == fence:
            fence = None
    return "\n".join(out)


def parse_ledger(text: str) -> collections.Counter[tuple[str, int, str]]:
    """Every declaration row in the ledger table, counted with multiplicity.

    Only rows inside the `| skill | words | why |` table count -- parsing is
    anchored to that header and stops at the end of the table, so a row written
    anywhere else in the document (in a fence, in a comment, in an example)
    declares nothing. The point of the hatch is the record it leaves; a
    declaration a reader of the ledger would never see is not one.

    Rows whose reason is blank, or still the pasted placeholder, are ignored:
    an undeclared declaration is not one either.
    """
    found: collections.Counter[tuple[str, int, str]] = collections.Counter()
    in_table = False
    for raw in _uncode(text).splitlines():
        line = raw.strip()
        if LEDGER_HEADER_RE.match(line):
            in_table = True
            continue
        if not in_table:
            continue
        if LEDGER_RULE_RE.match(line):
            continue
        m = LEDGER_ROW_RE.match(line)
        if not m:
            in_table = False  # the table ended; what follows it is prose
            continue
        skill, count, reason = (g.strip().strip("`") for g in m.groups())
        if not reason.strip("- ") or REASON_PLACEHOLDER in reason:
            continue
        try:
            found[(skill, int(count), reason)] += 1
        except ValueError:
            continue
    return found


def ledger_row(skill: str, net: int) -> str:
    return f"| {skill} | {net} | {REASON_PLACEHOLDER} |"


def rows_by_size(
    declarations: collections.Counter[tuple[str, int, str]],
) -> collections.Counter[tuple[str, int]]:
    """Collapse parsed rows onto `(skill, count)`, dropping the reason.

    `parse_ledger` keys on the whole row -- reason included -- because that is
    what lets a reader see two declarations of the same size as two rows
    rather than one. But the reason must not be part of what makes a row
    NEW: subtracting one `(skill, count, reason)` Counter from another treats
    any edit to a row's wording as that row vanishing and an unrelated one
    appearing, so a one-character fix to an inherited row's reason reads as a
    fresh declaration -- covering whatever this change actually cut, under
    wording nobody wrote for it. Collapsing first means the thing that has to
    grow between the two ledgers is the COUNT of rows at that size, which is
    the only thing "added a row" can honestly mean.
    """
    collapsed: collections.Counter[tuple[str, int]] = collections.Counter()
    for (skill, count, _reason), n in declarations.items():
        collapsed[(skill, count)] += n
    return collapsed


def declares(
    added: collections.Counter[tuple[str, int]], skill: str, net: int
) -> bool:
    """Does a row this change added cover a loss of `net` words from `skill`?"""
    return any(s == skill and c >= net for s, c in added)


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
    added = rows_by_size(parse_ledger(ledger_after)) - rows_by_size(
        parse_ledger(ledger_before)
    )
    errors: list[str] = []

    for path in sorted(cases):
        before, after = cases[path]
        loss = Loss(before, after)
        if not loss:
            continue

        skill = Path(path).parent.name
        if declares(added, skill, loss.net):
            continue

        errors.append(
            f"::error file={path}::this SKILL.md lost {loss.net} words that "
            f"nothing in the same part of it replaced ({loss.breakdown()}). "
            f"Rewrapping, reordering, moving a line and converting `{skill}` "
            f"to a markdown link all score zero here, so this is content, not "
            f"layout. Each part is scored on its own, so words added to the "
            f"frontmatter or to a code block cannot pay for prose that went "
            f"missing. Gone: {loss.excerpt()}. If the removal is deliberate, "
            f"add this row to {LEDGER} in this same change: "
            f"{ledger_row(skill, loss.net)}"
        )

    return errors


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

    def pair(self, base: str, old: str, head: str, new: str) -> None:
        """Record one before/after comparison, whatever the paths were called.

        One site, so the rename branch and the ordinary-modification branch
        cannot drift apart -- and so "did this file actually change?" is a
        single decision rather than a promise made twice.
        """
        before, after = _show(base, old), _show(head, new)
        if before is None or after is None:
            return
        if before != after:
            self.cases[new] = (before, after)


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
        "diff", "--name-status", "--find-renames=25%", base, head, "--", "skills"
    )
    if got.returncode != 0:
        return diff

    for line in got.stdout.splitlines():
        fields = line.split("\t")
        status, paths = fields[0], [p for p in fields[1:] if p]
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

    errors = run(diff.cases, ledger_before, ledger_after)

    if errors:
        for e in errors:
            print(e)
        print(f"::error::{len(errors)} SKILL.md file(s) lost prose undeclared")
        print(
            f"\nA size limit and a link sweep both push in the same direction: "
            f"delete something.\nThat is how three skills lost real content on "
            f"a change whose whole purpose\nwas strengthening the links between "
            f"them, with every check green.\n\nIf you are here because a file "
            f"would not fit, rewrite the section tighter rather\nthan cutting "
            f"it -- a rewrite that says the same thing in fewer words scores "
            f"zero\nhere and needs no row. Reach for deletion second, not "
            f"first.\n\nDeleting prose is allowed. Doing it silently is not. "
            f"Add the row printed above\nto {LEDGER} in this same change and "
            f"this gate passes."
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
