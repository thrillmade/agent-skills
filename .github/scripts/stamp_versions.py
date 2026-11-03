#!/usr/bin/env python3
"""Write the version/digest/origin stamp into every SKILL.md under skills/.

    python3 .github/scripts/stamp_versions.py            # report, change nothing
    python3 .github/scripts/stamp_versions.py --write     # stamp
    python3 .github/scripts/stamp_versions.py --check     # exit 1 if any is stale

Never edit any of the three by hand. `digest` is the file's own bytes, so a
typed value is wrong the moment the file next changes; `origin` has exactly
one correct value for every file; `version`'s PATCH digit is `stamp()`'s to
compute, not an author's to guess (MAJOR and MINOR are the author's -- see
`skill_version.py`). A wrong stamp is worse than no stamp: every subscriber
comparing against it reads a false identity and is told they are current
when they are not.

Line-oriented on purpose. 18 of 49 descriptions are `|`/`>-` block scalars and
a YAML round-trip rewrites them, so this never parses-and-re-emits; it splices
three lines into the frontmatter and leaves every other byte alone. Both of
those are ASSERTED per file, not intended: the body must come out
byte-identical, and the result must re-parse with `name` and `description`
unchanged.

Exit codes:
  0  nothing to do (or --write succeeded)
  1  --check found a stale/missing/duplicate stamp, or a self-assertion failed
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

import skill_version

ROOT = Path("skills")


def _parts(raw: bytes) -> tuple[bytes, bytes]:
    """(frontmatter-including-fences, body). Raises on a file without one."""
    m = skill_version.FRONTMATTER_RE.match(raw.replace(b"\r\n", b"\n"))
    if not m:
        raise ValueError("no frontmatter")
    lf = raw.replace(b"\r\n", b"\n")
    return lf[: m.end()], lf[m.end() :]


def _meta(front: bytes) -> dict:
    inner = skill_version.FRONTMATTER_RE.match(front).group(1)
    return yaml.safe_load(inner) or {}


def restamp(raw: bytes) -> bytes:
    """`skill_version.stamp`, with the invariants this script promises checked
    on every file rather than assumed once in a comment.
    """
    new = skill_version.stamp(raw)

    old_front, old_body = _parts(raw)
    new_front, new_body = _parts(new)
    assert new_body == old_body, "stamping changed the body"

    old_meta, new_meta = _meta(old_front), _meta(new_front)
    for key in ("name", "description"):
        assert new_meta.get(key) == old_meta.get(key), f"stamping changed `{key}`"

    assert new_meta.get("digest") == skill_version.digest(new), "stamp does not re-parse"
    assert new_meta.get("origin") == skill_version.ORIGIN, "origin does not re-parse"
    assert new_meta.get("version") == skill_version.stamped_version(new), "version does not re-parse"

    # Each of the three is its own fixed point: what the STRICT reader
    # extracts from the freshly written line must equal what the field is
    # actually FOR -- the hash of the elided bytes, the one true origin, and
    # whatever semver `stamp()` just decided. Verified independently rather
    # than folded into one assertion, because a regression that corrupts only
    # one of the three lines (see `version_line`/`digest_line`/`origin_line`)
    # must not hide behind the other two still agreeing with themselves.
    assert skill_version.stamped_digest(new) == skill_version.digest(new), "digest is not a fixed point"
    assert skill_version.stamped_origin(new) == skill_version.ORIGIN, "origin is not a fixed point"
    assert skill_version.stamped_version(new) is not None, "version is not a fixed point"
    # Idempotence is a DIFFERENT property from the fixed points above, not a
    # stronger restatement of them: it was believed to imply the fixed point
    # because `restamp` calls `stamp` twice, but a regression that lives
    # inside `*_line` itself -- not in the call site -- fires identically on
    # both calls, corrupting both sides of `stamp(new) == new` the same way
    # and leaving them equal to each other while both are wrong. An unquoted
    # `digest_line` is exactly that: `stamped_digest(new)` comes back `None`
    # while `stamp(new) == new` still holds, so only the fixed-point
    # assertions above catch it. Verified by mutation on
    # `skill_version.digest_line`, not on `stamp` -- see
    # `test_restamp_refuses_a_persistent_unquoting_regression`.
    assert skill_version.stamp(new) == new, "not idempotent"
    return new


_FIELDS = (
    ("version", skill_version.version_lines, skill_version.version_line_count),
    ("digest", skill_version.digest_lines, skill_version.digest_line_count),
    ("origin", skill_version.origin_lines, skill_version.origin_line_count),
)


def _why(raw: bytes) -> str:
    """Name every field this file's stamp gets wrong -- there can be more
    than one at once, e.g. a file carrying none of the three is wrong about
    all of them.
    """
    counts = {name: count(raw) for name, _lines, count in _FIELDS}
    if any(n != 1 for n in counts.values()):
        return ", ".join(f"{n} `{name}:` line(s)" for name, n in counts.items()) + " -- exactly one of each"

    want = skill_version.stamp(raw)
    wrong = [
        f"`{name}` claims {lines(raw)[0].split(': ', 1)[1]!s}"
        for name, lines, _count in _FIELDS
        if lines(raw)[0] != lines(want)[0]
    ]
    return "; ".join(wrong) if wrong else "the stamp is correct"  # pragma: no cover -- unreachable: raw != new implies at least one line differs


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true", help="rewrite stale stamps")
    ap.add_argument("--check", action="store_true", help="exit 1 if any is stale")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args(argv)

    root = Path(args.root)
    paths = sorted(root.glob("*/SKILL.md"))
    if not paths:
        # A cwd-relative walk that found nothing reports success just as
        # loudly as one that found 49 correct files. Refuse to.
        print(f"error: no SKILL.md files under '{root}' -- run from the repo root")
        return 1

    stale: list[Path] = []
    for path in paths:
        raw = path.read_bytes()
        new = restamp(raw)
        if new == raw:
            continue
        stale.append(path)
        if args.write:
            path.write_bytes(new)

    if args.write:
        print(f"stamped {len(stale)} of {len(paths)} SKILL.md file(s).")
        return 0

    if not stale:
        print(f"OK: {len(paths)} stamps match their file's content digest.")
        return 0

    for path in stale:
        print(f"{path}: {_why(path.read_bytes())}")
    print(
        f"{len(stale)} of {len(paths)} stamp(s) stale. "
        f"Run `python3 {Path(__file__).name} --write` -- never type one by hand."
    )
    return 1


if __name__ == "__main__":
    # `import skill_version` resolves both ways already: run as a script,
    # Python puts this file's directory on sys.path[0]; run under pytest,
    # tests/conftest.py does. Nothing to add here.
    sys.exit(main())
