#!/usr/bin/env python3
"""Validate every SKILL.md under skills/<name>/ (the `validate-skills` gate).

Called by `.github/workflows/validate-skills.yml` on PR + push to main.
Catches malformed frontmatter (missing name, missing description, name
mismatch with directory) before it ships to skills.sh, where downstream
consumers (clud-bug, agent runtimes via skills CLI) would silently get
broken skills.

Also gates docs/placement-map.json (when present): valid JSON/shape, and its
`skills` keys reconciled 1:1 against skills/ directory names. This is what
makes the placement-map guide's claim ("the map is kept in sync") actually
true instead of aspirational.

Three listings of the catalog have to agree with the tree, and each is
reconciled here (#229): the placement map 1:1 by key; the generated directory
skill by byte-identical re-render, plus the cross-check that a SUPERSEDED
skill is filed under `deprecated`; and README.md by membership only, since its
purpose column is prose no generator should flatten.

This file was a `python <<'PY'` heredoc inside the workflow until it was
extracted verbatim so it could be imported and characterized by
`tests/test_validate_skills.py`. Every rule, message string and exit code
below is the heredoc's, unchanged -- the gate's behaviour is now pinned by
tests rather than by re-reading YAML.

Stdlib + PyYAML only (the workflow pip-installs pyyaml; nothing else).

Inputs:
  cwd  ROOT and the placement map are BOTH cwd-relative, exactly as the
       heredoc had them. Run from the repo root. `main()`'s coverage guard
       is what stops a run from the wrong directory passing vacuously.

Outputs (stdout):
  One `::error file=<path>::<msg>` GitHub annotation per validation error,
  then a `::error::<N> skill validation errors` summary -- or a single
  `OK: <N> skills validated cleanly.` line.

Exit codes:
  0  Every SKILL.md (and the placement map, if present) validated cleanly
     AND the coverage guard agrees the run actually saw the tree.
  1  Any validation error, either infra-fatal condition (no skills/ dir, no
     skill subdirectories), or a coverage-guard failure.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.parse
from pathlib import Path

import yaml

# The directory generator. Imported rather than shelled out to so the gate
# renders in-process and compares the WHOLE body: the directory is a pure
# function of this checkout and reads no git history, so nothing weaker than
# byte identity is needed and nothing weaker is used.
#
# `.github/scripts` is sys.path[0] when this file is run as a script, and
# tests/conftest.py puts it there for the import path.
#
# The try/except is not defensive. Without it, deleting the generator takes
# the whole gate down with an uncaught ModuleNotFoundError traceback and no
# `::error file=` annotation -- so the one failure that means "the directory
# can no longer be verified at all" is the one CI renders least legibly.
try:
    import gen_skill_directory  # noqa: E402
except ImportError as _import_error:
    print(
        "::error file=.github/scripts/gen_skill_directory.py::the catalog directory "
        f"generator could not be imported ({_import_error}), so the committed "
        "directory cannot be re-rendered and compared. Every other rule below would "
        "still pass, and an unverifiable directory reads exactly like a verified one."
    )
    sys.exit(1)
import skill_version

ROOT = Path("skills")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

# protocol SPEC.md §1.10.1 "Frontmatter (NORMATIVE)" -- enums and
# shapes enforced below. Every key here is OPTIONAL in the
# frontmatter; unknown keys (and the RESERVED, definition-deferred
# `layer` / `status` / `superseded_by` keys) are always tolerated
# and never validated -- only the fields below are checked, and
# only when present.
NAME_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
# SPEC §1.10.1: `source: manual | logmind-derived | skills-sh | clud-bug-baseline`
SOURCE_VALUES = {"manual", "logmind-derived", "skills-sh", "clud-bug-baseline"}
# SPEC: `kind: rule | writing | design`
KIND_VALUES = {"rule", "writing", "design"}

# Skill body size. No exceptions, and the number lives HERE on
# purpose -- in code, changeable only by a reviewed edit to this file.
#
# It was briefly a JSON file carrying a `limitBytes` key plus a
# grandfather list. That is the worse design: a grandfather row
# exempts one skill visibly in review, but `limitBytes` is one line
# and exempts all 46 at once, silently. Closing the small door while
# leaving the large one open relocates the escape rather than
# shutting it.
#
# There is no exception path because there is nothing to except.
# Past this size a consuming reviewer truncates the body when
# building its prompt, so the tail never reaches the model while the
# author sees a complete file and a green build. An oversized skill
# is already broken for its reader; blessing it does not make it
# work, it only makes the breakage approved.
#
# 8192 is clud-bug's own DEFAULT_MAX_SKILL_BYTES
# (src/core/prompt-builder.ts), whose comment ties it to SPEC 1.10.
# Its shipped workflow templates override this DOWN to 4000, so a
# repo on an unmodified template truncates earlier -- clud-bug#301.
SIZE_LIMIT = 8192

# --- docs/placement-map.json gate ------------------------------------------
#
# The steward's placement map (docs/integrating-with-agent-skills.md
# "The placement map") claims it is the per-skill ground truth kept
# in sync with skills/. Make that claim real: validate shape + enums
# when the file is present, and reconcile its `skills` keys 1:1
# against the skills/ directory names (report missing/extra by
# name). Absence is tolerated (it may not exist yet / may be
# authored by a parallel agent) -- only presence-with-defects fails.

AUTHORING_HOME_RE = re.compile(r"^(catalog|undecided|repo-mirrored:[a-z0-9-]+)$")
DISTRIBUTION_VALUES = {"default-on", "opt-in", "catalog-only"}

# How the catalog announces a retirement. All three retired skills open their
# `description` with it, and no live skill does -- it is the first thing an
# agent reads, so it is the thing the directory has to agree with. Anchored by
# `.match()` (which starts at position 0) rather than by a `^` in the pattern:
# with both, neither can be tested, because removing either one leaves the
# other still anchoring. One owner for the anchoring, and a mutation proves it.
SUPERSEDED_RE = re.compile(r"SUPERSEDED\b")

# A README link to a skill, which is how the README names one. The table is
# still hand-written prose; this reconciles its MEMBERSHIP only -- see
# `readme_errors`.
README_SKILL_LINK_RE = re.compile(r"\(skills/([a-z0-9-]+)/SKILL\.md\)")

# --- markdown link integrity gate (skills/) ---------------------------------
#
# #234: `check-links` (the logmind-installed required status check) is blind
# to skills/ -- it walks docs/ only, so a merge gate reports green over the
# one directory the catalog exists to protect, and that green is
# indistinguishable from a real all-clear. Reproduced with a control in the
# issue: an identical broken link in a skill body passes; the same break in
# README.md is caught.
#
# Built HERE rather than routed through `.github/workflows/check-doc-links.yml`
# for two measured reasons (issue #234):
#   1. That workflow's Go linkchecker install hardcodes its roots, and its own
#      source defers config support -- setting `linkcheck.roots` is a silent
#      no-op, so it cannot be pointed at skills/ by configuration.
#   2. Its self-heal job can push commits to a PR branch with the instruction
#      "either remove the link line or fix the target path", aimed at a
#      `## Cross-references` block -- which silently deletes the content this
#      gate exists to protect, on the branch it is supposed to be protecting.
#
# SCOPE, decided and stated rather than left for a reader to infer: ONLY
# relative links are resolved against the filesystem. Absolute http(s) links
# are counted (`link_stats`) but never fetched -- network access from CI is
# flaky and slow, and a reference file's absolute GitHub URL legitimately
# 404s until ITS OWN PR merges (issue #234 names PR #233's three
# `references/` links as the live case); a checker that fetches would block
# its own PR. `main()` prints the scope line below unconditionally, so a
# reader of green output is told the bound rather than assuming "all links".
#
# Also handled, because a false positive here fires on every PR and is worse
# than the gap being closed:
#   - same-page anchors (`[x](#section)`) -- no path component, nothing to
#     resolve, never flagged;
#   - link-shaped text inside fenced code blocks and inline code spans (a
#     skill SHOWING markdown link syntax as an example) -- blanked out
#     before the link regex runs, so it is never seen as a real link;
#   - link-shaped text inside a CommonMark 4-SPACE-INDENTED code block, the
#     spelling with no fence to match against. `_indented_code_lines` reads
#     it directly rather than via a regex: whether a given 4-space indent
#     actually opens one depends on whether a paragraph is already open
#     (an indented block can never INTERRUPT one -- CommonMark) and on the
#     content column of whatever list item it may sit inside (measured FROM
#     that column, not from the left margin, so a nested bullet's own
#     wrapped continuation is never misread as its sibling's code). Getting
#     either wrong in the "blank real list prose" direction is worse than
#     this whole gate: it hides a real link inside ordinary text from every
#     check below, silently, rather than merely mis-scoping an example.
#     Checked against markdown-it-py over 60,000+ generated documents
#     (dev-time oracle only, never imported here): the dangerous direction
#     -- CommonMark says prose, this says code -- is 0/60,000; a difference
#     remains in the SAFE direction (this under-blanks a small number of
#     documents built from several coincident, deeply-nested restarting
#     list markers, none of which the shipping catalog's 49 SKILL.md files
#     contain even one instance of), which just narrows this gate's
#     coverage back toward the ORIGINAL false-positive risk on that shape
#     rather than opening a new one. Blockquoted content is explicitly OUT
#     OF SCOPE for indented-code detection, the same bound `FENCE_RE` above
#     already has (neither reads a `>` marker), and raw HTML blocks are not
#     modelled either -- a fence or an indented block written inside a
#     quote, or content that would only be excluded by tracking an open
#     HTML block, is not blanked by this gate at all.
#
# NOT checked: whether a `#fragment` heading actually exists in the target
# file. The control in #234 (and every case measured) is a missing FILE, not
# a missing heading; verifying headings too would need a markdown-heading
# parser per target file for a case nothing here has hit yet. Scope stated,
# not silently assumed.
#
# ALSO NOT checked: reference-style links (`[text][ref]` plus a `[ref]: url`
# definition elsewhere). `LINK_RE` below matches only the inline `(...)`
# form; no skill in this catalog uses the reference form today. A known
# bound, not an oversight -- stated here rather than left for the next
# reader to discover by a link that silently never gets resolved.

FENCE_RE = re.compile(r"^([ \t]*)(```|~~~).*?^\1\2[ \t]*$", re.DOTALL | re.MULTILINE)
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
ABSOLUTE_LINK_SCHEMES = ("http://", "https://", "mailto:")

# CommonMark's indent for a code block, and the tab stop it is measured
# after -- a tab-indented block is the same block, and leaving it unmeasured
# would be the same construct in a spelling `_indented_code_lines` cannot see.
CODE_INDENT = TAB_STOP = 4

# A line that opens (or is the same shape as) an ATX heading, a thematic
# break, or a setext heading underline -- the constructs `_indented_code_lines`
# needs to recognise because each interacts with an open paragraph or an open
# list differently. Definitions match check_prose_retention.py's own
# ATX_RE/BREAK_RE/SETEXT_RE/LIST_ITEM_RE byte for byte (that module's
# adjudication against markdown-it-py is the source for the shapes; this
# gate's needs are a strict subset of that module's, so it is reimplemented
# here rather than imported -- this gate stays Stdlib + PyYAML only, and a
# change to that module's own scoring logic must not silently change what
# gets blanked here).
_ATX_RE = re.compile(r"^#{1,6}(?:[ \t].*)?$")
_BREAK_RE = re.compile(r"^([-*_])[ \t]*(?:\1[ \t]*){2,}$")
_SETEXT_RE = re.compile(r"^(?:=+|-+)[ \t]*$")
_LIST_ITEM_RE = re.compile(r"^( *)([-*+]|\d{1,9}[.)])( +|$)")


def _indented_code_lines(text: str) -> set[int]:
    """1-based line numbers of `text` that open a CommonMark 4-space-indented
    code block.

    Assumes fenced blocks have ALREADY been blanked out of `text` (their
    backtick/tilde runs gone) -- see `_strip_code`, which runs `FENCE_RE`
    first for exactly this reason -- so no fence tracking happens here.

    Tracks two pieces of state a naive `^    ` regex does not: whether a
    PARAGRAPH is currently open (an indented block can never interrupt one,
    so the same four spaces right under an open paragraph are that
    paragraph's own wrapped text, not code), and a stack of enclosing LIST
    ITEM content columns (the four spaces are measured from there, not from
    the left margin, so a nested bullet's own continuation is never
    misread as its sibling's code).

    A line that LAZILY CONTINUES an open paragraph does not close any list
    it sits inside however shallow it is written -- only a line that would
    itself START a block ends a lazy continuation, and starting one
    requires meeting a column a lazy line does not have to meet. Within
    that: a heading or a thematic break is NOT eligible for lazy
    continuation at all (CommonMark lets either interrupt a paragraph
    outright, so a shallow one still closes the list it fails to indent
    into); a setext underline is the opposite -- it can never interrupt a
    paragraph, so a shallow one reached only by laziness stays literal
    continuation text rather than closing anything. And a list MARKER on a
    lazy-continuation line only opens a genuine new item if CommonMark
    would let it interrupt the paragraph it sits under: an ordered marker
    must start at 1, and no marker may open an empty item -- reading either
    one as real here leaves a phantom list column on the stack that
    outlives it and raises the threshold for a later, unrelated block.
    """
    lists: list[int] = []
    paragraph = False
    indented = False
    out: set[int] = set()

    for i, raw in enumerate(text.split("\n"), start=1):
        line = raw.expandtabs(TAB_STOP)

        if not line.strip():
            paragraph = False
            if indented:
                out.add(i)
            continue

        indent = len(line) - len(line.lstrip(" "))
        was_paragraph = paragraph
        indented = False
        threshold_before_pop = (lists[-1] if lists else 0) + CODE_INDENT

        lazy_ineligible = False
        if was_paragraph and indent < threshold_before_pop:
            probe = line[indent:]
            if _ATX_RE.match(probe) or _BREAK_RE.match(probe):
                lazy_ineligible = True
        if not was_paragraph or lazy_ineligible:
            while lists and indent < lists[-1]:
                lists.pop()

        threshold = (lists[-1] if lists else 0) + CODE_INDENT
        if not was_paragraph and indent >= threshold:
            indented = True
            out.add(i)
            continue

        body = line[indent:] if indent < threshold else line
        closes = False
        if indent < threshold:
            if _ATX_RE.match(body) or _BREAK_RE.match(body):
                closes = True
            elif (
                was_paragraph
                and indent >= (lists[-1] if lists else 0)
                and _SETEXT_RE.match(body)
            ):
                closes = True

        if closes:
            paragraph = False
            continue

        paragraph = True

        m = _LIST_ITEM_RE.match(line)
        if m:
            gap = len(m.group(3))
            empty = not line[m.end():].strip()
            marker = m.group(2)
            interrupts = marker[:-1] == "1" if marker[-1] in ".)" else True
            if was_paragraph and (empty or not interrupts):
                continue
            lists.append(
                len(m.group(1))
                + len(m.group(2))
                + (1 if empty or not 1 <= gap <= CODE_INDENT else gap)
            )

    return out


def _blank_out(match: re.Match) -> str:
    """Replace a matched span with same-length whitespace (newlines kept),
    so line numbers computed from the SCANNED text still line up with the
    original file -- deletion would shift every subsequent line number.
    """
    return re.sub(r"[^\n]", " ", match.group(0))


def _blank_lines(text: str, line_numbers: set[int]) -> str:
    """Blank whole LINES (whitespace, not deletion, so the split/join stays
    lossless and every line number after it is unchanged) at the given
    1-based numbers.
    """
    if not line_numbers:
        return text
    out = text.split("\n")
    for n in line_numbers:
        out[n - 1] = " " * len(out[n - 1])
    return "\n".join(out)


def _strip_code(text: str) -> str:
    """Blank fenced code blocks, then 4-space-indented code blocks, then
    inline code spans, so link-shaped text used as a documentation EXAMPLE
    is never read as a real link.

    Order matters twice over. Fences first: a fenced block can itself
    contain single backticks, so `INLINE_CODE_RE` would eat into it if run
    first, AND `_indented_code_lines` assumes fences are already gone (see
    its docstring) -- feeding it un-blanked fence markers would let its own
    (much narrower) fence-shaped checks misfire on them. Indented blocks
    before inline code: a `` ` `` inside a genuine indented block is the
    author's own text, not an inline-code delimiter, and blanking the
    block first removes it from `INLINE_CODE_RE`'s view entirely rather
    than relying on the regex to leave it alone.
    """
    scan = FENCE_RE.sub(_blank_out, text)
    scan = _blank_lines(scan, _indented_code_lines(scan))
    return INLINE_CODE_RE.sub(_blank_out, scan)


def _link_target(raw: str) -> str:
    """The URL/path portion of a `(...)` link destination, with an optional
    trailing `"title"` or `'title'` stripped off.
    """
    raw = raw.strip()
    m = re.match(r'^(\S+)(?:\s+["\'].*["\'])?$', raw)
    return m.group(1) if m else raw


def _iter_links(root: Path, errors: list[str] | None = None):
    """Yield (md_path, line_no, path_part, is_absolute) for every markdown
    link found under `root`, fenced code / inline code excluded and any
    `#fragment` split off. Same-page anchors (`[x](#foo)`, no path before
    the `#`) are never yielded -- there is nothing to classify or resolve.

    A file that cannot be READ -- non-UTF-8 content, or a dangling symlink
    ending `.md` -- has that failure appended to `errors` as a proper
    `::error file=` annotation and is then skipped, rather than letting the
    exception propagate. Uncaught, it would crash mid-generator and unwind
    through every caller's `for` loop, discarding whatever OTHER validation
    errors `run()`'s per-skill loop had already collected before printing an
    unhandled traceback instead of this gate's normal annotation form --
    still a non-zero exit (no false green), just an uglier and less useful
    one. `errors=None` (the default, and what `link_stats` passes) means
    "count what is readable and say nothing about the rest" -- safe only
    because `link_errors` below always passes its OWN list, so the failure
    is never silently dropped from every caller at once.
    """
    for md_path in sorted(root.glob("**/*.md")):
        try:
            text = md_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            if errors is not None:
                errors.append(
                    f"::error file={md_path}::could not read {md_path} to "
                    f"check its links: {e}"
                )
            continue
        scan = _strip_code(text)
        for m in LINK_RE.finditer(scan):
            target = _link_target(m.group(1))
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            is_absolute = path_part.startswith(ABSOLUTE_LINK_SCHEMES)
            line_no = scan.count("\n", 0, m.start()) + 1
            yield md_path, line_no, path_part, is_absolute


def _resolve_relative(md_path: Path, root: Path, path_part: str) -> Path:
    """A relative link resolves against the LINKING FILE's own directory
    (markdown convention); a leading-`/` link resolves against the repo
    root (`root.parent`, since `root` itself is `skills/`).

    `path_part` arrives percent-encoded exactly as written (`_iter_links`
    splits the `#fragment` off BEFORE any decoding, so a literal `#` in a
    filename -- spelled `%23` in the link -- is never mistaken for the
    fragment separator). Decoded here, once, right before it touches the
    filesystem: `Path.exists()` compares against real bytes on disk, which
    are never percent-encoded, so `with%20space.txt` has to become
    `with space.txt` before the check or a real file at that name reads as
    a broken link.
    """
    decoded = urllib.parse.unquote(path_part)
    base = root.parent if decoded.startswith("/") else md_path.parent
    return Path(os.path.normpath(base / decoded.lstrip("/")))


def link_errors(root: Path) -> list[str]:
    """Broken relative markdown links under `root` -- the #234 gate.

    Absolute http(s) links are never included here (see the module comment
    above); `link_stats` reports how many were seen instead.

    `errors` is created here and handed to `_iter_links`, so an unreadable
    file's annotation lands in the SAME list this function returns -- the
    caller sees one combined, ordered set of failures rather than a read
    failure reported through a side channel nothing here gates on.

    `target_path.is_file()`, not `.exists()`: `.exists()` is also true for
    a DIRECTORY, so `[x](references)` read as clean even though nothing at
    that path is a document a reader can open.
    """
    errors: list[str] = []
    for md_path, line_no, path_part, is_absolute in _iter_links(root, errors):
        if is_absolute:
            continue
        target_path = _resolve_relative(md_path, root, path_part)
        if not target_path.is_file():
            reason = (
                "is a directory, not a file"
                if target_path.is_dir()
                else "does not exist"
            )
            errors.append(
                f"::error file={md_path}::line {line_no}: broken relative "
                f"link -> {path_part} (resolved: {target_path}) {reason}"
            )
    return errors


def link_stats(root: Path) -> tuple[int, int]:
    """(relative_count, absolute_count) markdown links seen under `root` --
    what `main()`'s scope line reports, so a reader of green CI output is
    told the bound rather than assuming every link was verified.
    """
    relative = absolute = 0
    for _md_path, _line_no, _path_part, is_absolute in _iter_links(root):
        if is_absolute:
            absolute += 1
        else:
            relative += 1
    return relative, absolute


def _is_superseded(meta: dict) -> bool:
    """Whether this skill announces itself as retired.

    Three signals, because the catalog has used them at different times and a
    detector that only knows one is a detector that goes quiet the first time
    somebody uses another: a `description` opening `SUPERSEDED`, the RESERVED
    `superseded_by` key, and `status: superseded`.
    """
    description = meta.get("description")
    if isinstance(description, str) and SUPERSEDED_RE.match(description):
        return True
    if isinstance(meta.get("superseded_by"), str) and meta["superseded_by"].strip():
        return True
    status = meta.get("status")
    return isinstance(status, str) and status.strip().lower() == "superseded"


def _valid_extension_entry(e: object) -> bool:
    """An `applies_to.extensions` entry is a suffix-matched string —
    clud-bug does suffix matching, not strict dotfile-extension
    matching, so both '.tsx' and '_test.py' (skills/test-discipline
    ships the latter) are legitimate. Require: non-empty string, no
    whitespace, at least one '.', and not the bare string '.'.
    """
    return (
        isinstance(e, str)
        and e != ""
        and not re.search(r"\s", e)
        and "." in e
        and e != "."
    )


def _skill_dirs(root: Path) -> list[Path]:
    """Every immediate subdirectory of `root`, sorted. The set of things the
    gate considers a skill -- one SKILL.md is expected in each.
    """
    return sorted(p for p in root.iterdir() if p.is_dir())


# One (field, permissive-line-reader, strict-count, malformed-message) tuple
# per identity field, walked in `identity_errors` below. `digest` and
# `origin` have exactly one correct value the gate can compute on its own
# (the content hash, and the constant `skill_version.ORIGIN`); `version`
# does not -- its correct PATCH digit depends on whether THIS file's own
# prior claim already matches the freshly computed digest, which is exactly
# what `skill_version.stamp()` already works out. So every field's "what
# should this line say" answer is read the same way: render `stamp(raw)`
# once and compare each actual line against the line it produced.
_IDENTITY_FIELDS = (
    (
        "version",
        skill_version.version_lines,
        skill_version.version_line_count,
        skill_version.stamped_version,
        'It must be `version: "<major>.<minor>.<patch>"` -- the quotes are '
        "REQUIRED, an unquoted three-part number is still just text but a "
        "malformed one is not worth the exception. Never bump PATCH by hand; "
        "only MAJOR and MINOR are an author's to set.",
    ),
    (
        "digest",
        skill_version.digest_lines,
        skill_version.digest_line_count,
        skill_version.stamped_digest,
        'It must be `digest: "<12 lowercase hex>"` -- the quotes are '
        "REQUIRED, because unquoted an all-digit digest parses as an "
        "integer.",
    ),
    (
        "origin",
        skill_version.origin_lines,
        skill_version.origin_line_count,
        skill_version.stamped_origin,
        f"It must be `origin: {skill_version.ORIGIN}` -- unquoted, this "
        "catalog's own URL and nothing else.",
    ),
)


def identity_errors(prefix: str, raw: bytes) -> list[str]:
    """`version:` / `digest:` / `origin:` -- the three fields split out of
    the old single `version:` stamp (see skill_version.py's module
    docstring): an ordered, human semver; a recomputable content digest; and
    a machine-readable route home, in place of a YAML comment `yaml.safe_load`
    discarded before a program ever saw it.

    Checked against the file's own bytes, so none of the three is a promise a
    human has to keep. A stale stamp is worse than none: every subscriber
    comparing against it is told they are current when they are not.

    ENFORCED WHEN PRESENT, NOT REQUIRED -- the same posture `version:` alone
    had, and `source` and `kind` still have. The protocol SPEC owns the
    frontmatter schema (live §2.1 "The skill file"), and its table already
    marks `source` REQUIRED against 0 of 49 adopters. Declaring a required key
    from inside the catalog would widen that divergence rather than close it.
    Ratification is protocol#39's to grant; until it does, a file naming NONE
    of the three is not an error -- but naming one and not the others is: the
    three are gated together, because an index carrying `current` and
    `version` for a skill whose file only bothered to claim a digest is
    exactly the kind of half-true state this format exists to make
    unrepresentable.
    """
    opted_in = any(count(raw) for _f, _lf, count, _sv, _msg in _IDENTITY_FIELDS)
    if not opted_in:
        return []

    errors: list[str] = []
    expected_full = skill_version.stamp(raw)

    for field, line_fn, count_fn, stamped_fn, malformed_msg in _IDENTITY_FIELDS:
        lines = line_fn(raw)
        expected_line = line_fn(expected_full)[0]

        if len(lines) == 0:
            # The other two fields are present (`opted_in` is true) but this
            # one is not -- the file has opted the whole triple in without
            # actually naming all of it. Reported by name, the same as any
            # other missing-but-required-together key in this file.
            errors.append(
                f"::error file={prefix}::this file stamps `version:`/`digest:`/"
                f"`origin:` together but is missing `{field}:` -- it must be "
                f"all three or none. Run `python3 .github/scripts/"
                f"stamp_versions.py --write`, which would add `{expected_line}`."
            )
        elif len(lines) > 1:
            # Two lines for one field make identity a question of which
            # reader you ask. A `search`-based gate takes the FIRST and
            # passes; every YAML consumer takes the LAST (last key wins) and
            # reads something else. Neither is wrong about its own rule, so
            # the file has to be rejected rather than adjudicated. Not just
            # `version:`'s risk -- `yaml.safe_load` applies last-key-wins to
            # any duplicated key, so `digest:` and `origin:` get the same
            # check.
            shown = lines[0].split()[1] if len(lines[0].split()) > 1 else "?"
            errors.append(
                f"::error file={prefix}::frontmatter has {len(lines)} `{field}:` "
                f"lines, and there must be exactly one -- this gate would read "
                f"{shown} while `yaml.safe_load` reads the last one. Keep one "
                f"line: `{expected_line}`"
            )
        else:
            claimed = stamped_fn(raw)
            if claimed is None:
                errors.append(
                    f"::error file={prefix}::`{lines[0]}` is not a well-formed "
                    f"`{field}:` stamp. {malformed_msg} Never type this by hand; "
                    f"run `python3 .github/scripts/stamp_versions.py --write`."
                )
            elif lines[0] != expected_line:
                errors.append(
                    f"::error file={prefix}::`{field}` claims {claimed!r} but "
                    f"should read `{expected_line}`. The stamp is stale, so every "
                    f"subscriber comparing against it reads a wrong identity. Run "
                    f"`python3 .github/scripts/stamp_versions.py --write`."
                )
    return errors


def run(root: Path) -> list[str]:
    """Validate every skill under `root`, returning the `::error ...::` lines.

    An empty list means clean. The caller prints the lines and the summary --
    see `main()`, which also applies `coverage_errors()` to the clean path so
    a run that validated nothing cannot pass.

    Two INFRA-FATAL conditions print and `sys.exit(1)` from here rather than
    returning: a missing skills/ dir and a skills/ dir with no subdirectories.
    They are not validation errors, they carry no `::error::<N> skill
    validation errors` summary line, and that is the workflow's shipped
    behaviour -- preserved deliberately.
    """
    errors: list[str] = []
    # Slugs whose own frontmatter says they are retired. Collected here rather
    # than re-read in the placement-map block below, so the two can never
    # disagree about which skills those are.
    superseded: set[str] = set()
    # slug -> content digest, filled in as each skill is read, so the index
    # gate below compares against bytes this run actually saw.
    digests: dict[str, str] = {}
    # slug -> the semver the file itself claims, or None if it has never
    # been stamped -- same "filled in as read" reasoning as `digests` above.
    versions: dict[str, str | None] = {}

    if not root.exists() or not root.is_dir():
        print("::error::skills/ directory not found at repo root")
        sys.exit(1)

    skill_dirs = _skill_dirs(root)
    if not skill_dirs:
        print("::error::no skill subdirectories under skills/")
        sys.exit(1)

    for skill_dir in skill_dirs:
        dir_name = skill_dir.name
        skill_md = skill_dir / "SKILL.md"
        prefix = f"{skill_md}"

        if not skill_md.exists():
            errors.append(f"::error file={prefix}::missing SKILL.md")
            continue

        raw = skill_md.read_bytes()
        content = raw.decode("utf-8")
        m = FRONTMATTER_RE.match(content)
        if not m:
            errors.append(
                f"::error file={prefix}::missing YAML frontmatter "
                "(must start with --- ... --- block)"
            )
            continue

        try:
            meta = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            errors.append(
                f"::error file={prefix}::frontmatter is not valid YAML: {e}"
            )
            continue

        if not isinstance(meta, dict):
            errors.append(
                f"::error file={prefix}::frontmatter must be a YAML mapping"
            )
            continue

        if _is_superseded(meta):
            superseded.add(dir_name)

        name = meta.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            errors.append(
                f"::error file={prefix}::frontmatter is missing a non-empty `name:` field"
            )
        else:
            name = name.strip()
            if name != dir_name:
                errors.append(
                    f"::error file={prefix}::frontmatter name='{name}' "
                    f"does not match directory name '{dir_name}'"
                )
            if not NAME_SLUG_RE.match(name):
                errors.append(
                    f"::error file={prefix}::frontmatter name='{name}' does not match "
                    r"the SPEC §1.10.1 slug regex ^[a-z][a-z0-9-]{0,62}$"
                )

        description = meta.get("description")
        if not description or not isinstance(description, str) or not description.strip():
            errors.append(
                f"::error file={prefix}::frontmatter is missing a non-empty `description:` field"
            )

        # --- Content identity (`version:` / `digest:` / `origin:`) --------
        #
        # See `identity_errors` above for the rules. `digests`/`versions` are
        # filled in here regardless of whether this file opts in to the
        # stamp -- the skill-versions.json currency gate below needs every
        # skill's digest and semver, stamped or not (None is a value too).
        digests[dir_name] = skill_version.digest(raw)
        versions[dir_name] = skill_version.stamped_version(raw)
        errors.extend(identity_errors(prefix, raw))

        # Require an H1 (Markdown title) somewhere in the body after the frontmatter
        body = content[m.end():]
        if not re.search(r"^# .+", body, flags=re.MULTILINE):
            errors.append(
                f"::error file={prefix}::body has no top-level `# Title` heading"
            )

        # --- Body size (see SIZE_LIMIT above) ---
        # The error carries the REASON deliberately. A maintainer who
        # hits a bare limit files a bypass PR; one who is told the tail
        # silently never reaches the reader fixes the skill instead.
        body_bytes = len(body.encode("utf-8"))
        if body_bytes > SIZE_LIMIT:
            errors.append(
                f"::error file={prefix}::body is {body_bytes} bytes, over the "
                f"{SIZE_LIMIT}-byte limit by {body_bytes - SIZE_LIMIT}. Past this, a "
                f"consuming reviewer truncates the body when building its prompt -- your "
                f"reader silently does not receive the rest, and nothing reports it. "
                f"Fixes, in order: cut narration and duplication; replace anything a "
                f"neighbouring skill already owns with a relative markdown link to it; "
                f"split ONLY if this is genuinely two topics, never to hit the number. "
                f"Do NOT move instruction prose into references/ to buy bytes -- "
                f"that consumer reads SKILL.md and nothing else, so the move deletes "
                f"it for the reader it was written for. Shipping source material "
                f"there is fine and unaffected; the rule is about relocating what "
                f"the reader needs. There is no exception list for the limit."
            )

        # --- SPEC §1.10.1 OPTIONAL-field validation ---

        kind = meta.get("kind")
        if kind is not None and kind not in KIND_VALUES:
            errors.append(
                f"::error file={prefix}::`kind: {kind!r}` is not one of "
                f"{sorted(KIND_VALUES)} (SPEC §1.10.1)"
            )

        # `review_mode` was removed from the skill schema: how a repo
        # groups skills into passes is `review.passes` in its own review
        # config (SPEC §2.2), not a field on a skill it may not edit.
        # Unrecognised keys round-trip untouched (SPEC §2.1), so a stale
        # one is ignored rather than rejected.

        source = meta.get("source")
        if source is not None and source not in SOURCE_VALUES:
            errors.append(
                f"::error file={prefix}::`source: {source!r}` is not one of "
                f"{sorted(SOURCE_VALUES)} (SPEC §1.10.1)"
            )

        applies_to = meta.get("applies_to")
        if applies_to is not None:
            if not isinstance(applies_to, dict):
                errors.append(
                    f"::error file={prefix}::`applies_to` must be a YAML mapping"
                )
            else:
                paths = applies_to.get("paths")
                if paths is not None and (
                    not isinstance(paths, list)
                    or not all(isinstance(p, str) and p.strip() for p in paths)
                ):
                    errors.append(
                        f"::error file={prefix}::`applies_to.paths` must be a list "
                        "of non-empty glob strings (SPEC §1.10.1)"
                    )

                extensions = applies_to.get("extensions")
                if extensions is not None and (
                    not isinstance(extensions, list)
                    or not all(_valid_extension_entry(e) for e in extensions)
                ):
                    errors.append(
                        f"::error file={prefix}::`applies_to.extensions` must be a "
                        "list of extension/suffix strings (e.g. '.tsx', "
                        "'_test.py') (SPEC §1.10.1)"
                    )

                author = applies_to.get("author")
                if author is not None:
                    if not isinstance(author, str) or not author.strip():
                        errors.append(
                            f"::error file={prefix}::`applies_to.author` must be a "
                            "single non-empty GitHub handle string, not a list "
                            "(SPEC §1.10.1)"
                        )
                    elif author.strip().startswith("@"):
                        errors.append(
                            f"::error file={prefix}::`applies_to.author` must not "
                            "include a leading '@' (SPEC §1.10.1)"
                        )

    # --- docs/placement-map.json gate (see the constants above) --------

    placement_map_path = root.parent / "docs" / "placement-map.json"

    if placement_map_path.exists():
        pm_prefix = str(placement_map_path)

        try:
            pm_text = placement_map_path.read_text(encoding="utf-8")
        except OSError as e:
            errors.append(
                f"::error file={pm_prefix}::could not read {placement_map_path}: {e}"
            )
            pm_text = None

        pm = None
        if pm_text is not None:
            try:
                pm = json.loads(pm_text)
            except json.JSONDecodeError as e:
                errors.append(
                    f"::error file={pm_prefix}::{placement_map_path} is not valid JSON: {e}"
                )

        if pm is not None:
            if not isinstance(pm, dict):
                errors.append(
                    f"::error file={pm_prefix}::top level of {placement_map_path} "
                    "must be a JSON object with `version`, `updated`, `skills`"
                )
            else:
                version = pm.get("version")
                if not isinstance(version, int) or isinstance(version, bool):
                    errors.append(
                        f"::error file={pm_prefix}::`version` must be an int"
                    )

                updated = pm.get("updated")
                if not isinstance(updated, str) or not updated.strip():
                    errors.append(
                        f"::error file={pm_prefix}::`updated` must be a non-empty string"
                    )

                # --- `families`: the directory's grouping, ordered ---
                #
                # An ordered list rather than an object because the order IS
                # the document order of the generated directory, and a JSON
                # object's key order is not a thing a reviewer should have to
                # trust.
                families = pm.get("families")
                family_ids: set[str] = set()
                if not isinstance(families, list) or not families:
                    errors.append(
                        f"::error file={pm_prefix}::`families` must be a non-empty list "
                        "of {id, title, routes} objects. It is the directory's grouping; "
                        "without it every skill's `family` is unresolvable and the "
                        "generated directory is a flat list of names."
                    )
                else:
                    for i, fam in enumerate(families):
                        if not isinstance(fam, dict):
                            errors.append(
                                f"::error file={pm_prefix}::families[{i}] must be an "
                                "object with `id`, `title` and `routes`"
                            )
                            continue
                        fid = fam.get("id")
                        if not isinstance(fid, str) or not NAME_SLUG_RE.match(fid):
                            errors.append(
                                f"::error file={pm_prefix}::families[{i}].id={fid!r} must "
                                r"match ^[a-z][a-z0-9-]{0,62}$"
                            )
                        elif fid in family_ids:
                            errors.append(
                                f"::error file={pm_prefix}::families[{i}].id={fid!r} is "
                                "declared twice; a skill naming it would be listed twice"
                            )
                        else:
                            family_ids.add(fid)
                        for key in ("title", "routes"):
                            val = fam.get(key)
                            if not isinstance(val, str) or not val.strip():
                                errors.append(
                                    f"::error file={pm_prefix}::families[{i}].{key} must "
                                    "be a non-empty string"
                                )

                skills_map = pm.get("skills")
                if not isinstance(skills_map, dict):
                    errors.append(
                        f"::error file={pm_prefix}::`skills` must be an object "
                        "mapping skill name -> metadata"
                    )
                else:
                    malformed_entry = False
                    for slug, meta in skills_map.items():
                        if not isinstance(meta, dict):
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug} must be "
                                "an object (unknown per-skill keys are tolerated; "
                                "the value itself must still be a mapping)"
                            )
                            malformed_entry = True
                            continue

                        authoring_home = meta.get("authoring_home")
                        if not isinstance(authoring_home, str) or not AUTHORING_HOME_RE.match(
                            authoring_home
                        ):
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.authoring_home="
                                f"{authoring_home!r} must match "
                                r"^(catalog|undecided|repo-mirrored:[a-z0-9-]+)$"
                            )

                        distribution = meta.get("distribution")
                        if distribution not in DISTRIBUTION_VALUES:
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.distribution="
                                f"{distribution!r} is not one of "
                                f"{sorted(DISTRIBUTION_VALUES)}"
                            )

                        subscribers = meta.get("subscribers")
                        if not isinstance(subscribers, list) or not all(
                            isinstance(s, str) for s in subscribers
                        ):
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.subscribers "
                                "must be a list of strings"
                            )

                        # --- the directory's two editorial keys ---
                        #
                        # These are REQUIRED, and that is the whole point: the
                        # map is already reconciled 1:1 against skills/ below,
                        # so requiring them here means a skill cannot be added
                        # without saying which family it belongs to and what it
                        # owns. The README table has never had that property --
                        # it is complete by diligence, and the next skill added
                        # is the one that breaks it silently (#229).
                        family = meta.get("family")
                        if not isinstance(family, str) or not family.strip():
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.family must be "
                                "a non-empty string naming one of the `families` ids. It "
                                "is what puts this skill in the generated directory "
                                f"(skills/{gen_skill_directory.DIRECTORY_SLUG}/SKILL.md); "
                                "without it the skill exists and the catalog's own map "
                                "does not show it."
                            )
                        elif family not in family_ids:
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.family="
                                f"{family!r} is not a declared family. Declared: "
                                f"{', '.join(sorted(family_ids)) or '(none)'}"
                            )

                        # The one meaning-level check the byte comparison
                        # cannot make. `owns` and `family` are editorial text;
                        # the directory and the map agree with each other by
                        # construction, so a skill filed as live after it was
                        # retired is invisible to every gate above -- and it
                        # shipped that way: `skillforge` sat under "The
                        # catalog itself" reading "scaffolding a new skill"
                        # for the whole migration window, which routes an
                        # agent INTO the retired guidance. That is #229's
                        # failure inverted, inside the artifact built to
                        # prevent it, so the class is closed rather than the
                        # instance.
                        if (
                            slug in superseded
                            and isinstance(family, str)
                            and family != gen_skill_directory.DEPRECATED_FAMILY
                        ):
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.family="
                                f"{family!r}, but skills/{slug}/SKILL.md announces "
                                "itself as SUPERSEDED. A retired skill listed among "
                                "live ones is a directory routing agents to guidance "
                                "its own author told them to stop following. File it "
                                f"under '{gen_skill_directory.DEPRECATED_FAMILY}' and "
                                "point `owns` at the successors."
                            )

                        owns = meta.get("owns")
                        if not isinstance(owns, str) or not owns.strip():
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.owns must be a "
                                "non-empty string -- the fragment naming what this skill "
                                "OWNS, not what it is about, as it appears in the "
                                "directory."
                            )
                        elif len(owns.encode("utf-8")) > gen_skill_directory.OWNS_MAX_BYTES:
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.owns is "
                                f"{len(owns.encode('utf-8'))} bytes, over the "
                                f"{gen_skill_directory.OWNS_MAX_BYTES}-byte cap by "
                                f"{len(owns.encode('utf-8')) - gen_skill_directory.OWNS_MAX_BYTES}"
                                ". The cap is what keeps the directory itself under the "
                                "skill body limit as the catalog grows -- every byte here "
                                "is paid once per skill. Cut it to a fragment; the "
                                "family's routing line carries the context."
                            )

                    # Every declared family must have at least one skill. A
                    # family with none renders as nothing, so the map would
                    # claim a grouping the directory does not show -- the same
                    # divergence the 1:1 reconcile below exists to stop, in the
                    # one direction it does not cover.
                    #
                    # Suppressed when an entry was not even a mapping: that
                    # skill's `family` is unknowable, so "no skill lists it"
                    # would be a second annotation derived from the first
                    # defect rather than a finding of its own.
                    # `isinstance(..., str)` is load-bearing, not defensive:
                    # a `family: []` in the JSON is unhashable, and building
                    # this set without the guard raised TypeError out of the
                    # whole gate -- a malformed map taking the validator down
                    # instead of being reported by it.
                    used = {
                        m.get("family")
                        for m in skills_map.values()
                        if isinstance(m, dict) and isinstance(m.get("family"), str)
                    }
                    dead = [] if malformed_entry else sorted(family_ids - used)
                    if dead:
                        errors.append(
                            f"::error file={pm_prefix}::`families` declares "
                            f"{', '.join(dead)} but no skill lists "
                            f"{'them' if len(dead) > 1 else 'it'}. Delete the family or "
                            "give a skill that `family`."
                        )

                    # Map keys must EXACTLY equal the skills/ directory names.
                    map_names = set(skills_map.keys())
                    dir_names = {d.name for d in skill_dirs}
                    missing_from_map = sorted(dir_names - map_names)
                    extra_in_map = sorted(map_names - dir_names)
                    if missing_from_map:
                        errors.append(
                            f"::error file={pm_prefix}::{placement_map_path} is missing "
                            f"an entry for: {', '.join(missing_from_map)}"
                        )
                    if extra_in_map:
                        errors.append(
                            f"::error file={pm_prefix}::{placement_map_path} has an entry "
                            f"for non-existent skills/ dir(s): {', '.join(extra_in_map)}"
                        )

    errors.extend(directory_errors(root, placement_map_path))
    errors.extend(readme_errors(root, skill_dirs))
    errors.extend(link_errors(root))
    # --- docs/skill-versions.json currency gate ------------------------
    #
    # The published index is what a subscriber reads to answer "am I
    # current?", so a `current` that has fallen behind the tree tells them
    # they are up to date when they are not -- the exact failure this whole
    # mechanism exists to remove, relocated one hop away.
    #
    # This half needs NO git history: `current` is recomputed from the bytes
    # in the checkout, so it holds at the depth-1 checkout
    # validate-skills.yml uses. The history rows are NOT gated here and
    # cannot be at that depth; the index says so in its own `verification`
    # block rather than leaving a reader to assume otherwise.
    #
    # NOT gated on `.exists()`, unlike the placement map above -- that gate's
    # posture is "authored by a parallel agent, may not exist yet"; this
    # index is checked into the repo and generated by this catalog's own
    # tooling, so its absence is not a file some other process hasn't gotten
    # to yet. It is every `skills.<slug>` entry missing at once, and
    # `skills_current.py` already treats an unreadable index as UNCERTAIN
    # rather than a pass -- this matches that stance by falling into the same
    # "could not read" branch below rather than skipping it.

    versions_path = root.parent / "docs" / "skill-versions.json"
    sv_prefix = str(versions_path)
    try:
        index = json.loads(versions_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        errors.append(f"::error file={sv_prefix}::could not read {versions_path}: {e}")
        index = None

    if index is not None and not isinstance(index.get("skills"), dict):
        errors.append(
            f"::error file={sv_prefix}::`skills` must be an object mapping "
            "skill name -> {current, history}"
        )
    elif index is not None:
        published = index["skills"]
        for slug, want in sorted(digests.items()):
            entry = published.get(slug)
            if not isinstance(entry, dict):
                errors.append(
                    f"::error file={sv_prefix}::skills.{slug} is missing. Every "
                    "skill in skills/ must be published, or a subscriber "
                    "looking it up gets nothing and cannot tell that from "
                    "being current. Run "
                    "`python3 .github/scripts/gen_skill_versions.py --write`."
                )
                continue
            if entry.get("current") != want:
                errors.append(
                    f"::error file={sv_prefix}::skills.{slug}.current is "
                    f"{entry.get('current')!r} but skills/{slug}/SKILL.md digests "
                    f"to {want}. The index is stale, so every subscriber it "
                    "answers is told the wrong thing. Run "
                    "`python3 .github/scripts/gen_skill_versions.py --write`."
                )
            # `version` is the semver counterpart of the check just above --
            # same reasoning, same remedy. None is a legitimate value on both
            # sides (a skill never stamped), so it is compared like any other.
            want_version = versions.get(slug)
            if entry.get("version") != want_version:
                errors.append(
                    f"::error file={sv_prefix}::skills.{slug}.version is "
                    f"{entry.get('version')!r} but skills/{slug}/SKILL.md's "
                    f"`version:` claims {want_version!r}. The index is stale, "
                    "so every subscriber it answers is told the wrong thing. "
                    "Run `python3 .github/scripts/gen_skill_versions.py --write`."
                )

    return errors


def readme_errors(root: Path, skill_dirs: list[Path]) -> list[str]:
    """Reconcile the README's skill links 1:1 against `skills/`.

    #229's first problem, and the smaller half of it: the README table names
    every skill and nothing keeps it that way, so it is complete by diligence
    and the next skill added is the one that breaks it silently, in the file
    most readers meet first.

    MEMBERSHIP only. The purpose column is hand-written prose with room for
    sentences the byte-capped directory cannot afford, and generating it from
    `owns` would make the README worse to make it derived. So this gate asks
    the one question a machine can answer without flattening it: is every
    skill named, and is every skill it names real.

    Absence of the README is tolerated, exactly as the placement map's is --
    a tree that does not publish one has nothing to reconcile.
    """
    readme = root.parent / "README.md"
    if not readme.exists():
        return []

    prefix = str(readme)
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError as e:
        return [f"::error file={prefix}::could not read {readme}: {e}"]

    linked = set(README_SKILL_LINK_RE.findall(text))
    on_disk = {d.name for d in skill_dirs}

    errors: list[str] = []
    missing = sorted(on_disk - linked)
    if missing:
        errors.append(
            f"::error file={prefix}::the README does not link "
            f"skills/<name>/SKILL.md for: {', '.join(missing)}. It is the first "
            "listing most readers meet, and a skill missing from it reads as a "
            "skill that does not exist -- which is what somebody then writes "
            "again. Add a row to the table."
        )
    stale = sorted(linked - on_disk)
    if stale:
        errors.append(
            f"::error file={prefix}::the README links skills/<name>/SKILL.md for "
            f"dir(s) that do not exist: {', '.join(stale)}. A dead row sends a "
            "reader to a 404 and counts toward a completeness nobody has."
        )
    return errors


def directory_errors(root: Path, placement_map_path: Path) -> list[str]:
    """The generated catalog directory must equal what the generator renders.

    This is the half that makes drift unrepresentable rather than merely
    reconciled. The 1:1 reconcile above catches a skill that never got a map
    entry; this catches the entry that exists and the DIRECTORY that was not
    regenerated -- which is the same class of defect one level down, and the
    one a hand-kept skill body would have reintroduced.

    Runs only when the directory skill is present. Its absence is not an error
    HERE: this function's rules have to hold for any tree the gate is pointed
    at, including the tmp trees the suite drives it over, and "a directory
    exists" is a fact about THIS repo rather than about trees in general.
    Deleting the skill alone is already red (the map keeps an entry for a dir
    that no longer exists); deleting the entry as well is caught by
    `tests/test_gen_skill_directory.py::test_this_catalog_publishes_a_directory`,
    which owns that fact and reddens the PR that removes it. One owner, and it
    is named here so the next reader does not conclude nothing owns it.

    Presence WITHOUT a usable source is always an error -- an unverifiable
    directory reads exactly like a verified one.
    """
    path = root / gen_skill_directory.DIRECTORY_SLUG / "SKILL.md"
    if not path.exists():
        return []

    prefix = str(path)
    try:
        rendered = gen_skill_directory.render(root, placement_map_path)
    except SystemExit as e:
        return [
            f"::error file={prefix}::the directory cannot be rendered, so it cannot be "
            f"verified -- and an unverifiable directory reads exactly like a current "
            f"one to the agent holding it: {e}"
        ]

    size = gen_skill_directory.size_error(rendered)
    if size:
        return [f"::error file={prefix}::{size}"]

    content = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(content)
    if not m:
        # The per-skill loop already filed "missing YAML frontmatter"; adding a
        # second annotation for the same defect would only make the count lie.
        return []

    if content[m.end():] != rendered:
        return [
            f"::error file={prefix}::this body is GENERATED and no longer matches what "
            "docs/placement-map.json plus the skills/ tree render. Either a skill was "
            "added, removed or re-described without regenerating, or the body was "
            "hand-edited -- and a directory that has quietly stopped listing a skill is "
            "read as evidence that skill does not exist. Run "
            "`python3 .github/scripts/gen_skill_directory.py --write` and commit the "
            "result; edit the prose in the generator, never here."
        ]
    return []


def coverage_errors(root: Path, validated: int) -> list[str]:
    """Assert the run actually saw the tree it claims to have validated.

    `ROOT` is cwd-relative. A clean list of errors is only evidence if it was
    produced against real skills -- a run that walked an empty or wrong tree
    reports zero errors just as loudly as one that walked 48 correct skills.
    So the clean path is gated on: `validated` is non-zero, AND it equals the
    number of SKILL.md files actually on disk under `root`.

    Returns the `::error::` lines (empty list == the pass is evidence).
    """
    on_disk = len(list(root.glob("*/SKILL.md")))
    errors: list[str] = []

    if validated == 0:
        errors.append(
            f"::error::coverage guard: 0 skills validated under '{root}'. This gate is "
            "cwd-relative, so a run from the wrong directory validates nothing and "
            "would otherwise report success -- green CI over zero coverage. Run it "
            "from the repo root."
        )

    if validated != on_disk:
        errors.append(
            f"::error::coverage guard: validated {validated} skill dir(s) but '{root}' "
            f"holds {on_disk} SKILL.md file(s). The counts must agree or the pass is "
            "not evidence about the skills on disk."
        )

    return errors


def main() -> int:
    errors = run(ROOT)

    # Printed on every completed run, pass or fail (#234) -- but AFTER
    # `run(ROOT)`, which exits the process directly for the two infra-fatal
    # conditions (no skills/ dir; skills/ with no subdirectories) where
    # there is no tree to state a bound about. A reader of green CI output
    # is TOLD the bound the link gate checked -- relative links resolved on
    # disk, absolute http(s) links counted but never fetched -- rather than
    # left to assume "all links" from silence.
    relative, absolute = link_stats(ROOT)
    print(
        f"link scope: {relative} relative link(s) checked against the "
        f"filesystem; {absolute} absolute http(s)/mailto link(s) found and "
        "counted, not fetched (no network access in this gate)."
    )

    if errors:
        for e in errors:
            print(e)
        print(f"::error::{len(errors)} skill validation errors")
        return 1

    validated = len(_skill_dirs(ROOT))
    guard = coverage_errors(ROOT, validated)
    if guard:
        for e in guard:
            print(e)
        return 1

    print(f"OK: {validated} skills validated cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
