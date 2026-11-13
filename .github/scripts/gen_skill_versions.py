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

WHAT IS NOT GATED, STATED PLAINLY: the history rows' CONTENT. They are derived
from git, and CI cannot recompute them. This is the same defect that
disqualifies putting a revision ordinal in the file itself -- relocating it into
the index does not eliminate it, and pretending otherwise would be the
dishonesty this file exists to replace. The index carries the split in its own
`verification` block so a reader is told which half they can rely on.

WHAT IS GATED ABOUT THEM, since #290: that every row's VERSION was published.
A squash merge discards the branch commits a row cited, so a row written on a
branch names a commit the integration branch will never carry -- stale, but
repairable, because the same digest is carried by the squash commit. `--check`
therefore has two tiers. It FAILS a row whose digest no commit reachable from
HEAD or a publishing ref carries (a fabricated or never-published version), and
only WARNS about a row whose commit is unreachable but whose digest has a
reachable carrier, naming the repair. "Reachable" includes both publishing refs
-- subscribers install from main, and merged work lives on origin/dev until
promotion -- so a version either ref carries is published. The generator makes the
repair deterministic: it prefers a reachable carrier of each digest, `--write`
re-points a stale row at the earliest one, and prunes a row no reachable commit
carries (a branch-only intermediate a squash did not keep); see
`prune_unreachable`. Admission is stricter than the check: `--write` lets a row
in only if origin/dev or origin/main carries its digest, so a branch regen
records no in-flight row and the squash orphans cannot enter the file at all.

THE PROMOTION BRANCH IS WHERE HISTORY IS COMPLETED (#292). Admission means a
version gets its row only after a squash lands it on origin/dev, and nothing
pushes to dev, so dev's committed file lags by the newest row of every skill
changed since the last promotion. That is harmless -- subscribers read
main -- so the index is regenerated on the `promote/<date>` branch and
`--lag` fails a pull request into main while a row is still missing. It is
never run against dev.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

import skill_version

# The catalog's own list of its names has one owner, and it is not this file.
from census_counters import CATALOG_NAMES

# `--remotes=<pattern>` is matched RELATIVE to refs/remotes/, so this is
# `refs/remotes/origin/*`. Spelling it out in full silently matches nothing:
# `git rev-list` exits 0 with no output and the index generates with an empty
# history, which looks entirely plausible. Hence the guard in
# `enumerate_history` -- a zero here is never allowed to be reported as a
# result.
REFSPEC = "origin/*"
PUBLISHING_REF = "origin/main"
PUBLISHING_REFS = ("origin/dev", PUBLISHING_REF)
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
    "https://raw.githubusercontent.com/thrillmade/thrill-skills/main/"
    ".github/scripts/skills_current.py -- stdlib only, no install. Update "
    "with `npx skills add thrillmade/thrill-skills --skill <slug>`. The "
    "`history` rows are not gated by CI and the `current` values are: see "
    "`verification` below. `catalog` names this catalog's repository and "
    "every name it had before; a copy whose `origin:` names any of them "
    "came from here."
)


def catalog_block() -> dict:
    """The published `catalog` block: the repository's current name and every
    name it had before, both read from `CATALOG_NAMES` (oldest first, the
    present name last) so there is no second list to drift."""
    return {"repository": CATALOG_NAMES[-1], "former_names": list(CATALOG_NAMES[:-1])}


def git(*args: str, check: bool = True) -> str:
    p = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and p.returncode != 0:
        raise SystemExit(f"error: `git {' '.join(args)}` failed: {p.stderr.strip()}")
    return p.stdout


def reachable_commits(rev: str = "HEAD") -> set[str]:
    """Every full sha reachable from `rev`; empty if `rev` does not resolve."""
    return set(git("rev-list", rev, check=False).split())


def published_reachable() -> tuple[set[str], bool]:
    """ADMISSION: the full shas whose carried versions may be a history row,
    and whether a publishing ref contributed.

    A row may enter or stay in the file only if its digest is carried by a
    commit reachable from origin/dev or origin/main -- never bare HEAD, never a
    branch-local commit. This is the one gate every path routes through
    (enumeration's carrier preference, the re-point, the prune). A branch regen
    therefore records no in-flight row at all: the version that churned again
    before the squash would otherwise ride the file onto dev as a digest dev
    never carries. `current` is read from disk and is unaffected; a PR's new
    versions get their rows from the first regen after the squash, citing the
    squash commit. With neither ref present (a local-only repository) HEAD is
    the fallback and the caller says so.
    """
    shas: set[str] = set()
    for ref in PUBLISHING_REFS:
        shas |= reachable_commits(ref)
    if shas:
        return shas, True
    return reachable_commits(), False


def carried_digests(commits: set[str]) -> set[tuple[str, str]]:
    """{(slug, digest)} of every SKILL.md carried by any of `commits`."""
    blobs: dict[str, set[str]] = {}
    for sha in commits:
        listing = git("ls-tree", "-r", "--format=%(objectname) %(path)", sha, "skills/")
        for line in listing.splitlines():
            obj, path = line.split(" ", 1)
            parts = path.split("/")
            if len(parts) == 3 and parts[2] == "SKILL.md":
                blobs.setdefault(obj, set()).add(parts[1])
    contents = _batch_read(sorted(blobs))
    return {
        (slug, skill_version.digest(contents[obj]))
        for obj, slugs in blobs.items()
        for slug in slugs
    }


def enumerate_history() -> tuple[dict[str, list[tuple[str, str, str]]], set[str], dict]:
    """{slug: [(digest, short_sha, when)]} oldest-first, the slugs that have
    ever been on the PUBLISHING branch, and provenance.

    Those two sets are not the same and the difference matters. A slug on a
    feature branch has not been published; a slug that was on `main` and is
    gone from the tree has been retired. Collapsing them makes the index
    announce "the catalog no longer publishes this skill" about skills it has
    never published -- which is what it did, about five of a private consumer repo's own
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

    # Plus whatever HEAD reaches that no remote ref does (an unpushed local
    # commit): a reachable carrier must be findable or the prune below would
    # read its row as carried by nothing.
    known = set(commits)
    commits += [c for c in git("rev-list", "HEAD", check=False).split() if c not in known]

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

    # Commits that admit a row (see `published_reachable`). A squash merge
    # leaves the branch commits behind, so the oldest carrier of a blob may be
    # one dev will never have; an admitted carrier always outranks it.
    reachable, _ = published_reachable()

    # (slug, blob_sha) -> the OLDEST commit that carried it, among the
    # reachable ones where any exists. rev-list is newest-first, so the last
    # write wins -- except that an unreachable commit never displaces a
    # reachable one.
    seen: dict[tuple[str, str], tuple[str, str]] = {}
    seen_full: dict[tuple[str, str], str] = {}
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
            key = (parts[1], obj)
            prior = seen_full.get(key)
            if prior is None or sha in reachable or prior not in reachable:
                seen[key] = (sha[:7], when)
                seen_full[key] = sha
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
    reach7 = {c[:7] for c in reachable}
    # The timestamp alone is not a total order: commits land in the same
    # second on a fast runner, and %cI cannot see inside a second. The only
    # sub-second chronology git has is topology, so ties break by rev-list
    # rank, oldest first (rev-list is newest-first, hence the negation).
    # A row whose commit this enumeration never walked (a published legacy
    # row) ranks oldest within its tie; the sha is a determinism backstop
    # among those only. HEAD-only commits sit after the remote ones in
    # `commits`, so within a tie they also read as oldest -- they can carry
    # re-point candidates but never admitted rows, so order there is moot.
    rank = {sha[:7]: i for i, sha in enumerate(commits)}
    never = len(commits)
    row_order = lambda r: (r[4], -rank.get(r[2], never), r[2])  # noqa: E731
    for slug, rows in history.items():
        rows.sort(key=row_order)
        # Two blobs can normalise to one digest (they differed only in the
        # version/digest/origin lines, which are elided). Keep the earliest
        # appearance.
        dedup: dict[str, tuple[str, str | None, str, str, str]] = {}
        # Earliest REACHABLE row per digest, earliest overall only when none is
        # reachable: the earliest carrier can be a branch commit a squash
        # dropped while a reachable commit carries the same digest, and
        # keeping the former hides the latter from the re-point and the prune.
        for row in rows:
            held = dedup.get(row[0])
            if held is None or (held[2] not in reach7 and row[2] in reach7):
                dedup[row[0]] = row
        out[slug] = sorted(dedup.values(), key=row_order)

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
    reachable = {c[:7] for c in published_reachable()[0]}
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
            # The one exception to "published wins", and only for the commit:
            # a row citing a commit this checkout cannot reach (a branch
            # commit a squash merge removed) is re-pointed at the fresh
            # enumeration's carrier of the SAME digest when that one is
            # reachable. The date stays -- it is what a subscriber read.
            commit = old["commit"]
            if commit not in reachable and was is not None and was[2] in reachable:
                commit = was[2]
            rows[old["v"]] = (old["v"], version, commit, old["date"],
                              was[4] if was else old["date"])
        history[slug] = sorted(rows.values(), key=lambda r: r[4])
    return history


def prune_unreachable(
    history: dict[str, list],
    root: Path,
    pruned: list[tuple[str, str, str]] | None = None,
    skipped: list[tuple[str, str, str]] | None = None,
) -> dict[str, list]:
    """Drop every row whose commit this checkout (or origin/main) cannot reach.

    `pruned` collects the rows that were in the published file and are now
    gone; `skipped` the branch-only versions enumeration found that were never
    in it, which are not added and so are not "pruned".

    By the time this runs `merge_published` and the enumeration have already
    re-pointed every row that HAS a reachable carrier, so a row still citing an
    unreachable commit is one NO reachable commit carries: a version that only
    ever existed on a branch (an intermediate state a squash merge never kept)
    and so was never published. This file is the record of PUBLISHED versions
    -- the digests a subscriber's copy is classified against -- so such a row
    is a regen-on-branch artifact, not history, and append-only protection is
    for the real kind. Both conditions must hold, in the never-guess spirit of
    the repair: reachable-but-unmatched is kept, unreachable-but-matched was
    re-pointed above. On a PR branch a version in flight is reachable from the
    branch HEAD, so it is never pruned before the squash.
    """
    reachable = {c[:7] for c in published_reachable()[0]}
    in_file: set[tuple[str, str]] = set()
    path = root / OUT
    if path.exists():
        for slug, entry in json.loads(path.read_text(encoding="utf-8")).get("skills", {}).items():
            in_file.update((slug, r["v"]) for r in entry.get("history", []))
    for slug, rows in history.items():
        kept = []
        for row in rows:
            if row[2] in reachable:
                kept.append(row)
                continue
            bucket = pruned if (slug, row[0]) in in_file else skipped
            if bucket is not None:
                bucket.append((slug, row[0], row[2]))
        history[slug] = kept
    return history


def rows_ungated(skills: dict[str, dict]) -> int:
    """History rows CI cannot recompute: every row except a live skill's
    current one, which validate_skills.py recomputes from the tree.

    Counted from the rows, not as `rows - live skills`: a live skill with no
    row for its current digest (an in-flight edit, a skill not yet on main)
    gates nothing, so subtracting it per skill went negative on a small
    catalog and undercounted on this one.
    """
    gated = sum(
        1
        for e in skills.values()
        if e["current"] is not None and any(r["v"] == e["current"] for r in e["history"])
    )
    return sum(len(e["history"]) for e in skills.values()) - gated


def build(
    root: Path,
    pruned: list[tuple[str, str, str]] | None = None,
    skipped: list[tuple[str, str, str]] | None = None,
) -> dict:
    history, on_main, provenance = enumerate_history()
    history = merge_published(history, root)
    history = prune_unreachable(history, root, pruned, skipped)
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
        "catalog": catalog_block(),
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
                "NOT GATED. History content is derived from git and CI "
                "cannot recompute these rows; only that every row's `commit` "
                "is an ancestor of the checked revision is gated "
                "(`gen_skill_versions.py --check`). Regenerate them in a full "
                "clone with `.github/scripts/gen_skill_versions.py --write`."
            ),
            "history_rows_ungated": rows_ungated(skills),
        },
        "skills": skills,
    }


def stale_rows(
    root: Path, head: str
) -> tuple[list[tuple[str, str, str, str]], list[tuple[str, str, str, str]], bool]:
    """(failing, stale, main_present). Both lists hold (slug, digest, commit,
    why) for published rows whose `commit` is not an ancestor of `head`.

    `failing` rows have a digest NO commit reachable from `head` or a
    publishing ref (origin/dev, origin/main) carries -- fabricated or never
    published. `stale` rows have a reachable carrier, so the pointer is
    repairable by `--write`. One definition of "published" serves admission
    and this check alike: `published_reachable()`.

    Refuses on a shallow clone: there an ancestor looks missing, and a gate
    that reports on a history it cannot see is reporting on the clone.
    """
    if git("rev-parse", "--is-shallow-repository").strip() == "true":
        raise SystemExit(
            "error: shallow clone. Ancestry cannot be checked without the "
            "full history; fetch with depth 0 before running --check."
        )
    if subprocess.run(
        ["git", "rev-parse", "--verify", "-q", f"{head}^{{commit}}"],
        capture_output=True,
    ).returncode != 0:
        raise SystemExit(f"error: `{head}` does not resolve to a commit.")
    published = json.loads((root / OUT).read_text(encoding="utf-8")).get("skills", {})
    reach = reachable_commits(head)
    pub, pub_present = published_reachable()
    carried: set[tuple[str, str]] | None = None
    failing, stale = [], []
    for slug, entry in published.items():
        for row in entry.get("history", []):
            rc = subprocess.run(
                ["git", "merge-base", "--is-ancestor", row["commit"], head],
                capture_output=True,
            ).returncode
            if rc == 0:
                continue
            if carried is None:
                carried = carried_digests(reach | pub)
            why = "not an ancestor" if rc == 1 else "not a commit in this clone"
            (stale if (slug, row["v"]) in carried else failing).append(
                (slug, row["v"], row["commit"], why)
            )
    return failing, stale, pub_present


def check(root: Path, head: str) -> int:
    """Two tiers, deliberately. FAILS a row whose digest nothing reachable from
    `head` or a publishing ref carries: published-version integrity is the property
    protected. WARNS about a row whose pointer is unreachable but whose digest
    is carried: pointers are repairable metadata, so a fabricated pointer
    beside a real digest is accepted by design. `--write` admits rows only
    from origin/dev and origin/main, so this state does not arise from it."""
    failing, stale, pub_present = stale_rows(root, head)
    if not pub_present:
        print(f"note: neither origin/dev nor origin/main is present; reachability considered {head} alone")
    for slug, v, commit, why in stale:
        print(f"::warning file={OUT}::{slug} {v}: commit {commit} is {why} of {head}, but a reachable commit carries this digest")
    if stale:
        print(
            f"{len(stale)} stale history row(s): repair with "
            "`python3 .github/scripts/gen_skill_versions.py --write` in a full "
            "clone with origin fetched, then commit docs/skill-versions.json."
        )
    for slug, v, commit, why in failing:
        print(f"::error file={OUT}::{slug} {v}: commit {commit} is {why} of {head} and no commit reachable from {head} or a publishing ref carries this digest")
    if failing:
        print(
            f"{len(failing)} history row(s) name a version nothing reachable "
            "carries -- fabricated or never published. `--write` prunes them."
        )
        return 1
    print(f"OK: every history row's digest is carried by a commit reachable from {head} or a publishing ref (origin/dev, origin/main).")
    return 0


class LagReport(NamedTuple):
    missing: list[tuple[str, str, str, str]]  # (slug, digest, commit, date)
    repointed: list[tuple[str, str, str, str]]  # (slug, digest, new commit, old commit)
    unpublished: list[tuple[str, str, str]]  # (slug, version, commit)
    skills: int
    versions: int


def missing_rows(root: Path, head: str) -> LagReport:
    """What a fresh build would change in the committed file, restricted to
    commits reachable from `head` (those are the versions this branch promotes;
    one merged into dev after the branch was cut is not demanded of it):
    `missing` rows it would add, `repointed` rows whose commit it would change,
    and `unpublished` versions the live tree carries that no publishing ref
    does -- the admission rule keeps those out of the index, so no row can be
    built for them yet. `skills` and `versions` count what was examined.
    Nothing is written."""
    path = root / OUT
    committed = json.loads(path.read_text(encoding="utf-8")).get("skills", {}) if path.exists() else {}
    reach7 = {c[:7] for c in reachable_commits(head)}
    missing, repointed = [], []
    skipped: list[tuple[str, str, str]] = []
    index = build(root, skipped=skipped)
    for slug, entry in index["skills"].items():
        had = {r["v"]: r for r in committed.get(slug, {}).get("history", [])}
        for row in entry["history"]:
            old = had.get(row["v"])
            if old is None:
                if row["commit"] in reach7:
                    missing.append((slug, row["v"], row["commit"], row["date"]))
            elif old["commit"] != row["commit"]:
                repointed.append((slug, row["v"], row["commit"], old["commit"]))
    unpublished = []
    for slug, digest, commit in skipped:
        live = root / "skills" / slug / "SKILL.md"
        if commit in reach7 and live.exists():
            raw = live.read_bytes()
            if skill_version.digest(raw) == digest:
                unpublished.append((slug, skill_version.stamped_version(raw) or digest, commit))
    return LagReport(
        missing,
        repointed,
        sorted(set(unpublished)),
        len(index["skills"]),
        index["versions_enumerated"],
    )


def lag(root: Path, head: str) -> int:
    """Fail while this branch carries a version whose history row is missing.

    A version whose commit is on neither origin/dev nor origin/main (made on
    the promotion branch itself, or on a pull request into main that skips dev)
    cannot get a row: admission cites only those two refs, because a squash
    leaves a pull request branch's commits unreachable. That is a warning, not
    a failure -- the next promotion's regeneration adds the row once the change
    is on dev or main -- so a skill is not changed on the promotion branch."""
    if git("rev-parse", "--is-shallow-repository").strip() == "true":
        raise SystemExit(
            "error: shallow clone. The history cannot be rebuilt without the "
            "full history; fetch with depth 0 before running --lag."
        )
    if subprocess.run(
        ["git", "rev-parse", "--verify", "-q", f"{head}^{{commit}}"],
        capture_output=True,
    ).returncode != 0:
        raise SystemExit(f"error: `{head}` does not resolve to a commit.")
    missing, repointed, unpublished, skills, versions = missing_rows(root, head)
    if skills == 0 or versions == 0:
        print(f"::error file={OUT}::--lag examined {skills} skill(s) and {versions} version(s); a check that examined nothing is not a pass")
        return 1
    for slug, v, new, old in repointed:
        print(f"::warning file={OUT}::{slug} {v}: a fresh build cites commit {new}, the committed row cites {old}")
    for slug, version, commit in unpublished:
        print(
            f"::warning file={OUT}::{slug} {version}: carried by {commit}, which is on neither "
            "origin/dev nor origin/main, so no history row can be built for it yet; the next "
            "promotion's regeneration adds it once the change is on dev or main"
        )
    for slug, v, commit, date in missing:
        print(f"::error file={OUT}::{slug} {v}: published at {commit} ({date}) but has no history row")
    if missing:
        print(
            f"{len(missing)} history row(s) missing. Repair on this branch: "
            "python3 .github/scripts/gen_skill_versions.py --write, then "
            f"commit {OUT}."
        )
        return 1
    print(f"OK: history is complete for {head}: compared {versions} history row(s) across {skills} skill(s) in a fresh build; that is the whole catalog, not the versions this branch promotes.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true")
    ap.add_argument(
        "--check",
        action="store_true",
        help="fail if any history row names a digest no commit reachable from --head or a publishing ref (origin/dev, origin/main) carries; warn on stale pointers",
    )
    ap.add_argument(
        "--lag",
        action="store_true",
        help="fail if a fresh build would add a history row for a version --head carries (run on the promotion into main); writes nothing",
    )
    ap.add_argument("--head", default="HEAD", help="revision --check and --lag measure against")
    ap.add_argument("--root", default=".")
    args = ap.parse_args(argv)

    root = Path(args.root)
    if args.check:
        return check(root, args.head)
    if args.lag:
        return lag(root, args.head)
    pruned: list[tuple[str, str, str]] = []
    skipped: list[tuple[str, str, str]] = []
    index = build(root, pruned, skipped)
    text = json.dumps(index, indent=1, sort_keys=False) + "\n"
    if args.write:
        (root / OUT).write_text(text, encoding="utf-8")
        for slug, v, commit in pruned:
            print(f"pruned {slug} {v} (commit {commit}: unreachable, carried by no reachable commit)")
        print(f"pruned {len(pruned)} unpublished row(s)")
        if skipped:
            print(f"skipped {len(skipped)} branch-only never-published version(s)")
        if not published_reachable()[1]:
            print("note: neither origin/dev nor origin/main is present; admission used HEAD alone")
        print(
            f"wrote {OUT}: {len(index['skills'])} skills, "
            f"{index['versions_enumerated']} versions, {len(text)} bytes"
        )
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
