#!/usr/bin/env python3
"""Content identity for a SKILL.md, derivable from the file alone.

One rule, short enough to retype from memory:

    normalise CRLF -> LF, delete the `version:` line from the frontmatter,
    sha256 the remaining bytes, take the first 12 hex characters.

That constraint is the whole design. `npx skills add` copies a SKILL.md
wholesale and records a `computedHash` produced by its own normalisation; a
subscriber cannot reproduce that hash, so today nobody can answer "is my copy
current?" from inside their own repo. A digest a consumer can recompute with
`sha256` and a two-line elision is one they can check without us.

Deleting the `version:` line before hashing is what makes the value a fixed
point: a file's digest does not depend on what its stamp already claimed, so
the same expected value is printed whether the stamp is right, wrong,
malformed or absent. An error message that names a different value depending
on how badly the file is broken is wrong on the first paste.

Everything else is frontmatter and body alike -- `description` in particular.
It is the trigger surface (this catalog ships `skill-frontmatter-quality` to
police it), so a body-only digest would report a rewritten description as
"current".

Two regexes on purpose:

  VERSION_LINE_RE  PERMISSIVE. Elision, and counting. Matches any shape of
                   `version:` line so the digest is invariant across all of
                   them.
  STAMP_RE         STRICT. What a well-formed stamp looks like. Read from the
                   RAW line, never from a YAML parse: unquoted, an all-digit
                   digest is coerced to int (`766941312459` is a real
                   historical digest, and `000000123456` is read as octal ->
                   42798, silently, and does not round-trip).

Stdlib only. No git, no network -- a consumer with the file in hand has
everything.
"""

from __future__ import annotations

import hashlib
import re

FRONTMATTER_RE = re.compile(rb"^---\n(.*?)\n---", re.DOTALL)

# PERMISSIVE: any `version:` line at the start of a frontmatter line.
VERSION_LINE_RE = re.compile(rb"(?m)^version:[^\n]*\n")

# STRICT: `version: "<12 lowercase hex>"`, optionally trailed by the generated
# comment. The quotes are part of the shape, not decoration -- see above.
STAMP_RE = re.compile(rb'(?m)^version:[ \t]*"([0-9a-f]{12})"[ \t]*(?:#[^\n]*)?$')

# The route home, carried by every stamped file. A copy taken by hand -- no
# `npx skills add`, no lock, no checker -- is a normal case for a public
# catalog, and this is the only thing in the file that tells whoever holds it
# where the answer lives. It sits in the frontmatter, which the size gate does
# not charge for, rather than in the body, which it does.
HOME = "github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json"
COMMENT = f"# is your copy current? {HOME}"


def _lf(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n")


def version_line(value: str) -> str:
    """The one canonical spelling of the stamp. Generated, never typed -- so
    the digest and the route home have exactly one owner between them.
    """
    return f'version: "{value}"  {COMMENT}'


def digest(raw: bytes) -> str:
    """The 12-hex content identity of these bytes."""
    raw = _lf(raw)
    m = FRONTMATTER_RE.match(raw)
    if m:
        raw = VERSION_LINE_RE.sub(b"", raw[: m.end()]) + raw[m.end() :]
    return hashlib.sha256(raw).hexdigest()[:12]


def version_lines(raw: bytes) -> list[str]:
    """Every `version:` line in the frontmatter, in order, newline stripped.

    The count matters as much as the content. Two `version:` lines make the
    file's identity a matter of which reader you ask -- a `search`-based
    reader takes the first, `yaml.safe_load` takes the last (last key wins),
    and a gate built on the first passes a file every tool downstream reads
    differently. So callers require exactly one.
    """
    m = FRONTMATTER_RE.match(_lf(raw))
    if not m:
        return []
    front = _lf(raw)[: m.end()]
    return [ln.decode("utf-8", "replace").rstrip("\n") for ln in VERSION_LINE_RE.findall(front)]


def version_line_count(raw: bytes) -> int:
    return len(version_lines(raw))


def stamped_value(raw: bytes) -> str | None:
    """The digest this file CLAIMS, or None if it does not make one claim.

    None covers all of: no frontmatter, no stamp, a malformed stamp, and --
    deliberately -- more than one `version:` line. A file with two claims has
    made none.
    """
    lines = version_lines(raw)
    if len(lines) != 1:
        return None
    m = STAMP_RE.match(lines[0].encode("utf-8"))
    return m.group(1).decode() if m else None


def stamp(raw: bytes) -> bytes:
    """Return `raw` carrying its own digest as the first frontmatter line.

    Idempotent, and a no-op on the body: any existing `version:` lines are
    removed first, so re-stamping a wrong, malformed or duplicated stamp
    converges in one pass.
    """
    raw = _lf(raw)
    m = FRONTMATTER_RE.match(raw)
    if not m:
        raise ValueError("no frontmatter -- nothing to stamp")
    stripped = VERSION_LINE_RE.sub(b"", raw[: m.end()]) + raw[m.end() :]
    line = version_line(digest(stripped)).encode("utf-8") + b"\n"
    return stripped[:4] + line + stripped[4:]
