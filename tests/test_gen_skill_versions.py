"""`.github/scripts/gen_skill_versions.py` -- the published version index.

Built on a throwaway git repository with real `refs/remotes/origin/*` refs,
because every rule worth testing here is a rule about which refs a fact came
from, and a fixture that fakes that tests nothing.

The rule this file exists for: **a slug on a feature branch has not been
published.** Collapsing "on some branch" into "published" made the index
announce `retired` -- "the catalog no longer publishes this skill" -- about
five skills the catalog had never published, the moment a nomination branch
appeared on origin. They were another repo's own local skills.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

import gen_skill_versions
import skill_version

SKILL = """---
name: {name}
description: What this skill does.
---

# Title

{body}
"""


class Repo:
    def __init__(self, base: Path) -> None:
        self.base = base
        self.git("init", "-q", "-b", "main")
        self.git("config", "user.email", "t@example.com")
        self.git("config", "user.name", "t")

    def git(self, *a: str) -> str:
        p = subprocess.run(["git", *a], cwd=self.base, capture_output=True, text=True)
        assert p.returncode == 0, f"git {a}: {p.stderr}"
        return p.stdout.strip()

    def skill(self, name: str, body: str = "Body.") -> Path:
        d = self.base / "skills" / name
        d.mkdir(parents=True, exist_ok=True)
        p = d / "SKILL.md"
        p.write_text(SKILL.format(name=name, body=body), encoding="utf-8")
        return p

    def commit(self, msg: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)
        return self.git("rev-parse", "HEAD")

    def publish(self, ref: str, sha: str | None = None) -> None:
        """Make `refs/remotes/origin/<ref>` exist, as a fresh clone would."""
        self.git("update-ref", f"refs/remotes/origin/{ref}", sha or self.git("rev-parse", "HEAD"))


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Repo:
    r = Repo(tmp_path)
    monkeypatch.chdir(tmp_path)
    return r


def build(repo: Repo) -> dict:
    return gen_skill_versions.build(repo.base)


# --- the published / merely-pushed distinction -----------------------------


def test_a_skill_on_main_and_in_the_tree_is_published(repo: Repo) -> None:
    p = repo.skill("alpha")
    repo.commit("add alpha")
    repo.publish("main")
    index = build(repo)
    assert index["skills"]["alpha"]["current"] == skill_version.digest(p.read_bytes())
    assert [h["v"] for h in index["skills"]["alpha"]["history"]] == [
        skill_version.digest(p.read_bytes())
    ]


def test_a_skill_only_on_a_feature_branch_is_not_published_at_all(repo: Repo) -> None:
    """The defect. `beta` is somebody's nomination, not this catalog's skill.
    Publishing it as `retired` tells its author the catalog dropped a skill it
    never carried; publishing it as anything at all is a claim we cannot make.
    """
    repo.skill("alpha")
    main = repo.commit("add alpha")
    repo.publish("main", main)

    repo.git("checkout", "-q", "-b", "nomination")
    repo.skill("beta")
    repo.commit("nominate beta")
    repo.publish("nomination")
    repo.git("checkout", "-q", "main")
    assert not (repo.base / "skills" / "beta").exists()  # control: gone from the tree

    index = build(repo)
    assert "alpha" in index["skills"]           # control: the probe finds skills
    assert "beta" not in index["skills"]


def test_a_skill_removed_from_main_is_retired(repo: Repo) -> None:
    repo.skill("alpha")
    repo.skill("gamma")
    repo.commit("add both")
    subprocess.run(["rm", "-rf", str(repo.base / "skills" / "gamma")], check=True)
    repo.commit("retire gamma")
    repo.publish("main")

    index = build(repo)
    assert index["skills"]["gamma"]["current"] is None
    assert index["skills"]["gamma"]["retired"] is True
    assert index["skills"]["gamma"]["history"]  # the old version stays resolvable


# --- history is append-only ------------------------------------------------


def test_a_regeneration_never_drops_a_published_history_row(repo: Repo) -> None:
    """Two people regenerate from different fetch states. Whoever has fetched
    less must not be able to delete rows the other published -- a subscriber
    holding a deleted version would read DIVERGED instead of STALE n.
    """
    p = repo.skill("alpha")
    repo.commit("v1")
    repo.publish("main")
    (repo.base / "docs").mkdir(exist_ok=True)

    index = build(repo)
    index["skills"]["alpha"]["history"].insert(
        0, {"v": "aaaaaaaaaaaa", "commit": "0000000", "date": "2020-01-01"}
    )
    (repo.base / "docs" / "skill-versions.json").write_text(json.dumps(index))

    again = build(repo)
    rows = [h["v"] for h in again["skills"]["alpha"]["history"]]
    assert "aaaaaaaaaaaa" in rows
    assert skill_version.digest(p.read_bytes()) in rows


def test_a_published_rows_date_is_not_rewritten(repo: Repo) -> None:
    repo.skill("alpha")
    repo.commit("v1")
    repo.publish("main")
    (repo.base / "docs").mkdir(exist_ok=True)

    index = build(repo)
    index["skills"]["alpha"]["history"][0]["date"] = "2019-05-05"
    (repo.base / "docs" / "skill-versions.json").write_text(json.dumps(index))

    again = build(repo)
    assert again["skills"]["alpha"]["history"][0]["date"] == "2019-05-05"


# --- refusing to publish an index built from nothing -----------------------


def test_no_origin_refs_is_fatal_not_an_empty_index(repo: Repo) -> None:
    """`git rev-list` exits 0 with no output for a refspec that matches
    nothing, and an index generated from that looks entirely plausible. It
    happened during this lane's own build, from `--remotes=refs/remotes/origin/*`
    -- which is matched relative to refs/remotes/ and so matches nothing.
    """
    repo.skill("alpha")
    repo.commit("v1")
    assert repo.git("rev-parse", "HEAD")  # control: there IS history to find
    with pytest.raises(SystemExit) as e:
        build(repo)
    assert "0 commits" in str(e.value)


def test_no_publishing_ref_is_fatal(repo: Repo) -> None:
    repo.skill("alpha")
    repo.commit("v1")
    repo.publish("nomination")
    with pytest.raises(SystemExit) as e:
        build(repo)
    assert "publishing branch cannot be told from a feature branch" in str(e.value)


def test_no_skills_directory_is_fatal(repo: Repo) -> None:
    (repo.base / "README.md").write_text("x")
    repo.commit("no skills")
    repo.publish("main")
    with pytest.raises(SystemExit) as e:
        build(repo)
    assert "0 SKILL.md blobs" in str(e.value)


# --- provenance is recorded, not asserted ---------------------------------


def test_the_index_records_which_refs_it_was_built_from(repo: Repo) -> None:
    repo.skill("alpha")
    repo.commit("v1")
    repo.publish("main")
    index = build(repo)
    assert index["enumeration"]["refs"] == "refs/remotes/origin/*"
    assert index["enumeration"]["publishing_ref"] == "origin/main"
    assert index["enumeration"]["commits"] >= 1
    assert index["versions_enumerated"] >= 1


def test_authoring_home_is_copied_from_the_placement_map_never_invented(repo: Repo) -> None:
    repo.skill("alpha")
    repo.skill("beta")
    (repo.base / "docs").mkdir(exist_ok=True)
    (repo.base / "docs" / "placement-map.json").write_text(
        json.dumps({"skills": {"alpha": {"authoring_home": "repo-mirrored:logmind"}}})
    )
    repo.commit("v1")
    repo.publish("main")

    index = build(repo)
    assert index["skills"]["alpha"]["authoring_home"] == "repo-mirrored:logmind"
    assert "authoring_home" not in index["skills"]["beta"]
