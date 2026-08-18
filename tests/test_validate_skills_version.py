"""The `version:` rule inside the `validate-skills` gate, and the index gate.

Two halves, and they fail for different reasons on purpose:

  the stamp   -- pure `sha256` over bytes in hand. Needs no git history, so
                 it holds at the depth-1 checkout validate-skills.yml uses.
  the index   -- `docs/skill-versions.json`'s `current` must equal the digest
                 of the file on disk. Also history-free. The index's HISTORY
                 rows are not gated by anything and cannot be at that depth;
                 that is stated in the index itself, not papered over here.

The rule is ENFORCED WHEN PRESENT rather than required -- the same posture
`source` and `kind` already have. `test_an_unstamped_skill_is_not_an_error`
is what says so, and it is the test to delete if protocol#39 ever ratifies
`version:` as REQUIRED.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import skill_version
import stamp_versions
import validate_skills

from conftest import SCRIPTS, SkillTree

ALPHA = "::error file=skills/alpha/SKILL.md::"
INDEX = "::error file=docs/skill-versions.json::"


def only(errors: list[str]) -> str:
    assert len(errors) == 1, f"expected exactly one error, got {errors}"
    return errors[0]


def stamped(tree: SkillTree, name: str = "alpha", extra: str = "") -> Path:
    """A skill carrying its own correct stamp."""
    path = tree.frontmatter(name, extra=extra)
    raw = (path / "SKILL.md").read_bytes()
    (path / "SKILL.md").write_bytes(skill_version.stamp(raw))
    return path / "SKILL.md"


def index_for(tree: SkillTree, *paths: Path, current: dict | None = None) -> Path:
    """Write a `docs/skill-versions.json` that is correct for `paths`, with
    `current` overriding individual slugs."""
    skills = {}
    for p in paths:
        skills[p.parent.name] = {
            "current": skill_version.digest(p.read_bytes()),
            "history": [],
        }
    for slug, value in (current or {}).items():
        skills.setdefault(slug, {"history": []})["current"] = value
    d = tree.base / "docs"
    d.mkdir(parents=True, exist_ok=True)
    out = d / "skill-versions.json"
    out.write_text(json.dumps({"version": 1, "skills": skills}), encoding="utf-8")
    return out


# --- enforced when present -------------------------------------------------


def test_an_unstamped_skill_is_not_an_error(tree: SkillTree) -> None:
    """`source` is marked REQUIRED by the SPEC table this gate cites and has
    0 of 49 adopters. A second unratified requirement widens that divergence
    instead of closing it, so absence is tolerated and a WRONG stamp is not.
    """
    tree.valid_skill()
    assert tree.validate() == []


def test_a_correctly_stamped_skill_is_clean(tree: SkillTree) -> None:
    stamped(tree)
    assert tree.validate() == []


# --- the gate reads the same bytes `stamp_versions` and `skill_version` do -
#
# `read_text()` universal-newline-decodes BOTH `\r\n` and a lone `\r` to
# `\n`; `skill_version._lf()` only elides `\r\n` pairs. A gate built on the
# text path can therefore call a file clean that the digest rule (and
# `stamp_versions --write`) disagrees with, and the remedy it prints is then
# a no-op.


def test_a_cr_only_file_fails_missing_frontmatter(tree: SkillTree) -> None:
    """No `\\n` anywhere -- the frontmatter fences aren't `---\\n` any more,
    so there is nothing here `FRONTMATTER_RE` can match. This has to be an
    error, not a silently-skipped file.
    """
    path = tree.valid_skill()
    assert tree.validate() == []  # control: clean before the corruption
    raw = (path / "SKILL.md").read_bytes()
    cr_only = raw.replace(b"\n", b"\r")
    assert b"\n" not in cr_only and b"\r" in cr_only  # control: genuinely CR-only
    (path / "SKILL.md").write_bytes(cr_only)
    assert "missing YAML frontmatter" in only(tree.validate())


def test_a_lone_cr_in_the_body_is_tolerated(tree: SkillTree) -> None:
    """A lone CR that never pairs with an LF, sitting in the BODY where it
    doesn't touch the frontmatter fences, must not stop the frontmatter from
    matching -- and the digest this gate checks against must be the same one
    `stamp_versions.py` computes for the same bytes.
    """
    path = tree.frontmatter(body="\n# Title\n\nBody one.\rBody two.\n")
    raw = (path / "SKILL.md").read_bytes()
    assert b"\r" in raw and b"\r\n" not in raw  # control: a lone CR, not a pair
    stamped_raw = skill_version.stamp(raw)
    (path / "SKILL.md").write_bytes(stamped_raw)
    assert tree.validate() == []
    assert stamp_versions.restamp(stamped_raw) == stamped_raw  # agrees with --check


# --- the stamp is checked against the file's own bytes ---------------------


def test_a_stale_stamp_names_both_values(tree: SkillTree) -> None:
    path = stamped(tree)
    raw = path.read_bytes()
    path.write_bytes(raw + b"one more sentence.\n")
    expected = skill_version.digest(path.read_bytes())
    error = only(tree.validate())
    assert error.startswith(ALPHA + "`version` claims ")
    assert f"content digest is {expected}" in error
    assert "stamp_versions.py --write" in error


def test_a_one_byte_body_edit_is_caught(tree: SkillTree) -> None:
    path = stamped(tree)
    path.write_bytes(path.read_bytes().replace(b"Body.", b"Bodyx"))
    assert "is stale" in only(tree.validate())


def test_a_description_edit_is_caught(tree: SkillTree) -> None:
    """The row that rejects a body-only digest: `description` is the trigger
    surface, and a digest that ignores it calls a rewritten one "current".
    """
    path = stamped(tree)
    path.write_bytes(path.read_bytes().replace(
        b"description: What this skill does.",
        b"description: What this skill does!",
    ))
    assert "is stale" in only(tree.validate())


def test_an_added_frontmatter_key_is_caught(tree: SkillTree) -> None:
    path = stamped(tree)
    path.write_bytes(path.read_bytes().replace(b"---\n\n# Title", b"kind: rule\n---\n\n# Title"))
    assert "is stale" in only(tree.validate())


def test_a_whitespace_only_body_edit_is_caught(tree: SkillTree) -> None:
    path = stamped(tree)
    path.write_bytes(path.read_bytes() + b"\n")
    assert "is stale" in only(tree.validate())


# --- malformed shapes all name the SAME expected value ---------------------


@pytest.mark.parametrize(
    "line",
    [
        b"version: banana",
        b'version: "abc123"',
        b'version: "E606DD248A0A"',
        b"version:",
    ],
)
def test_a_malformed_stamp_is_rejected(tree: SkillTree, line: bytes) -> None:
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.version_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, line))
    error = only(tree.validate())
    assert "is not a well-formed stamp" in error
    assert "the quotes are REQUIRED" in error


def test_an_unquoted_digest_is_rejected(tree: SkillTree) -> None:
    """Unquoted, an all-digit digest stops being a string. `766941312459` is
    a real historical digest of this catalog's own frontend-a11y, and
    `000000123456` is read as octal -> 42798 and does not round-trip.
    """
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.version_lines(raw)[0].encode()
    d = skill_version.digest(raw).encode()
    path.write_bytes(raw.replace(good, b"version: " + d))
    assert "is not a well-formed stamp" in only(tree.validate())


def test_a_zero_digest_is_rejected(tree: SkillTree) -> None:
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.version_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, b'version: "000000000000"'))
    assert "is stale" in only(tree.validate())


# --- the duplicate-key bypass (C2) -----------------------------------------


def test_two_version_lines_are_rejected(tree: SkillTree) -> None:
    """The bypass this closes: a gate that reads the FIRST `version:` line
    sees the correct digest and exits 0, while `yaml.safe_load` -- last key
    wins, so every agent and every tool -- reads the second one.
    """
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.version_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, good + b'\nversion: "deadbeefcafe"'))

    # the trap, demonstrated on the mutated file before the gate runs
    import yaml
    front = skill_version.FRONTMATTER_RE.match(path.read_bytes()).group(1)
    assert yaml.safe_load(front)["version"] == "deadbeefcafe"
    assert skill_version.STAMP_RE.search(path.read_bytes()).group(1).decode() != "deadbeefcafe"

    error = only(tree.validate())
    assert "has 2 `version:` lines" in error
    assert "yaml.safe_load" in error


def test_a_second_malformed_version_line_is_also_rejected(tree: SkillTree) -> None:
    """One well-formed stamp plus one malformed line leaves the STRICT match
    count at exactly one while YAML still reads the other. The count that has
    to be one is the permissive one.
    """
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.version_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, good + b"\nversion: banana"))
    assert len(skill_version.STAMP_RE.findall(path.read_bytes())) == 1
    assert "has 2 `version:` lines" in only(tree.validate())


# --- the line is generated in full ----------------------------------------


def test_the_route_home_may_not_be_dropped(tree: SkillTree) -> None:
    """A bare `version: "<digest>"` is a 12-hex string with no instruction
    attached, in a file that may have been copied by hand out of a public
    repo. The comment is the only thing telling whoever holds it where the
    answer lives, so it is part of the generated line, not decoration.
    """
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.version_lines(raw)[0]
    bare = f'version: "{skill_version.digest(raw)}"'
    assert bare != good
    path.write_bytes(raw.replace(good.encode(), bare.encode()))
    error = only(tree.validate())
    assert "generated in full" in error
    assert skill_version.HOME in error


def test_a_nested_version_key_is_left_alone(tree: SkillTree) -> None:
    """`metadata.version` is somebody else's field."""
    path = stamped(tree, extra="metadata:\n  version: 3\n")
    assert tree.validate() == []


# --- the index-currency gate ----------------------------------------------


def test_a_matching_index_is_clean(tree: SkillTree) -> None:
    path = stamped(tree)
    index_for(tree, path)
    assert tree.validate() == []


def test_a_stale_index_entry_is_rejected(tree: SkillTree) -> None:
    path = stamped(tree)
    index_for(tree, path, current={"alpha": "deadbeefcafe"})
    error = only(tree.validate())
    assert error.startswith(INDEX + "skills.alpha.current is 'deadbeefcafe'")
    assert "gen_skill_versions.py --write" in error


def test_a_skill_missing_from_the_index_is_rejected(tree: SkillTree) -> None:
    path = stamped(tree)
    tree.valid_skill("beta")
    index_for(tree, path)
    error = only(tree.validate())
    assert error.startswith(INDEX + "skills.beta is missing")


def test_an_absent_index_is_rejected(tree: SkillTree) -> None:
    """NOT the placement map's posture. The placement map may be authored by
    a parallel agent and legitimately not exist yet; this index is generated
    by this catalog's own tooling and checked in, so its absence is every
    `skills.<slug>` entry missing at once -- deleting it must not silently
    disarm the gate that exists to catch exactly that.

    `validate_skills.run()` directly, not `tree.validate()` -- the latter
    auto-provisions a matching index for tests that don't care about this
    gate (see its docstring), which would defeat the one test that does.
    """
    stamped(tree)
    assert not (tree.base / "docs" / "skill-versions.json").exists()
    error = only(validate_skills.run(Path("skills")))
    assert error.startswith(INDEX + "could not read")


def test_a_malformed_index_is_rejected(tree: SkillTree) -> None:
    stamped(tree)
    d = tree.base / "docs"
    d.mkdir(parents=True, exist_ok=True)
    (d / "skill-versions.json").write_text("{not json", encoding="utf-8")
    assert "could not read" in only(tree.validate())


def test_an_index_with_no_skills_object_is_rejected(tree: SkillTree) -> None:
    stamped(tree)
    d = tree.base / "docs"
    d.mkdir(parents=True, exist_ok=True)
    (d / "skill-versions.json").write_text('{"version": 1}', encoding="utf-8")
    assert "`skills` must be an object" in only(tree.validate())


# --- the real catalog, through the real CLI --------------------------------


def test_the_shipped_catalog_passes_the_real_gate() -> None:
    """No pipe: the exit code is read from the process, not from a `tail`."""
    repo = SCRIPTS.parents[1]
    p = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_skills.py")],
        cwd=repo, capture_output=True, text=True,
    )
    assert p.returncode == 0, p.stdout + p.stderr
    assert p.stdout.strip().endswith("skills validated cleanly.")


def test_the_shipped_index_is_current_for_every_skill() -> None:
    repo = SCRIPTS.parents[1]
    index = json.loads((repo / "docs" / "skill-versions.json").read_text())
    files = sorted((repo / "skills").glob("*/SKILL.md"))
    assert len(files) >= 40  # control for the zero below
    for f in files:
        entry = index["skills"][f.parent.name]
        assert entry["current"] == skill_version.digest(f.read_bytes()), f.parent.name


def test_the_shipped_index_never_invents_an_authoring_home() -> None:
    """`docs/placement-map.json` owns that fact; the index copies it. A slug
    the map does not carry gets no value rather than a plausible one -- the
    defect that put a fabricated `authoring_home` on a skill that never
    shipped.
    """
    repo = SCRIPTS.parents[1]
    index = json.loads((repo / "docs" / "skill-versions.json").read_text())
    placement = json.loads((repo / "docs" / "placement-map.json").read_text())["skills"]
    assert placement  # control
    for slug, entry in index["skills"].items():
        if "authoring_home" in entry:
            assert entry["authoring_home"] == placement[slug]["authoring_home"], slug


def test_the_index_states_which_half_of_it_is_gated() -> None:
    """The history rows cannot be checked at fetch-depth 1 and nothing checks
    them. Saying so in the artifact is the difference between a known
    limitation and a silent one.
    """
    repo = SCRIPTS.parents[1]
    index = json.loads((repo / "docs" / "skill-versions.json").read_text())
    assert index["verification"]["current"].startswith("GATED.")
    assert index["verification"]["history"].startswith("NOT GATED.")
    assert index["verification"]["history_rows_ungated"] > 0
