#!/usr/bin/env python3
"""Are the agent-skills copies in THIS repo current? Run it from your repo root.

    curl -fsSLO https://raw.githubusercontent.com/thrillmade/agent-skills/main/.github/scripts/skills_current.py
    python3 skills_current.py

Stdlib only, one HTTPS GET, and it reads nothing but your own files. No git
access to the catalog, no `skills-lock.json`, no `npx`. That is the point:
`npx skills add` records a `computedHash` produced by its own normalisation
which a subscriber cannot reproduce, so until now there was no way to answer
this question from inside your own repo.

The rule, small enough to check by hand if you would rather not run this:

    normalise CRLF -> LF, delete the `version:`, `digest:` and `origin:`
    lines from the frontmatter, sha256 the remaining bytes, take the first
    12 hex characters

then look your skill's slug up in the published index. The catalog's own copy
of that rule lives in `.github/scripts/skill_version.py`, and a test asserts
the two agree on every skill in the catalog, so this file is a copy of the
rule but not a second owner of it.

Verdicts:

    current       your digest is what the catalog publishes today
    STALE n       your digest is n published versions behind
    DIVERGED      your digest is not one the catalog ever published --
                  edited locally, or newer than what main publishes
    unpublished   a version the catalog carries, but not the current one
                  (you are on a branch build, not behind)
    mirrored      authored in another repo; the catalog only mirrors it, so
                  it is not the authority and no staleness is claimed
    retired       the catalog no longer publishes this slug. There is
                  deliberately no "reinstall" here: that install cannot
                  succeed, and printing it would be an instruction that fails
    local-skill   not a catalog slug. Nothing to compare, so nothing is said

Exit codes:

    0  everything is current, local, mirrored, or unpublished (a branch
       build -- by definition not behind, so not a failure)
    1  something is stale, diverged, or retired (a copy that is behind, or
       one whose skill the catalog no longer carries at all)
    2  UNCERTAIN -- the index could not be read, or no skills were found.
       Never 0: a run that examined nothing reports success exactly as loudly
       as one that examined thirty files, and that is the failure this whole
       mechanism exists to remove.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

INDEX_URL = (
    "https://raw.githubusercontent.com/thrillmade/agent-skills/main/"
    "docs/skill-versions.json"
)
ROOTS = (".agents/skills", ".claude/skills")

FRONTMATTER_RE = re.compile(rb"^---\n(.*?)\n---(?=\n|\Z)", re.DOTALL)
IDENTITY_LINE_RES = (
    re.compile(rb"(?m)^version:[^\n]*\n"),
    re.compile(rb"(?m)^digest:[^\n]*\n"),
    re.compile(rb"(?m)^origin:[^\n]*\n"),
)


def digest(raw: bytes) -> str:
    raw = raw.replace(b"\r\n", b"\n")
    m = FRONTMATTER_RE.match(raw)
    if m:
        front = raw[: m.end()]
        for line_re in IDENTITY_LINE_RES:
            front = line_re.sub(b"", front)
        raw = front + raw[m.end() :]
    return hashlib.sha256(raw).hexdigest()[:12]


def load_index(where: str) -> dict:
    """The index, or exit 2. Absence is never allowed to read as 'current'."""
    try:
        if "://" in where:
            with urllib.request.urlopen(where, timeout=20) as r:
                body = r.read()
        else:
            body = Path(where).read_bytes()
        index = json.loads(body)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as e:
        sys.exit(_uncertain(f"could not read the version index at {where}: {e}"))
    if not isinstance(index.get("skills"), dict) or not index["skills"]:
        sys.exit(_uncertain(f"the version index at {where} lists no skills"))
    return index


def _uncertain(msg: str) -> int:
    print(f"UNCERTAIN: {msg}", file=sys.stderr)
    print("Reporting nothing rather than reporting 'current' from an absence.", file=sys.stderr)
    return 2


def discover(repo: Path, roots: list[str] | None) -> list[Path]:
    """Every installed skill directory, from every root, counted once.

    BOTH roots, because the default is wrong for most repos: measured across
    20 sibling repos, `.agents/skills` exists in 3 and `.claude/skills` in 12.
    A checker that looks at one of them reports "0 current, 0 stale" in the
    other nine and exits 0.

    And resolved, because in the repos that have both, `.claude/skills/<slug>`
    is usually a SYMLINK to `.agents/skills/<slug>` -- 17 of 17 in
    arlyn-delivery, 23 of 29 in arlyn-working. Counting the link and its
    target separately double-reports every one of them.
    """
    explicit = roots is not None
    seen: dict[Path, Path] = {}
    order: list[Path] = []
    for name in roots or ROOTS:
        root = repo / name
        if not root.is_dir():
            if explicit:
                sys.exit(_uncertain(f"--root {name} is not a directory under {repo}"))
            continue
        for d in sorted(root.iterdir()):
            skill = d / "SKILL.md"
            if not skill.is_file():
                continue
            real = skill.resolve()
            if real in seen:
                continue
            seen[real] = d
            order.append(d)
    return order


def classify(slug: str, mine: str, index: dict) -> tuple[str, str]:
    entry = index["skills"].get(slug)
    if entry is None:
        return "local-skill", "not a catalog slug -- nothing to compare"

    history = [h["v"] for h in entry.get("history", [])]
    dates = {h["v"]: h["date"] for h in entry.get("history", [])}
    current = entry.get("current")
    home = entry.get("authoring_home") or ""

    if current is None:
        return "retired", "the catalog no longer publishes this skill"
    if mine == current:
        return "current", ""

    # ABOVE the history checks below on purpose: a mirrored skill's
    # AUTHORING repo is not this catalog, so a digest here that predates
    # `current` is still not this catalog's to call stale -- the source of
    # truth is the authoring repo, and this index only mirrors what it last
    # saw there. Checking history first would tell an authoring repo to
    # overwrite its own source from the mirror the docstring above says is
    # "not the authority".
    if home.startswith("repo-mirrored:"):
        return "mirrored", f"authored in {home.split(':', 1)[1]}; the catalog only mirrors it"

    if mine in history and current in history:
        i, j = history.index(current), history.index(mine)
        if j < i:
            return (
                f"STALE {i - j}",
                f"yours {mine} ({dates[mine]}), catalog {current} ({dates[current]})",
            )
        return "unpublished", f"yours {mine} ({dates[mine]}) is not on the published branch"

    if mine in history:
        return f"STALE {len(history) - history.index(mine)}", (
            f"yours {mine} ({dates[mine]}), catalog {current}"
        )

    return "DIVERGED", f"yours {mine} is not a version the catalog published"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", action="append", help="skill root (repeatable)")
    ap.add_argument("--index", default=INDEX_URL)
    ap.add_argument("--repo", default=".")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve()
    index = load_index(args.index)
    dirs = discover(repo, args.root)
    if not dirs:
        looked = ", ".join(args.root or ROOTS)
        return _uncertain(f"no SKILL.md found under {looked} in {repo}")

    tally: dict[str, int] = {}
    lines: list[str] = []
    for d in dirs:
        mine = digest((d / "SKILL.md").read_bytes())
        verdict, why = classify(d.name, mine, index)
        head = verdict.split()[0]
        tally[head] = tally.get(head, 0) + 1
        if head in ("current", "local-skill"):
            continue
        lines.append(f"{verdict:12} {d.name}  {why}")
        if head == "STALE":
            lines.append(
                f"{'':12} update:  npx skills add thrillmade/agent-skills "
                f"--skill {d.name}"
            )

    for line in lines:
        print(line)
    order = ["current", "STALE", "DIVERGED", "unpublished", "mirrored", "retired", "local-skill"]
    print(
        f"\n{len(dirs)} skill(s) checked: "
        + ", ".join(f"{tally[k]} {k}" for k in order if k in tally)
    )
    return 1 if tally.get("STALE") or tally.get("DIVERGED") or tally.get("retired") else 0


if __name__ == "__main__":
    sys.exit(main())
