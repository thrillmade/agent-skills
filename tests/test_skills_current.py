"""The consumer checker -- `.github/scripts/skills_current.py`.

This is the only artifact a subscriber actually runs, so the tests that
matter are the ones about being wrong in their repo rather than in ours:

  * it must carry the SAME digest rule the catalog gates against, or the two
    disagree and every verdict it prints is noise;
  * it must find their skills wherever they keep them -- measured across 20
    sibling repos, `.agents/skills` exists in 3 and `.claude/skills` in 12,
    and in the repos with both the second is symlinks into the first;
  * it must exit 2 rather than 0 whenever it examined nothing, because a run
    over an empty directory prints success exactly as loudly as a real one.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import skill_version
import skills_current

from conftest import SCRIPTS

REPO = SCRIPTS.parents[1]
SCRIPT = SCRIPTS / "skills_current.py"

SKILL = """---
name: {name}
description: What this skill does.
---

# Title

Body {n}.
"""


def write_skill(root: Path, name: str, n: int = 0) -> Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    p = d / "SKILL.md"
    p.write_text(SKILL.format(name=name, n=n), encoding="utf-8")
    return p


def write_index(base: Path, skills: dict) -> Path:
    p = base / "index.json"
    p.write_text(json.dumps({"version": 1, "skills": skills}), encoding="utf-8")
    return p


def run(*args: str) -> subprocess.CompletedProcess:
    """No pipe. The exit code comes from the process."""
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


# --- one rule, two copies, gated to agree ----------------------------------


def test_the_checker_and_the_catalog_agree_on_every_catalog_skill() -> None:
    files = sorted((REPO / "skills").glob("*/SKILL.md"))
    assert len(files) >= 40  # control for the zero
    for f in files:
        raw = f.read_bytes()
        assert skills_current.digest(raw) == skill_version.digest(raw), f.parent.name


@pytest.mark.parametrize(
    "raw",
    [
        b"---\nname: a\n---\n\n# T\n\nB.\n",
        b'---\nname: a\nversion: "aaaaaaaaaaaa"\n---\n\n# T\n\nB.\n',
        b"---\nname: a\nversion: banana\n---\n\n# T\n\nB.\n",
        b"---\r\nname: a\r\n---\r\n\r\n# T\r\n\r\nB.\r\n",
        b"no frontmatter at all\n",
        b"---\nname: a\nmetadata:\n  version: 3\n---\n\n# T\n\nB.\n",
    ],
)
def test_the_two_copies_agree_on_the_awkward_shapes(raw: bytes) -> None:
    assert skills_current.digest(raw) == skill_version.digest(raw)


# --- discovery -------------------------------------------------------------


def test_both_roots_are_discovered(tmp_path: Path) -> None:
    write_skill(tmp_path / ".agents" / "skills", "alpha")
    write_skill(tmp_path / ".claude" / "skills", "beta")
    found = {d.name for d in skills_current.discover(tmp_path, None)}
    assert found == {"alpha", "beta"}


def test_a_symlinked_copy_is_counted_once(tmp_path: Path) -> None:
    """`.claude/skills/<slug>` is a symlink into `.agents/skills/<slug>` in
    every repo here that has both -- 17 of 17 in arlyn-delivery. Counting the
    link and its target separately double-reports the whole install.
    """
    real = write_skill(tmp_path / ".agents" / "skills", "alpha").parent
    link_root = tmp_path / ".claude" / "skills"
    link_root.mkdir(parents=True)
    (link_root / "alpha").symlink_to(real)
    assert (link_root / "alpha" / "SKILL.md").is_file()  # control: the link works
    assert [d.name for d in skills_current.discover(tmp_path, None)] == ["alpha"]


def test_a_directory_without_a_skill_md_is_skipped(tmp_path: Path) -> None:
    (tmp_path / ".claude" / "skills" / "empty").mkdir(parents=True)
    write_skill(tmp_path / ".claude" / "skills", "alpha")
    assert [d.name for d in skills_current.discover(tmp_path, None)] == ["alpha"]


# --- refusing to report success over nothing -------------------------------


def test_no_roots_at_all_exits_2(tmp_path: Path) -> None:
    index = write_index(tmp_path, {"alpha": {"current": "a" * 12, "history": []}})
    p = run("--repo", str(tmp_path), "--index", str(index))
    assert p.returncode == 2, p.stdout
    assert "no SKILL.md found" in p.stderr


def test_an_empty_root_exits_2(tmp_path: Path) -> None:
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    index = write_index(tmp_path, {"alpha": {"current": "a" * 12, "history": []}})
    p = run("--repo", str(tmp_path), "--index", str(index))
    assert p.returncode == 2, p.stdout


def test_an_explicit_root_that_does_not_exist_exits_2(tmp_path: Path) -> None:
    """The spec's documented default was `--root .agents/skills`, which 8 of
    11 repos here do not have. Under the old behaviour that printed
    "0 current, 0 stale" and exited 0.
    """
    write_skill(tmp_path / ".claude" / "skills", "alpha")
    index = write_index(tmp_path, {"alpha": {"current": "a" * 12, "history": []}})
    p = run("--repo", str(tmp_path), "--index", str(index), "--root", ".agents/skills")
    assert p.returncode == 2, p.stdout
    assert "is not a directory" in p.stderr


def test_an_unreachable_index_exits_2(tmp_path: Path) -> None:
    write_skill(tmp_path / ".claude" / "skills", "alpha")
    p = run("--repo", str(tmp_path), "--index", str(tmp_path / "nope.json"))
    assert p.returncode == 2, p.stdout
    assert "could not read the version index" in p.stderr


def test_an_index_listing_no_skills_exits_2(tmp_path: Path) -> None:
    write_skill(tmp_path / ".claude" / "skills", "alpha")
    index = write_index(tmp_path, {})
    p = run("--repo", str(tmp_path), "--index", str(index))
    assert p.returncode == 2, p.stdout
    assert "lists no skills" in p.stderr


def test_a_bad_host_exits_2(tmp_path: Path) -> None:
    write_skill(tmp_path / ".claude" / "skills", "alpha")
    p = run("--repo", str(tmp_path), "--index",
            "https://this-host-does-not-exist.invalid/x.json")
    assert p.returncode == 2, p.stdout


# --- the verdicts ----------------------------------------------------------


def _classify(mine: str, entry: dict | None) -> tuple[str, str]:
    index = {"skills": {"alpha": entry} if entry is not None else {}}
    return skills_current.classify("alpha", mine, index)


def test_a_matching_digest_is_current() -> None:
    assert _classify("aaaaaaaaaaaa", {"current": "aaaaaaaaaaaa", "history": []})[0] == "current"


def test_a_digest_earlier_in_history_is_stale_by_its_distance() -> None:
    entry = {
        "current": "cccccccccccc",
        "history": [
            {"v": "aaaaaaaaaaaa", "date": "2026-01-01", "commit": "1111111"},
            {"v": "bbbbbbbbbbbb", "date": "2026-02-01", "commit": "2222222"},
            {"v": "cccccccccccc", "date": "2026-03-01", "commit": "3333333"},
        ],
    }
    assert _classify("aaaaaaaaaaaa", entry)[0] == "STALE 2"
    assert _classify("bbbbbbbbbbbb", entry)[0] == "STALE 1"


def test_a_digest_after_current_is_not_called_stale() -> None:
    """A version that exists in the catalog but sits after what main
    publishes is a branch build. Calling it "stale" and telling the holder to
    reinstall would move them BACKWARDS.
    """
    entry = {
        "current": "aaaaaaaaaaaa",
        "history": [
            {"v": "aaaaaaaaaaaa", "date": "2026-01-01", "commit": "1111111"},
            {"v": "bbbbbbbbbbbb", "date": "2026-02-01", "commit": "2222222"},
        ],
    }
    assert _classify("bbbbbbbbbbbb", entry)[0] == "unpublished"


def test_an_unknown_digest_is_diverged() -> None:
    entry = {"current": "aaaaaaaaaaaa", "history": []}
    assert _classify("ffffffffffff", entry)[0] == "DIVERGED"


def test_an_unknown_slug_is_a_local_skill_not_an_accusation() -> None:
    """arlyn-working authors 6 skills of its own alongside 23 subscribed
    ones. Reporting those 6 as edited-locally would be six accusations
    against files this catalog has never had an opinion about.
    """
    verdict, why = _classify("ffffffffffff", None)
    assert verdict == "local-skill"
    assert "nothing to compare" in why


def test_a_repo_mirrored_skill_is_not_accused_of_diverging() -> None:
    entry = {
        "current": "aaaaaaaaaaaa",
        "authoring_home": "repo-mirrored:logmind",
        "history": [],
    }
    verdict, why = _classify("ffffffffffff", entry)
    assert verdict == "mirrored"
    assert "logmind" in why


def test_a_repo_mirrored_skill_already_in_history_is_still_mirrored_not_stale() -> None:
    """The defect: an authoring repo's own digest can land in THIS catalog's
    history (a mirror sync captured it once), which put the `mine in history
    and current in history` branch ahead of the `repo-mirrored:` branch and
    made this classify STALE -- telling the authoring repo to
    `npx skills add` its own source from a mirror that is, by the module
    docstring's own words, "not the authority".
    """
    entry = {
        "current": "cccccccccccc",
        "authoring_home": "repo-mirrored:logmind",
        "history": [
            {"v": "aaaaaaaaaaaa", "date": "2026-01-01", "commit": "1111111"},
            {"v": "cccccccccccc", "date": "2026-02-01", "commit": "2222222"},
        ],
    }
    verdict, why = _classify("aaaaaaaaaaaa", entry)
    assert verdict == "mirrored"
    assert "logmind" in why


def test_a_retired_skill_never_produces_an_install_instruction(tmp_path: Path) -> None:
    """A slug the catalog no longer publishes has no version to install.
    Printing `npx skills add ... <slug>` for it is an instruction that
    cannot succeed.

    It DOES exit nonzero, though: `retired` means a copy is behind a skill
    the catalog dropped entirely, and the exit-code table says so -- a
    docstring promising 1 "for something stale or diverged" while the code
    folded this into the silent-0 bucket was the exact silent all-clear this
    mechanism exists to close.
    """
    write_skill(tmp_path / ".claude" / "skills", "alpha")
    index = write_index(tmp_path, {
        "alpha": {"current": None, "retired": True, "history": [
            {"v": "aaaaaaaaaaaa", "date": "2026-01-01", "commit": "1111111"}]},
    })
    p = run("--repo", str(tmp_path), "--index", str(index))
    assert "retired" in p.stdout
    assert "npx skills add" not in p.stdout
    assert p.returncode == 1, p.stdout


def test_an_unpublished_branch_build_still_exits_0(tmp_path: Path) -> None:
    """`unpublished` is explicitly NOT behind (see the docstring) -- a
    feature-branch build ahead of what `current` names. Unlike `retired`,
    this one stays in the exit-0 bucket, and the docstring says so.
    """
    p = write_skill(tmp_path / ".claude" / "skills", "alpha", n=1)
    mine = skill_version.digest(p.read_bytes())
    index = write_index(tmp_path, {
        "alpha": {"current": "aaaaaaaaaaaa", "history": [
            {"v": "aaaaaaaaaaaa", "date": "2026-01-01", "commit": "1111111"},
            {"v": mine, "date": "2026-02-01", "commit": "2222222"},
        ]},
    })
    r = run("--repo", str(tmp_path), "--index", str(index))
    assert "unpublished" in r.stdout
    assert r.returncode == 0, r.stdout


# --- end to end ------------------------------------------------------------


def test_a_current_install_reports_current_and_exits_0(tmp_path: Path) -> None:
    p = write_skill(tmp_path / ".claude" / "skills", "alpha")
    index = write_index(tmp_path, {
        "alpha": {"current": skill_version.digest(p.read_bytes()), "history": []},
    })
    r = run("--repo", str(tmp_path), "--index", str(index))
    assert r.returncode == 0, r.stdout + r.stderr
    assert "1 current" in r.stdout


def test_a_stale_install_reports_it_and_exits_1(tmp_path: Path) -> None:
    p = write_skill(tmp_path / ".claude" / "skills", "alpha", n=1)
    old = skill_version.digest(p.read_bytes())
    index = write_index(tmp_path, {
        "alpha": {"current": "cccccccccccc", "history": [
            {"v": old, "date": "2026-01-01", "commit": "1111111"},
            {"v": "cccccccccccc", "date": "2026-02-01", "commit": "2222222"},
        ]},
    })
    r = run("--repo", str(tmp_path), "--index", str(index))
    assert r.returncode == 1, r.stdout
    assert "STALE 1" in r.stdout
    assert "npx skills add thrillmade/agent-skills --skill alpha" in r.stdout


def test_the_catalog_answers_its_own_checker_as_current(tmp_path: Path) -> None:
    """End to end against the shipped index and the shipped skills: a repo
    holding today's catalog files must come back entirely current. If this
    goes red the index and the tree have drifted.
    """
    root = tmp_path / ".claude" / "skills"
    root.mkdir(parents=True)
    files = sorted((REPO / "skills").glob("*/SKILL.md"))
    assert len(files) >= 40  # control
    for f in files:
        d = root / f.parent.name
        d.mkdir()
        (d / "SKILL.md").write_bytes(f.read_bytes())
    r = run("--repo", str(tmp_path), "--index", str(REPO / "docs" / "skill-versions.json"))
    assert r.returncode == 0, r.stdout + r.stderr
    assert f"{len(files)} current" in r.stdout
