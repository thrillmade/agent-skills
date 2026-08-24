"""The `version:`/`digest:`/`origin:` rule inside the `validate-skills` gate,
and the index gate.

Two halves, and they fail for different reasons on purpose:

  the stamp   -- pure `sha256`/string comparison over bytes in hand
                 (`skill_version.stamp`). Needs no git history, so it holds
                 at the depth-1 checkout validate-skills.yml uses.
  the index   -- `docs/skill-versions.json`'s `current`/`version` must equal
                 the digest/semver of the file on disk. Also history-free.
                 The index's HISTORY rows are not gated by anything and
                 cannot be at that depth; that is stated in the index itself,
                 not papered over here.

The rule is ENFORCED WHEN PRESENT rather than required -- the same posture
`source` and `kind` already have. `test_a_completely_unstamped_skill_is_not_an_error`
is what says so, and it is the test to delete if protocol#39 ever ratifies
the identity block as REQUIRED. But naming ONE of the three without the other
two IS an error -- `test_naming_one_field_without_the_others_is_rejected`
covers that.
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


def only(errors) -> str:
    errors = list(errors)
    assert len(errors) == 1, f"expected exactly one error, got {errors}"
    return errors[0]


def stamped(tree: SkillTree, name: str = "alpha", extra: str = "") -> Path:
    """A skill carrying its own correct three-field stamp."""
    path = tree.frontmatter(name, extra=extra)
    raw = (path / "SKILL.md").read_bytes()
    (path / "SKILL.md").write_bytes(skill_version.stamp(raw))
    return path / "SKILL.md"


def index_for(tree: SkillTree, *paths: Path, current: dict | None = None, version: dict | None = None) -> Path:
    """Write a `docs/skill-versions.json` that is correct for `paths`, with
    `current`/`version` overriding individual slugs."""
    skills = {}
    for p in paths:
        raw = p.read_bytes()
        skills[p.parent.name] = {
            "current": skill_version.digest(raw),
            "version": skill_version.stamped_version(raw),
            "history": [],
        }
    for slug, value in (current or {}).items():
        skills.setdefault(slug, {"history": []})["current"] = value
    for slug, value in (version or {}).items():
        skills.setdefault(slug, {"history": []})["version"] = value
    d = tree.base / "docs"
    d.mkdir(parents=True, exist_ok=True)
    out = d / "skill-versions.json"
    out.write_text(json.dumps({"version": 1, "skills": skills}), encoding="utf-8")
    return out


# --- enforced when present, and enforced together --------------------------


def test_a_completely_unstamped_skill_is_not_an_error(tree: SkillTree) -> None:
    """`source` is marked REQUIRED by the SPEC table this gate cites and has
    0 of 49 adopters. A second unratified requirement widens that divergence
    instead of closing it, so absence is tolerated and a WRONG stamp is not.
    """
    tree.valid_skill()
    assert tree.validate() == []


def test_a_correctly_stamped_skill_is_clean(tree: SkillTree) -> None:
    stamped(tree)
    assert tree.validate() == []


def test_naming_one_field_without_the_others_is_rejected(tree: SkillTree) -> None:
    """A file that only bothers to claim `origin:` (say) opts the whole
    triple in -- it is not a mix-and-match menu. Reported as `version`
    missing AND `digest` missing, not silently accepted as one-third done.
    """
    tree.frontmatter(extra=f'origin: "{skill_version.ORIGIN}"\n')
    errors = tree.validate()
    assert any("missing `version:`" in e for e in errors)
    assert any("missing `digest:`" in e for e in errors)
    assert not any("missing `origin:`" in e for e in errors)  # origin IS there
    assert len(errors) == 2


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


# --- the digest field is checked against the file's own bytes --------------


def test_a_stale_digest_names_both_values(tree: SkillTree) -> None:
    path = stamped(tree)
    raw = path.read_bytes()
    path.write_bytes(raw + b"one more sentence.\n")
    error = only(e for e in tree.validate() if "`digest`" in e)
    assert error.startswith(ALPHA + "`digest` claims ")
    assert "should read `digest:" in error


def test_a_one_byte_body_edit_is_caught(tree: SkillTree) -> None:
    path = stamped(tree)
    path.write_bytes(path.read_bytes().replace(b"Body.", b"Bodyx"))
    errors = tree.validate()
    assert any("`digest` claims" in e for e in errors)
    assert any("`version` claims" in e for e in errors)  # PATCH is stale too


def test_a_description_edit_is_caught(tree: SkillTree) -> None:
    """The row that rejects a body-only digest: `description` is the trigger
    surface, and a digest that ignores it calls a rewritten one "current".
    """
    path = stamped(tree)
    path.write_bytes(path.read_bytes().replace(
        b"description: What this skill does.",
        b"description: What this skill does!",
    ))
    assert any("`digest` claims" in e for e in tree.validate())


def test_an_added_frontmatter_key_is_caught(tree: SkillTree) -> None:
    path = stamped(tree)
    path.write_bytes(path.read_bytes().replace(b"---\n\n# Title", b"kind: rule\n---\n\n# Title"))
    assert any("`digest` claims" in e for e in tree.validate())


def test_a_whitespace_only_body_edit_is_caught(tree: SkillTree) -> None:
    path = stamped(tree)
    path.write_bytes(path.read_bytes() + b"\n")
    assert any("`digest` claims" in e for e in tree.validate())


# --- malformed shapes, per field --------------------------------------------


@pytest.mark.parametrize(
    "line",
    [
        b"digest: banana",
        b'digest: "abc123"',
        b'digest: "E606DD248A0A"',
        b"digest:",
    ],
)
def test_a_malformed_digest_is_rejected(tree: SkillTree, line: bytes) -> None:
    # A digest this gate cannot trust also makes `version` unverifiable (see
    # skill_version.stamp: an unreadable prior digest forces a PATCH bump),
    # so `version` goes stale in the same stroke -- filtered, not `only()`.
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.digest_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, line))
    error = only(e for e in tree.validate() if "`digest:`" in e or "`digest` claims" in e)
    assert "is not a well-formed `digest:` stamp" in error
    assert "the quotes are REQUIRED" in error


@pytest.mark.parametrize(
    "line",
    [
        b"version: banana",
        b'version: "1.2"',
        b'version: "01.2.3"',
        b"version:",
    ],
)
def test_a_malformed_version_is_rejected(tree: SkillTree, line: bytes) -> None:
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.version_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, line))
    error = only(tree.validate())
    assert "is not a well-formed `version:` stamp" in error


def test_an_unquoted_digest_is_rejected(tree: SkillTree) -> None:
    """Unquoted, an all-digit digest stops being a string. `766941312459` is
    a real historical digest of this catalog's own frontend-a11y, and
    `000000123456` is read as octal -> 42798 and does not round-trip.
    """
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.digest_lines(raw)[0].encode()
    d = skill_version.digest(raw).encode()
    path.write_bytes(raw.replace(good, b"digest: " + d))
    errors = [e for e in tree.validate() if "digest" in e]
    assert "is not a well-formed `digest:` stamp" in only(errors)


def test_a_zero_digest_is_rejected(tree: SkillTree) -> None:
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.digest_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, b'digest: "000000000000"'))
    assert any("`digest` claims" in e for e in tree.validate())


def test_a_wrong_origin_is_rejected(tree: SkillTree) -> None:
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.origin_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, b'origin: "https://example.invalid"'))
    error = only(tree.validate())
    assert error.startswith(ALPHA + "`origin` claims ")
    assert skill_version.ORIGIN in error


def test_an_unquoted_origin_is_rejected(tree: SkillTree) -> None:
    """SPEC 2.1 requires all three identity values be quoted. The pre-2.1
    unquoted shape must fail the STRICT reader, or the MUST is decorative --
    a file would keep validating either way and the rule would rot.
    """
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.origin_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, b"origin: " + skill_version.ORIGIN.encode()))
    assert "is not a well-formed `origin:` stamp" in only(tree.validate())


def test_a_malformed_origin_is_rejected(tree: SkillTree) -> None:
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.origin_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, b"origin:"))
    assert "is not a well-formed `origin:` stamp" in only(tree.validate())


# --- the duplicate-key bypass (C2), for each field --------------------------


def test_two_version_lines_are_rejected(tree: SkillTree) -> None:
    """The bypass this closes: a gate that reads the FIRST `version:` line
    sees the correct claim and exits 0, while `yaml.safe_load` -- last key
    wins, so every agent and every tool -- reads the second one.
    """
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.version_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, good + b'\nversion: "9.9.9"'))

    # the trap, demonstrated on the mutated file before the gate runs
    import yaml
    front = skill_version.FRONTMATTER_RE.match(path.read_bytes()).group(1)
    assert yaml.safe_load(front)["version"] == "9.9.9"
    assert skill_version.SEMVER_RE.search(path.read_bytes()).group(1).decode() != "9.9.9"

    error = only(tree.validate())
    assert "has 2 `version:` lines" in error
    assert "yaml.safe_load" in error


def test_two_digest_lines_are_rejected(tree: SkillTree) -> None:
    # A duplicated digest also reads as an untrustworthy prior claim (same
    # cascade as the malformed cases above), so `version` goes stale too.
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.digest_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, good + b'\ndigest: "deadbeefcafe"'))
    error = only(e for e in tree.validate() if "digest:` lines" in e)
    assert "has 2 `digest:` lines" in error


def test_two_origin_lines_are_rejected(tree: SkillTree) -> None:
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.origin_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, good + b"\norigin: https://example.invalid"))
    error = only(tree.validate())
    assert "has 2 `origin:` lines" in error


def test_a_second_malformed_version_line_is_also_rejected(tree: SkillTree) -> None:
    """One well-formed stamp plus one malformed line leaves the STRICT match
    count at exactly one while YAML still reads the other. The count that has
    to be one is the permissive one.
    """
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.version_lines(raw)[0].encode()
    path.write_bytes(raw.replace(good, good + b"\nversion: banana"))
    assert len(skill_version.SEMVER_RE.findall(path.read_bytes())) == 1
    assert "has 2 `version:` lines" in only(tree.validate())


# --- the line is generated in full ------------------------------------------


def test_the_route_home_may_not_be_dropped_from_digest(tree: SkillTree) -> None:
    """A bare `digest: "<value>"` is a 12-hex string with no instruction
    attached, in a file that may have been copied by hand out of a public
    repo. The comment is the only thing telling whoever holds it where the
    answer lives, so it is part of the generated line, not decoration.
    """
    path = stamped(tree)
    raw = path.read_bytes()
    good = skill_version.digest_lines(raw)[0]
    bare = f'digest: "{skill_version.digest(raw)}"'
    assert bare != good
    path.write_bytes(raw.replace(good.encode(), bare.encode()))
    error = only(tree.validate())
    assert "claims" in error
    assert skill_version.HOME in error


def test_a_nested_version_key_is_left_alone(tree: SkillTree) -> None:
    """`metadata.version` is somebody else's field."""
    path = stamped(tree, extra="metadata:\n  version: 3\n")
    assert tree.validate() == []


# --- the index-currency gate ------------------------------------------------


def test_a_matching_index_is_clean(tree: SkillTree) -> None:
    path = stamped(tree)
    index_for(tree, path)
    assert tree.validate() == []


def test_a_stale_current_index_entry_is_rejected(tree: SkillTree) -> None:
    path = stamped(tree)
    index_for(tree, path, current={"alpha": "deadbeefcafe"})
    error = only(tree.validate())
    assert error.startswith(INDEX + "skills.alpha.current is 'deadbeefcafe'")
    assert "gen_skill_versions.py --write" in error


def test_a_stale_version_index_entry_is_rejected(tree: SkillTree) -> None:
    path = stamped(tree)
    index_for(tree, path, version={"alpha": "9.9.9"})
    error = only(tree.validate())
    assert error.startswith(INDEX + "skills.alpha.version is '9.9.9'")
    assert "gen_skill_versions.py --write" in error


def test_a_never_stamped_skill_is_clean_against_a_null_version_entry(tree: SkillTree) -> None:
    """A file that opts out of the identity block entirely (the tolerated
    posture) has no semver to claim -- `stamped_version` reads None, and the
    index must publish `version: null` to match, not invent a value.
    """
    path = tree.valid_skill()
    d = tree.base / "docs"
    d.mkdir(parents=True, exist_ok=True)
    raw = (path / "SKILL.md").read_bytes()
    (d / "skill-versions.json").write_text(json.dumps({
        "version": 1,
        "skills": {"alpha": {"current": skill_version.digest(raw), "version": None, "history": []}},
    }), encoding="utf-8")
    assert tree.validate() == []


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


# --- the real catalog, through the real CLI ---------------------------------


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
        raw = f.read_bytes()
        assert entry["current"] == skill_version.digest(raw), f.parent.name
        assert entry["version"] == skill_version.stamped_version(raw), f.parent.name


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
