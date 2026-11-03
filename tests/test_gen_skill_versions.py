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
import os
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

    def commit(self, msg: str, date: str | None = None) -> str:
        self.git("add", "-A")
        args = ["commit", "-q", "-m", msg]
        env = None
        if date is not None:
            env = {**os.environ, "GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date}
        p = subprocess.run(["git", *args], cwd=self.base, capture_output=True, text=True, env=env)
        assert p.returncode == 0, f"git {args}: {p.stderr}"
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
        0, {"v": "aaaaaaaaaaaa", "commit": repo.git("rev-parse", "--short=7", "HEAD"), "date": "2020-01-01"}
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
    # Match text unique to THIS guard. `"0 commits"` also appears in the
    # publishing-ref guard immediately below it, so asserting on that passed
    # with this guard deleted -- the test was green on the next guard's
    # message, which is not a pass about this one.
    assert "Refusing to publish an index built from nothing" in str(e.value)


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


# --- history row order is the meaning, and nothing else pins it -----------


def test_history_rows_are_ascending_chronological_order(repo: Repo) -> None:
    """`skills_current.classify` computes `STALE n` from `history.index()` --
    the row order IS what "n versions behind" means, oldest first. Nothing
    else in this file asserts it: three sort sites (`enumerate_history`
    twice, `merge_published` once) all key on the same timestamp, and a
    `reverse=True` at any of them silently turns a two-versions-behind copy
    into `unpublished`, which reads as fine.
    """
    p = repo.skill("alpha", body="Body 1.")
    v1 = skill_version.digest(p.read_bytes())
    repo.commit("v1", date="2024-01-01T00:00:00")

    p = repo.skill("alpha", body="Body 2.")
    v2 = skill_version.digest(p.read_bytes())
    repo.commit("v2", date="2024-06-01T00:00:00")

    p = repo.skill("alpha", body="Body 3.")
    v3 = skill_version.digest(p.read_bytes())
    repo.commit("v3", date="2025-01-01T00:00:00")
    repo.publish("main")

    index = build(repo)
    rows = [h["v"] for h in index["skills"]["alpha"]["history"]]
    assert len({v1, v2, v3}) == 3  # control: three genuinely distinct versions
    assert rows == [v1, v2, v3]


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


# --- the `version` (semver) field ------------------------------------------


def test_a_live_skills_semver_is_read_from_its_own_frontmatter(repo: Repo) -> None:
    p = repo.skill("alpha")
    p.write_bytes(skill_version.stamp(p.read_bytes()))
    repo.commit("add alpha, stamped")
    repo.publish("main")
    index = build(repo)
    assert index["skills"]["alpha"]["version"] == "1.0.0"


def test_an_unstamped_live_skill_has_a_null_version(repo: Repo) -> None:
    repo.skill("alpha")  # SKILL.md with no version:/digest:/origin: lines
    repo.commit("add alpha")
    repo.publish("main")
    index = build(repo)
    assert index["skills"]["alpha"]["version"] is None


def test_history_rows_carry_the_semver_of_their_own_blob(repo: Repo) -> None:
    """Old-style and unstamped blobs read `version: None` -- `stamped_version`
    does not match a bare digest or nothing at all -- and the one blob
    committed under the three-field format reads its real semver.
    """
    p = repo.skill("alpha", body="v1")
    repo.commit("v1, unstamped", date="2024-01-01T00:00:00")

    p = repo.skill("alpha", body="v2")
    p.write_bytes(skill_version.stamp(p.read_bytes()))
    v2 = skill_version.digest(p.read_bytes())
    repo.commit("v2, stamped", date="2024-06-01T00:00:00")
    repo.publish("main")

    index = build(repo)
    rows = {h["v"]: h["version"] for h in index["skills"]["alpha"]["history"]}
    assert len(rows) == 2  # control: two genuinely distinct rows
    assert rows[v2] == "1.0.0"
    unstamped_digest = [v for v in rows if v != v2][0]
    assert rows[unstamped_digest] is None


def test_a_regeneration_fills_in_a_missing_version_from_the_fresh_enumeration(
    repo: Repo,
) -> None:
    """`version` is a pure function of the blob's own bytes, unlike
    `commit`/`date` -- so a row published before this field existed (no
    `version` key at all) must not silently keep reading `null` forever once
    a run CAN recompute it. `commit`/`date` still win from the published row
    (append-only); `version` does not need that protection and must not lose
    data to it.
    """
    p = repo.skill("alpha")
    p.write_bytes(skill_version.stamp(p.read_bytes()))
    repo.commit("v1")
    repo.publish("main")
    (repo.base / "docs").mkdir(exist_ok=True)

    index = build(repo)
    # Simulate a row published by the code before this field existed: same
    # digest, no `version` key at all.
    del index["skills"]["alpha"]["history"][0]["version"]
    (repo.base / "docs" / "skill-versions.json").write_text(json.dumps(index))

    again = build(repo)
    assert again["skills"]["alpha"]["history"][0]["version"] == "1.0.0"


def test_a_published_version_is_not_overwritten_by_a_fresh_derivation(repo: Repo) -> None:
    """Once out, `version` -- like `commit`/`date` -- is corrected by an
    explicit edit to the checked-in file, visible in review, not by whatever
    a regeneration happens to recompute.
    """
    p = repo.skill("alpha")
    p.write_bytes(skill_version.stamp(p.read_bytes()))
    repo.commit("v1")
    repo.publish("main")
    (repo.base / "docs").mkdir(exist_ok=True)

    index = build(repo)
    index["skills"]["alpha"]["history"][0]["version"] = "9.9.9"
    (repo.base / "docs" / "skill-versions.json").write_text(json.dumps(index))

    again = build(repo)
    assert again["skills"]["alpha"]["history"][0]["version"] == "9.9.9"


def test_a_retired_skill_has_a_null_version(repo: Repo) -> None:
    repo.skill("alpha")
    p = repo.skill("gamma")
    p.write_bytes(skill_version.stamp(p.read_bytes()))
    repo.commit("add both")
    subprocess.run(["rm", "-rf", str(repo.base / "skills" / "gamma")], check=True)
    repo.commit("retire gamma")
    repo.publish("main")

    index = build(repo)
    assert index["skills"]["gamma"]["current"] is None
    assert index["skills"]["gamma"]["version"] is None


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


# --- history rows must cite commits the checked revision contains (#290) ----


FABRICATED = "deadbee"


def write_index(repo: Repo) -> None:
    (repo.base / "docs").mkdir(exist_ok=True)
    assert gen_skill_versions.main(["--write"]) == 0


def squash_merge(repo: Repo, branch: str) -> str:
    """Land `branch` on main the way a squash merge does: one new commit
    carrying the branch's tree, none of the branch's commits."""
    repo.git("checkout", "-q", "main")
    repo.git("checkout", branch, "--", ".")
    return repo.commit("squash")


def branch_with_a_new_version(repo: Repo) -> str:
    """main holds v1; `feat` changes the skill and records the index. Returns
    the branch commit that changed the skill."""
    repo.skill("alpha", body="v1")
    repo.commit("v1")
    repo.publish("main")
    repo.git("checkout", "-q", "-b", "feat")
    repo.skill("alpha", body="v2")
    changed = repo.commit("v2")
    repo.publish("feat")
    write_index(repo)
    repo.commit("index")
    repo.publish("feat")
    return changed


def test_check_goes_red_on_a_row_whose_digest_nothing_reachable_carries(
    repo: Repo, capsys: pytest.CaptureFixture[str]
) -> None:
    repo.skill("alpha")
    repo.commit("v1")
    repo.publish("main")
    write_index(repo)
    assert gen_skill_versions.main(["--check"]) == 0

    index = json.loads((repo.base / "docs" / "skill-versions.json").read_text())
    index["skills"]["alpha"]["history"][0]["v"] = "aaaaaaaaaaaa"
    index["skills"]["alpha"]["history"][0]["commit"] = FABRICATED
    (repo.base / "docs" / "skill-versions.json").write_text(json.dumps(index))

    capsys.readouterr()
    assert gen_skill_versions.main(["--check"]) == 1
    out = capsys.readouterr().out
    assert f"commit {FABRICATED} is not a commit in this clone" in out
    assert "::error" in out


def test_an_in_flight_branch_version_gets_no_history_row_before_the_squash(repo: Repo) -> None:
    changed = branch_with_a_new_version(repo)
    index = json.loads((repo.base / "docs" / "skill-versions.json").read_text())
    v2 = skill_version.digest(SKILL.format(name="alpha", body="v2").encode())
    assert v2 not in [h["v"] for h in index["skills"]["alpha"]["history"]]
    assert changed[:7] not in [h["commit"] for h in index["skills"]["alpha"]["history"]]
    # `current` is still read from disk.
    assert index["skills"]["alpha"]["current"] == v2
    assert gen_skill_versions.main(["--check"]) == 0


def inject_stale_row(repo: Repo, commit: str, body: str = "v2") -> str:
    """A row an older generator would have written: real digest, branch commit."""
    path = repo.base / "docs" / "skill-versions.json"
    index = json.loads(path.read_text())
    v = skill_version.digest(SKILL.format(name="alpha", body=body).encode())
    index["skills"]["alpha"]["history"].append(
        {"v": v, "version": None, "commit": commit[:7], "date": "2026-01-01"}
    )
    path.write_text(json.dumps(index))
    return v


def test_a_post_squash_regeneration_adds_the_version_citing_the_squash(repo: Repo) -> None:
    changed = branch_with_a_new_version(repo)
    squashed = squash_merge(repo, "feat")
    repo.publish("main")

    write_index(repo)
    index = json.loads((repo.base / "docs" / "skill-versions.json").read_text())
    v2 = skill_version.digest(SKILL.format(name="alpha", body="v2").encode())
    rows = {h["v"]: h["commit"] for h in index["skills"]["alpha"]["history"]}
    assert rows[v2] == squashed[:7] != changed[:7]
    assert gen_skill_versions.main(["--check"]) == 0


def test_a_stale_pointer_with_a_published_digest_warns_then_is_repaired(
    repo: Repo, capsys: pytest.CaptureFixture[str]
) -> None:
    changed = branch_with_a_new_version(repo)
    squashed = squash_merge(repo, "feat")
    repo.publish("main")
    v2 = inject_stale_row(repo, changed)

    capsys.readouterr()
    assert gen_skill_versions.main(["--check"]) == 0
    out = capsys.readouterr().out
    assert "::warning file=docs/skill-versions.json::alpha" in out
    assert f"commit {changed[:7]} is not an ancestor of HEAD" in out
    assert "gen_skill_versions.py --write" in out
    assert "::error" not in out

    write_index(repo)
    rows = {
        h["v"]: h["commit"]
        for h in json.loads((repo.base / "docs" / "skill-versions.json").read_text())["skills"]["alpha"]["history"]
    }
    assert rows[v2] == squashed[:7]
    capsys.readouterr()
    assert gen_skill_versions.main(["--check"]) == 0
    assert "::warning" not in capsys.readouterr().out


def test_a_fresh_enumeration_prefers_a_reachable_carrier_of_a_version(repo: Repo) -> None:
    """No index to repair: the same blob lives on a branch commit (older, not
    reachable from main) and on the squash commit; the row cites the latter."""
    changed = branch_with_a_new_version(repo)
    squashed = squash_merge(repo, "feat")
    repo.publish("main")
    (repo.base / "docs" / "skill-versions.json").unlink()

    rows = build(repo)["skills"]["alpha"]["history"]
    assert rows[-1]["commit"] == squashed[:7]
    assert changed[:7] not in [h["commit"] for h in rows]


def test_same_second_commits_still_order_by_stamp(
    repo: Repo, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CI regression (#291): on a fast runner the whole fixture lands in one
    second, the timestamp sort ties, and insertion order (rev-list, newest
    first) reversed the history exactly on the tie. The stamp breaks it."""
    monkeypatch.setenv("GIT_COMMITTER_DATE", "2026-11-03T00:00:00Z")
    monkeypatch.setenv("GIT_AUTHOR_DATE", "2026-11-03T00:00:00Z")
    changed = branch_with_a_new_version(repo)
    squashed = squash_merge(repo, "feat")
    repo.publish("main")
    (repo.base / "docs" / "skill-versions.json").unlink()

    rows = build(repo)["skills"]["alpha"]["history"]
    assert rows[-1]["commit"] == squashed[:7]
    assert changed[:7] not in [h["commit"] for h in rows]


def test_a_row_no_reachable_commit_carries_is_pruned_by_write(repo: Repo) -> None:
    changed = branch_with_a_new_version(repo)
    # An intermediate branch version the squash never kept.
    repo.git("checkout", "-q", "feat")
    repo.skill("alpha", body="v3")
    repo.commit("v3")
    repo.publish("feat")
    write_index(repo)
    repo.commit("index 2")
    repo.publish("feat")
    repo.skill("alpha", body="v2")
    repo.commit("back to v2")
    repo.publish("feat")
    squash_merge(repo, "feat")
    repo.publish("main")

    write_index(repo)
    index = json.loads((repo.base / "docs" / "skill-versions.json").read_text())
    v3 = skill_version.digest(SKILL.format(name="alpha", body="v3").encode())
    rows = index["skills"]["alpha"]["history"]
    assert v3 not in [h["v"] for h in rows]
    assert changed[:7] not in [h["commit"] for h in rows]
    assert gen_skill_versions.main(["--check"]) == 0


def test_write_prunes_an_unpublished_row_but_repoints_a_matchable_one(repo: Repo) -> None:
    changed = branch_with_a_new_version(repo)
    squashed = squash_merge(repo, "feat")
    repo.publish("main")
    path = repo.base / "docs" / "skill-versions.json"
    index = json.loads(path.read_text())
    # Unreachable commit AND a digest nothing carries: never published.
    index["skills"]["alpha"]["history"].append(
        {"v": "aaaaaaaaaaaa", "version": None, "commit": FABRICATED, "date": "2026-01-01"}
    )
    path.write_text(json.dumps(index))

    write_index(repo)
    rows = {h["v"]: h["commit"] for h in json.loads(path.read_text())["skills"]["alpha"]["history"]}
    assert "aaaaaaaaaaaa" not in rows
    v2 = skill_version.digest(SKILL.format(name="alpha", body="v2").encode())
    assert rows[v2] == squashed[:7] != changed[:7]
    assert gen_skill_versions.main(["--check"]) == 0


def stamped(body: str, version: str) -> str:
    text = SKILL.format(name="alpha", body=body)
    return text.replace("---\n", f'---\nversion: "{version}"\n', 1)


def test_a_digest_shared_with_a_reachable_commit_is_repointed_never_pruned(repo: Repo) -> None:
    """Two blobs share a digest (they differ only in the `version:` line): the
    earliest sits on a branch commit the squash dropped, the other on the
    squash commit. The published row must follow the reachable one."""
    repo.skill("alpha", body="v1")
    repo.commit("v1")
    repo.publish("main")
    repo.git("checkout", "-q", "-b", "feat")
    (repo.base / "skills" / "alpha" / "SKILL.md").write_text(stamped("B", "1.0.1"))
    c1 = repo.commit("B on the branch")
    repo.publish("feat")
    write_index(repo)
    inject_stale_row(repo, c1, body="B")  # as an older generator wrote it
    repo.commit("index")
    repo.publish("feat")

    repo.git("checkout", "-q", "main")
    repo.git("checkout", "feat", "--", "docs")
    (repo.base / "skills" / "alpha" / "SKILL.md").write_text(stamped("B", "1.0.2"))
    squashed = repo.commit("squash")
    repo.publish("main")

    path = repo.base / "docs" / "skill-versions.json"
    digest = skill_version.digest(stamped("B", "1.0.1").encode())
    assert digest == skill_version.digest(stamped("B", "1.0.2").encode())  # control
    before = {h["v"]: h["commit"] for h in json.loads(path.read_text())["skills"]["alpha"]["history"]}
    assert before[digest] == c1[:7]

    write_index(repo)
    rows = {h["v"]: h["commit"] for h in json.loads(path.read_text())["skills"]["alpha"]["history"]}
    assert rows[digest] == squashed[:7]


def test_a_main_only_digest_is_published_so_it_is_carried(repo: Repo) -> None:
    """Subscribers install from main: a version only origin/main reaches is
    carried, not fabricated, when the checked HEAD is somewhere else."""
    repo.skill("alpha", body="v1")
    repo.commit("v1")
    repo.git("checkout", "-q", "-b", "side")
    repo.git("checkout", "-q", "main")
    repo.skill("alpha", body="hotfix")
    hot = repo.commit("hotfix")
    repo.publish("main")
    row = {
        "v": skill_version.digest(SKILL.format(name="alpha", body="hotfix").encode()),
        "version": None, "commit": hot[:7], "date": "2026-01-01",
    }
    repo.git("checkout", "-q", "side")
    write_index(repo)
    path = repo.base / "docs" / "skill-versions.json"
    index = json.loads(path.read_text())
    index["skills"]["alpha"]["history"].append(row)
    path.write_text(json.dumps(index))
    assert gen_skill_versions.main(["--check"]) == 0


def test_a_dev_only_digest_is_published_so_it_is_admitted(repo: Repo) -> None:
    """dev is a publishing ref too: merged work lives there until promotion,
    so a version only origin/dev reaches is admitted, never skipped as
    in-flight."""
    repo.skill("alpha", body="v1")
    repo.commit("v1")
    repo.publish("main")
    repo.git("checkout", "-q", "-b", "side")
    repo.git("checkout", "-q", "-b", "dev", "main")
    repo.skill("alpha", body="on dev")
    dev_sha = repo.commit("on dev")
    repo.publish("dev")
    repo.git("checkout", "-q", "side")
    write_index(repo)
    index = json.loads((repo.base / "docs" / "skill-versions.json").read_text())
    rows = {r["v"]: r for r in index["skills"]["alpha"]["history"]}
    digest = skill_version.digest(SKILL.format(name="alpha", body="on dev").encode())
    assert digest in rows, "a dev-published version must get a history row"
    assert rows[digest]["commit"] == dev_sha[:7]
    assert gen_skill_versions.main(["--check"]) == 0


def test_check_refuses_a_shallow_clone(
    repo: Repo, tmp_path_factory: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo.skill("alpha")
    repo.commit("v1")
    repo.skill("alpha", body="v2")
    repo.commit("v2")
    repo.publish("main")
    write_index(repo)
    repo.commit("index")

    shallow = tmp_path_factory.mktemp("shallow") / "clone"
    subprocess.run(
        ["git", "clone", "-q", "--depth", "1", f"file://{repo.base}", str(shallow)], check=True
    )
    monkeypatch.chdir(shallow)
    with pytest.raises(SystemExit, match="shallow clone"):
        gen_skill_versions.main(["--check"])
