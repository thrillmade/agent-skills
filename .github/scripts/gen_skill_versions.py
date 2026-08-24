#!/usr/bin/env python3
"""Generate docs/skill-versions.json -- the catalog's published version index.

    python3 .github/scripts/gen_skill_versions.py --write

One HTTPS GET answers "is my copy current?" for a subscriber who has no git
access to this repo, no `skills-lock.json` and no CLI: they digest their own
SKILL.md with the rule in `skill_version.py` and look the value up here.

ENUMERATION IS FROM `refs/remotes/origin/*`, AND THAT CHOICE IS LOAD-BEARING.
It is exactly what a fresh `git clone` of this repository has, so the output is
reproducible by anyone. Measured on one machine, same probe, only the refspec
differing:

    origin/main          100 commits   145 blobs   49 slugs
    refs/remotes/origin/*  103 commits   146 blobs   49 slugs
    --remotes            107 commits   147 blobs   49 slugs   (local fetch refs)
    --all                193 commits   155 blobs   50 slugs   (local branches)

`--all` is a property of one workstation. The 50th slug it finds -- `night-mode`
-- reaches no remote ref and never shipped; publishing it would print "STALE,
run `npx skills add ... night-mode`", an instruction that cannot succeed.
`--remotes` unqualified is nearly as bad here: it picked up two `refs/remotes/pr/*`
refs that only exist because of a local fetch refspec.

There is deliberately NO "never decreases" ratchet on the count. Branches on
the remote are deleted and created; a monotonicity rule over a number that
legitimately moves down is a rule nobody can satisfy and everyone learns to
bypass. What IS gated, on every PR and needing no history at all, is that each
`current` equals the digest of the file on disk -- see validate_skills.py.

WHAT IS NOT GATED, STATED PLAINLY: the history rows. They are derived from git,
and `.github/workflows/validate-skills.yml` checks out at depth 1, so CI cannot
recompute them. This is the same defect that disqualifies putting a revision
ordinal in the file itself -- relocating it into the index does not eliminate
it, and pretending otherwise would be the dishonesty this file exists to
replace. The index carries the split in its own `verification` block so a
reader is told which half they can rely on.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import skill_version

# `--remotes=<pattern>` is matched RELATIVE to refs/remotes/, so this is
# `refs/remotes/origin/*`. Spelling it out in full silently matches nothing:
# `git rev-list` exits 0 with no output and the index generates with an empty
# history, which looks entirely plausible. Hence the guard in
# `enumerate_history` -- a zero here is never allowed to be reported as a
# result.
REFSPEC = "origin/*"
PUBLISHING_REF = "origin/main"
OUT = Path("docs/skill-versions.json")

# Every stamped SKILL.md points a reader here, so this file has to answer the
# question on its own rather than assume they arrived knowing what it is.
README = (
    "Content identity for every SKILL.md this catalog has published. "
    "To check a copy you hold, by hand: normalise CRLF to LF, delete the "
    "`version:`, `digest:` and `origin:` lines from its frontmatter, sha256 "
    "the rest, take the first 12 hex characters -- then find your skill's "
    "slug below. Matching `current` means you are up to date; a match in "
    "`history` means you are that many versions behind; no match means your "
    "copy was edited locally. `version` and each row's `version` are the "
    "skill's own semver, null for anything published before that field "
    "existed. To check a whole repo at once, run "
    "https://raw.githubusercontent.com/thrillmade/agent-skills/main/"
    ".github/scripts/skills_current.py -- stdlib only, no install. Update "
    "with `npx skills add thrillmade/agent-skills --skill <slug>`. The "
    "`history` rows are not gated by CI and the `current` values are: see "
    "`verification` below."
)


def git(*args: str, check: bool = True) -> str:
    p = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and p.returncode != 0:
        raise SystemExit(f"error: `git {' '.join(args)}` failed: {p.stderr.strip()}")
    return p.stdout


def enumerate_history() -> tuple[dict[str, list[tuple[str, str, str]]], set[str], dict]:
    """{slug: [(digest, short_sha, when)]} oldest-first, the slugs that have
    ever been on the PUBLISHING branch, and provenance.

    Those two sets are not the same and the difference matters. A slug on a
    feature branch has not been published; a slug that was on `main` and is
    gone from the tree has been retired. Collapsing them makes the index
    announce "the catalog no longer publishes this skill" about skills it has
    never published -- which is what it did, about five of arlyn-working's own
    locally-authored skills, the moment a nomination branch appeared on origin.
    """
    commits = git("rev-list", f"--remotes={REFSPEC}").split()
    if not commits:
        raise SystemExit(
            f"error: `git rev-list --remotes={REFSPEC}` reached 0 commits. "
            "That is a shallow clone, a wrong refspec or a repo with no "
            "`origin` -- not an empty history. Refusing to publish an index "
            "built from nothing. Run in a full clone with a fetched origin."
        )

    # `check=False`: a missing ref is a git error, and the message below says
    # what to do about it rather than surfacing a traceback.
    published = set(git("rev-list", PUBLISHING_REF, check=False).split())
    if not published:
        raise SystemExit(
            f"error: `git rev-list {PUBLISHING_REF}` reached 0 commits, so the "
            "publishing branch cannot be told from a feature branch. Fetch "
            f"{PUBLISHING_REF} before regenerating."
        )
    on_main: set[str] = set()

    # (slug, blob_sha) -> the OLDEST commit that carried it. rev-list is
    # newest-first, so the last write wins.
    seen: dict[tuple[str, str], tuple[str, str]] = {}
    blobs: set[str] = set()
    for sha in commits:
        # Keep the full timestamp for ordering and publish only the date.
        # Two versions of one skill can land on the same day, and sorting the
        # truncated date falls back to comparing the short sha -- which is
        # alphabetical, not chronological, and silently reverses them.
        when = git("show", "-s", "--format=%cI", sha).strip()
        listing = git("ls-tree", "-r", "--format=%(objectname) %(path)", sha, "skills/")
        for line in listing.splitlines():
            obj, path = line.split(" ", 1)
            parts = path.split("/")
            if len(parts) != 3 or parts[2] != "SKILL.md":
                continue
            seen[(parts[1], obj)] = (sha[:7], when)
            blobs.add(obj)
            if sha in published:
                on_main.add(parts[1])

    contents = _batch_read(sorted(blobs))

    # Rows are (digest, semver, short_sha, published date, sort key). The
    # last two differ once a row has been published: see `merge_published`.
    # `semver` is `skill_version.stamped_version` of the SAME blob the digest
    # came from -- a pure function of content, unlike `sha`/`when`, so it
    # needs no append-only protection of its own; every commit before the
    # three-field format shipped reads back None here, because their
    # `version:` line held a digest, not a semver -- the same "no valid
    # claim" case `stamped_version` already treats identically to absence.
    history: dict[str, list[tuple[str, str | None, str, str, str]]] = {}
    for (slug, obj), (sha, when) in seen.items():
        history.setdefault(slug, []).append(
            (
                skill_version.digest(contents[obj]),
                skill_version.stamped_version(contents[obj]),
                sha,
                when[:10],
                when,
            )
        )

    out: dict[str, list[tuple[str, str | None, str, str, str]]] = {}
    for slug, rows in history.items():
        rows.sort(key=lambda r: r[4])
        # Two blobs can normalise to one digest (they differed only in the
        # version/digest/origin lines, which are elided). Keep the earliest
        # appearance.
        dedup: dict[str, tuple[str, str | None, str, str, str]] = {}
        for row in rows:
            dedup.setdefault(row[0], row)
        out[slug] = sorted(dedup.values(), key=lambda r: r[4])

    if not blobs:
        raise SystemExit(
            f"error: {len(commits)} commits reached but 0 SKILL.md blobs under "
            "skills/. The path layout changed or the refspec is wrong; either "
            "way an index with no history is not a finding."
        )

    provenance = {
        "refs": f"refs/remotes/{REFSPEC}",
        "publishing_ref": PUBLISHING_REF,
        "commits": len(commits),
        "blobs": len(blobs),
    }
    return out, on_main, provenance


def _batch_read(shas: list[str]) -> dict[str, bytes]:
    """`git cat-file --batch` over every blob at once -- one subprocess, not
    one per blob."""
    if not shas:
        return {}
    p = subprocess.run(
        ["git", "cat-file", "--batch"],
        input="\n".join(shas).encode() + b"\n",
        capture_output=True,
        check=True,
    )
    out, i, result = p.stdout, 0, {}
    for _ in shas:
        nl = out.index(b"\n", i)
        obj, _kind, size = out[i:nl].split()
        i = nl + 1
        result[obj.decode()] = out[i : i + int(size)]
        i += int(size) + 1
    return result


def merge_published(history: dict[str, list], root: Path) -> dict[str, list]:
    """Union in whatever the committed index already publishes.

    History is APPEND-ONLY, and that is not a nicety. Two people regenerate
    from different fetch states -- one has fetched a branch the other has
    not -- so a generator that replaces history lets whoever has fetched less
    silently delete rows the other published. A subscriber holding one of the
    deleted versions then reads `DIVERGED` instead of `STALE n`.

    Making the generator monotone is also why there is no "never decreases"
    ratchet in CI. A ratchet is a rule that detects the loss after it is
    written and that nobody can satisfy across machines; this makes the loss
    unrepresentable instead.
    """
    path = root / OUT
    if not path.exists():
        return history
    published = json.loads(path.read_text(encoding="utf-8")).get("skills", {})
    for slug, entry in published.items():
        # A published row's `commit`/`date` WIN over a freshly derived one.
        # Once a date is out there a subscriber may have read it, and
        # re-deriving it from a different set of refs can move it. Correcting
        # a published row is then an explicit edit to this file, which is
        # visible in review -- rather than something that happens to whoever
        # regenerates next.
        rows = {r[0]: r for r in history.get(slug, [])}
        for old in entry.get("history", []):
            # Keep the enumerated SORT key where there is one. A published row
            # carries a date, an enumerated row a full timestamp, and mixing
            # the two as strings reorders versions that landed on the same
            # day -- which this catalog already has.
            was = rows.get(old["v"])
            # `version` is NOT append-only the way `commit`/`date` are: it is
            # a pure function of the blob's own bytes, so a freshly-derived
            # value is never wrong, only sometimes MISSING when this run
            # cannot read the blob at all (a digest that only survives in an
            # already-published row, from a ref nobody still fetches). Every
            # row published before this field existed has no "version" key at
            # all -- `.get` reads that the same way `stamped_version` reads a
            # pre-migration blob: as no claim, not as a claim of None.
            version = old.get("version")
            if version is None and was is not None:
                version = was[1]
            rows[old["v"]] = (old["v"], version, old["commit"], old["date"],
                              was[4] if was else old["date"])
        history[slug] = sorted(rows.values(), key=lambda r: r[4])
    return history


def build(root: Path) -> dict:
    history, on_main, provenance = enumerate_history()
    history = merge_published(history, root)
    live = {p.parent.name: p for p in sorted((root / "skills").glob("*/SKILL.md"))}
    if not live:
        raise SystemExit(f"error: no SKILL.md under {root / 'skills'}")

    placement = {}
    pm = root / "docs" / "placement-map.json"
    if pm.exists():
        placement = json.loads(pm.read_text())["skills"]

    skills: dict[str, dict] = {}
    for slug in sorted(set(history) | set(live)):
        rows = history.get(slug, [])
        entry: dict = {}
        if slug in live:
            live_raw = live[slug].read_bytes()
            entry["current"] = skill_version.digest(live_raw)
            # The semver counterpart of `current` -- None for a skill never
            # stamped under the three-field format, same as `stamped_version`
            # itself reads it.
            entry["version"] = skill_version.stamped_version(live_raw)
            # `authoring_home` has exactly one owner -- the CI-gated placement
            # map. Copied, never invented: a slug the map does not carry gets
            # no value rather than a plausible one.
            if slug in placement:
                entry["authoring_home"] = placement[slug]["authoring_home"]
        elif slug in on_main:
            # Published once, gone from the tree. `current: null` says so, and
            # the checker must not tell anyone to reinstall it.
            entry["current"] = None
            entry["version"] = None
            entry["retired"] = True
        else:
            # Seen only on a feature branch. It has never been published, so
            # this index has nothing true to say about it and says nothing:
            # the checker then reports `local-skill`, which is exactly right
            # for a skill somebody else authored and nominated.
            continue
        entry["history"] = [
            {"v": v, "version": ver, "commit": c, "date": d} for v, ver, c, d, _ in rows
        ]
        skills[slug] = entry

    rows_total = sum(len(s["history"]) for s in skills.values())
    return {
        "version": 1,
        "_readme": README,
        "generated_from": "remotes-exhaustive",
        "enumeration": provenance,
        "versions_enumerated": rows_total,
        "verification": {
            "current": (
                "GATED. validate_skills.py recomputes every `current` from "
                "skills/<slug>/SKILL.md on every pull request. Needs no git "
                "history, so it holds at the depth-1 checkout CI uses."
            ),
            "history": (
                "NOT GATED. History is derived from git and validate-skills.yml "
                "checks out at fetch-depth 1, so CI cannot recompute these rows. "
                "Regenerate them in a full clone with "
                "`.github/scripts/gen_skill_versions.py --write`."
            ),
            "history_rows_ungated": rows_total - len(live),
        },
        "skills": skills,
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)

    root = Path(args.root)
    index = build(root)
    text = json.dumps(index, indent=1, sort_keys=False) + "\n"
    if args.write:
        (root / OUT).write_text(text, encoding="utf-8")
        print(
            f"wrote {OUT}: {len(index['skills'])} skills, "
            f"{index['versions_enumerated']} versions, {len(text)} bytes"
        )
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
