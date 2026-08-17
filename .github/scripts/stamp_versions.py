#!/usr/bin/env python3
"""Write the `version:` stamp into every SKILL.md under skills/.

    python3 .github/scripts/stamp_versions.py            # report, change nothing
    python3 .github/scripts/stamp_versions.py --write     # stamp
    python3 .github/scripts/stamp_versions.py --check     # exit 1 if any is stale

Never edit a stamp by hand -- the digest is the file's own bytes, so a typed
value is wrong the moment the file next changes, and a wrong stamp is worse
than no stamp: every subscriber comparing against it reads a false identity
and is told they are current when they are not.

Line-oriented on purpose. 18 of 49 descriptions are `|`/`>-` block scalars and
a YAML round-trip rewrites them, so this never parses-and-re-emits; it splices
one line into the frontmatter and leaves every other byte alone. Both of those
are ASSERTED per file, not intended: the body must come out byte-identical, and
the result must re-parse with `name` and `description` unchanged.

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
    assert new_meta.get("version") == skill_version.digest(new), "stamp does not re-parse"

    assert skill_version.stamped_value(new) == skill_version.digest(new), "not a fixed point"
    assert skill_version.stamp(new) == new, "not idempotent"
    return new


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
        raw = path.read_bytes()
        n = skill_version.version_line_count(raw)
        if n == 0:
            why = f"no `version:` line; should be {skill_version.digest(raw)}"
        elif n > 1:
            why = f"{n} `version:` lines -- there must be exactly one"
        else:
            why = (
                f"claims {skill_version.stamped_value(raw)}, "
                f"content digest is {skill_version.digest(raw)}"
            )
        print(f"{path}: {why}")
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
