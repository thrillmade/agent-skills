#!/usr/bin/env python3
"""Content identity for a SKILL.md, derivable from the file alone.

Three fields, each answering a different question a subscriber has no other
way to ask:

    version: "1.4.2"    ordered, human -- which revision, and how it compares
    digest:  "c894961136c7"   exact, machine-recomputable -- which bytes
    origin:  "https://github.com/thrillmade/agent-skills"   where to check

`digest` used to be all there was, spelled `version:` -- a fixed point, but
one that answers "same or different," never "newer." `origin` used to be a
YAML *comment* trailing that line: readable by a human who opens the file,
discarded by `yaml.safe_load` before a program ever sees it. Both defects,
and both fixed the same way: give the fact its own field.

The rule, short enough to retype from memory:

    normalise CRLF -> LF, delete the `version:`, `digest:` and `origin:`
    lines from the frontmatter, sha256 the remaining bytes, take the first
    12 hex characters.

That constraint is unchanged in spirit and widened in fact: ALL THREE lines
are elided before hashing, not just one, or stamping would change the
digest it is supposed to be stable under -- see `stamp()`. Deleting them is
what makes the value a fixed point: a file's digest does not depend on what
its stamp already claimed, so the same expected value is printed whether the
stamp is right, wrong, malformed or absent.

Everything else is frontmatter and body alike -- `description` in particular.
It is the trigger surface (this catalog ships `skill-frontmatter-quality` to
police it), so a body-only digest would report a rewritten description as
"current".

`version` is NOT a second copy of the digest. It is semver, one skill at a
time, ruled by the CEO as:

    MAJOR  the guidance reversed -- we now say the opposite of what we said.
           Rare by design; the real case is SC 2.5.8's `or` -> `and` in
           frontend-a11y.
    MINOR  new guidance added.
    PATCH  same guidance, tightened or corrected.

MAJOR and MINOR are an author's decision, typed by hand in the same edit
that earns them -- this module never invents one. PATCH is the one number
nobody ever hand-maintains: `stamp()` bumps it whenever the content digest
changes and the author has not already claimed a MAJOR/MINOR move, so it is
always gated, never typed. See `stamp()` for exactly how that reads its own
prior claim before overwriting it -- the one place in this module that is
NOT a pure function of the bytes alone, by necessity: "how many patches
since 1.0.0" is not recoverable from one file's bytes without a memory of
what it last claimed.

Two shapes of regex per field, on purpose:

  *_LINE_RE   PERMISSIVE. Elision, and counting. Matches any shape of a
              `field:` line so the digest is invariant across all of them,
              and so a duplicate is caught regardless of which copy is
              well-formed.
  SEMVER_RE / DIGEST_RE / ORIGIN_RE
              STRICT. What a well-formed stamp looks like. Read from the RAW
              line, never from a YAML parse: unquoted, an all-digit digest
              is coerced to int (`766941312459` is a real historical digest,
              and `000000123456` is read as octal -> 42798, silently, and
              does not round-trip) -- the same landmine a bare `1.0` would
              be for `version` if it were ever two components instead of
              three. All THREE are quoted, the URL included: a URL has no
              coercion landmine of its own, but a rule with a per-field
              carve-out is one every implementer must re-derive, and the
              cost of getting it wrong is silent and asymmetric.

Stdlib only. No git, no network -- a consumer with the file in hand has
everything, and `stamp()` reaches for nothing this module does not already
have in `raw`.
"""

from __future__ import annotations

import hashlib
import re

# The closing delimiter must be a line that is EXACTLY `---`. Without the
# lookahead, `\n---` also matches the first three characters of `----` or
# `--- not a close`, ending the block early -- so an identity line after
# such a line would not be elided, and this implementation would compute a
# different digest from one that follows SPEC 2.1 step 2 ("closes at the
# first subsequent line that is exactly `---`"). A LOOKAHEAD, not a match:
# `m.end()` must stay immediately after the closing `---`, because callers
# slice on it and consuming the newline would move bytes across that seam.
FRONTMATTER_RE = re.compile(rb"^---\n(.*?)\n---(?=\n|\Z)", re.DOTALL)

# PERMISSIVE: any line of this shape at column 0 of the frontmatter. Anchored
# to column 0 so a nested `metadata:\n  version: 3` -- somebody else's field
# -- survives into the hash; see `test_elision_is_frontmatter_only`.
VERSION_LINE_RE = re.compile(rb"(?m)^version:[^\n]*\n")
DIGEST_LINE_RE = re.compile(rb"(?m)^digest:[^\n]*\n")
ORIGIN_LINE_RE = re.compile(rb"(?m)^origin:[^\n]*\n")

# The three lines `digest()` elides and `stamp()` rewrites, always together --
# one owner for "which lines make up the identity block."
IDENTITY_LINE_RES = (VERSION_LINE_RE, DIGEST_LINE_RE, ORIGIN_LINE_RE)

# STRICT: `version: "<major>.<minor>.<patch>"`, no leading zeros (matches
# semver.org's own grammar for numeric identifiers) and no pre-release or
# build metadata -- nothing here asks for either.
SEMVER_RE = re.compile(
    rb'(?m)^version:[ \t]*"((?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))"[ \t]*$'
)

# STRICT: `digest: "<12 lowercase hex>"`, optionally trailed by the generated
# comment. The quotes are part of the shape, not decoration -- see above.
DIGEST_RE = re.compile(rb'(?m)^digest:[ \t]*"([0-9a-f]{12})"[ \t]*(?:#[^\n]*)?$')

# STRICT: `origin: "<url>"`, QUOTED. A URL has no int/octal coercion
# landmine of its own -- the quotes are here for uniformity, not for safety,
# because SPEC 2.1 makes the rule all three fields rather than the two that
# can be digit-shaped. Over-quoting a URL is inert; under-quoting a digest
# is an identity that compares unequal to itself. The strict reader has to
# enforce it or the MUST is decorative: a bare URL would keep validating and
# nothing would ever notice.
ORIGIN_RE = re.compile(rb'(?m)^origin:[ \t]*"([^"\n]+)"[ \t]*$')

# The route home, carried by every stamped file. A copy taken by hand -- no
# `npx skills add`, no lock, no checker -- is a normal case for a public
# catalog, and this is the only thing in the file that tells whoever holds it
# where the answer lives. It sits in the frontmatter, which the size gate does
# not charge for, rather than in the body, which it does.
HOME = "github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json"
COMMENT = f"# is your copy current? {HOME}"

# The `origin:` field's one value, for every skill this catalog publishes --
# including the `repo-mirrored:` ones (see docs/placement-map.json): the
# question this field answers is "where do I go to check currency", and that
# is always THIS catalog, never the authoring repo. `skills_current.py`
# already resolves a mirrored skill's verdict through this same index; origin
# says so as a real field instead of leaving it implicit.
ORIGIN = "https://github.com/thrillmade/agent-skills"


def _lf(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def version_line(value: str) -> str:
    """The one canonical spelling of the semver line. Generated, never typed."""
    return f'version: "{value}"'


def digest_line(value: str) -> str:
    """The one canonical spelling of the digest line. Carries the route home
    -- `version:` did before this field split in two; the value moved, the
    comment moved with it.
    """
    return f'digest: "{value}"  {COMMENT}'


def origin_line() -> str:
    """The one canonical spelling of the origin line. Not a function of
    `value` -- there is exactly one value, `ORIGIN`, for every file.
    """
    return f'origin: "{ORIGIN}"'


def digest(raw: bytes) -> str:
    """The 12-hex content identity of these bytes."""
    raw = _lf(raw)
    m = FRONTMATTER_RE.match(raw)
    if m:
        front = raw[: m.end()]
        for line_re in IDENTITY_LINE_RES:
            front = line_re.sub(b"", front)
        raw = front + raw[m.end() :]
    return hashlib.sha256(raw).hexdigest()[:12]


def _lines(raw: bytes, line_re: re.Pattern[bytes]) -> list[str]:
    m = FRONTMATTER_RE.match(_lf(raw))
    if not m:
        return []
    front = _lf(raw)[: m.end()]
    return [ln.decode("utf-8", "replace").rstrip("\n") for ln in line_re.findall(front)]


def version_lines(raw: bytes) -> list[str]:
    """Every `version:` line in the frontmatter, in order, newline stripped.

    The count matters as much as the content. Two `version:` lines make the
    file's identity a matter of which reader you ask -- a `search`-based
    reader takes the first, `yaml.safe_load` takes the last (last key wins),
    and a gate built on the first passes a file every tool downstream reads
    differently. So callers require exactly one. Same rule, independently,
    for `digest_lines` and `origin_lines` below.
    """
    return _lines(raw, VERSION_LINE_RE)


def digest_lines(raw: bytes) -> list[str]:
    return _lines(raw, DIGEST_LINE_RE)


def origin_lines(raw: bytes) -> list[str]:
    return _lines(raw, ORIGIN_LINE_RE)


def version_line_count(raw: bytes) -> int:
    return len(version_lines(raw))


def digest_line_count(raw: bytes) -> int:
    return len(digest_lines(raw))


def origin_line_count(raw: bytes) -> int:
    return len(origin_lines(raw))


def stamped_version(raw: bytes) -> str | None:
    """The semver this file CLAIMS, or None if it does not make one claim.

    None covers all of: no `version:` line, a malformed one, and --
    deliberately -- more than one. A file with two claims has made none.
    Every skill this catalog carried the day the three-field format shipped
    reads as None here: their one `version:` line held a 12-hex digest, and
    `SEMVER_RE` does not match that shape. That is not a special case in the
    code below -- it is the same "no valid claim" path a brand-new file takes,
    and `stamp()` seeds both at "1.0.0".
    """
    lines = version_lines(raw)
    if len(lines) != 1:
        return None
    m = SEMVER_RE.match(lines[0].encode("utf-8"))
    return m.group(1).decode() if m else None


def stamped_digest(raw: bytes) -> str | None:
    """The digest this file CLAIMS, or None if it does not make one claim."""
    lines = digest_lines(raw)
    if len(lines) != 1:
        return None
    m = DIGEST_RE.match(lines[0].encode("utf-8"))
    return m.group(1).decode() if m else None


def stamped_origin(raw: bytes) -> str | None:
    """The origin this file CLAIMS, or None if it does not make one claim."""
    lines = origin_lines(raw)
    if len(lines) != 1:
        return None
    m = ORIGIN_RE.match(lines[0].encode("utf-8"))
    return m.group(1).decode() if m else None


def _bump(old_version: str | None) -> str:
    """The next semver, PATCH-only -- see the module docstring for the
    MAJOR/MINOR/PATCH split. `old_version` is whatever this same file already
    claims, read by `stamp()` BEFORE it strips the line away; MAJOR and MINOR
    carry through untouched, because inventing either here is exactly what
    this function is not allowed to do.

    No valid semver to carry forward -- `old_version is None`, covering a
    file stamped for the first time under this format AND every file
    carrying the OLD one (`version:` held a digest, which is not a semver,
    so `stamped_version` already read it as absent) -- seeds "1.0.0". One
    rule, mechanical, and it is why the 56 skills this catalog held the day
    this format shipped all migrate to the same value rather than to 56
    hand-picked ones.
    """
    if old_version is None:
        return "1.0.0"
    major, minor, patch = old_version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def stamp(raw: bytes) -> bytes:
    """Return `raw` carrying a fresh version/digest/origin block as the first
    three frontmatter lines.

    `digest` and `origin` are unconditional: `digest` is always the hash of
    the elided bytes, `origin` is always `ORIGIN`. `version` is the one field
    that reads `raw`'s OWN prior claim before overwriting it -- the only
    state this function consults, so it stays a function of the file in hand
    alone, no git, no second file:

      * the newly computed digest equals what `raw` already, validly,
        claims -- nothing about the content has changed since the last
        stamp. Keep the version exactly as it is; not even a patch bump.
      * it does not (a real edit, a first-ever stamp, or a claim `stamp`
        cannot trust -- malformed, duplicated, absent) -- bump PATCH; see
        `_bump`.

    Idempotent, and a no-op on the body: any existing version:/digest:/
    origin: lines are removed first, so re-stamping a wrong, malformed or
    duplicated block converges in one pass.
    """
    raw = _lf(raw)
    m = FRONTMATTER_RE.match(raw)
    if not m:
        raise ValueError("no frontmatter -- nothing to stamp")

    old_version = stamped_version(raw)
    old_digest = stamped_digest(raw)
    new_digest = digest(raw)
    new_version = old_version if (old_version is not None and old_digest == new_digest) else _bump(old_version)

    front = raw[: m.end()]
    for line_re in IDENTITY_LINE_RES:
        front = line_re.sub(b"", front)
    stripped = front + raw[m.end() :]

    block = (
        version_line(new_version).encode("utf-8") + b"\n"
        + digest_line(new_digest).encode("utf-8") + b"\n"
        + origin_line().encode("utf-8") + b"\n"
    )
    return stripped[:4] + block + stripped[4:]
