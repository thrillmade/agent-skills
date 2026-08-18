"""The `validate-skills` gate's CLI contract, and its coverage guard.

CI reads three things from this script and nothing else: the
`::error file=<path>::<msg>` annotations, the `::error::<N> skill validation
errors` summary, and the exit code. Those are the contract under test here.

The coverage guard is the other half. `ROOT` is cwd-relative, so a run that
walks the wrong tree reports zero errors exactly as loudly as a run that
walks 48 correct skills -- a pass is only evidence if the count backs it up.
The two `test_main_refuses_*` tests below fail if that guard is ever removed:
delete it and `main()` prints `OK: 0 skills validated cleanly.` and returns 0.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest
import validate_skills

from conftest import REPO_ROOT, SCRIPTS, SkillTree

SCRIPT = SCRIPTS / "validate_skills.py"

# GitHub only renders an annotation in the file view when it is emitted in
# exactly this shape: `::error file=<path>::<message>`, one line, no comma
# before `::`. Pin it -- a stray space or a `,line=` breaks the annotation
# silently and the error becomes log noise nobody sees.
ANNOTATION_RE = re.compile(r"^::error file=[^:\n]+::.+$")
SUMMARY_RE = re.compile(r"^::error::(\d+) skill validation errors$")


# --- Annotation + summary format -------------------------------------------


def test_every_per_skill_error_is_a_well_formed_annotation(tree: SkillTree) -> None:
    tree.skill("alpha", "---\nname: beta\n---\n\nno title\n")
    tree.skill("zeta")
    errors = tree.validate()
    assert errors  # control: the fixture really is broken
    for error in errors:
        assert ANNOTATION_RE.match(error), error


def test_placement_map_errors_are_annotated_against_the_map(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map({"version": 1, "updated": "2026-08-14", "skills": {}})
    for error in tree.validate():
        assert error.startswith("::error file=docs/placement-map.json::"), error


def test_main_prints_every_error_then_a_matching_summary(
    tree: SkillTree, capsys: pytest.CaptureFixture[str]
) -> None:
    tree.skill("alpha", "---\nname: beta\n---\n\nno title\n")
    errors = tree.validate()
    assert len(errors) == 3  # control: pin the fixture's error count

    assert validate_skills.main() == 1
    lines = capsys.readouterr().out.splitlines()

    assert lines[:-1] == errors
    summary = SUMMARY_RE.match(lines[-1])
    assert summary, lines[-1]
    # The summary counts the lines actually printed, not something adjacent.
    assert int(summary.group(1)) == len(lines) - 1


def test_main_reports_success_on_a_clean_tree(
    tree: SkillTree, capsys: pytest.CaptureFixture[str]
) -> None:
    tree.valid_skill("alpha")
    tree.valid_skill("beta")
    # `main()` reads `docs/skill-versions.json` itself now (absence is an
    # error -- see `test_an_absent_index_is_rejected`), and `main()` here is
    # called directly rather than through `tree.validate()`, so it does not
    # get that method's auto-provisioned index. Seed one that matches.
    tree.validate()
    assert validate_skills.main() == 0
    assert capsys.readouterr().out == "OK: 2 skills validated cleanly.\n"


# --- Infra-fatal conditions (exit 1, and deliberately no summary line) ------


def test_missing_skills_dir_exits_1_without_a_summary(
    tree: SkillTree, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        validate_skills.main()
    assert exc.value.code == 1
    assert capsys.readouterr().out == "::error::skills/ directory not found at repo root\n"


def test_empty_skills_dir_exits_1_without_a_summary(
    tree: SkillTree, capsys: pytest.CaptureFixture[str]
) -> None:
    (tree.base / "skills").mkdir()
    with pytest.raises(SystemExit) as exc:
        validate_skills.main()
    assert exc.value.code == 1
    assert capsys.readouterr().out == "::error::no skill subdirectories under skills/\n"


def test_a_file_named_skills_is_not_a_skills_dir(
    tree: SkillTree, capsys: pytest.CaptureFixture[str]
) -> None:
    (tree.base / "skills").write_text("not a directory", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        validate_skills.main()
    assert exc.value.code == 1
    assert capsys.readouterr().out == "::error::skills/ directory not found at repo root\n"


# --- The coverage guard ----------------------------------------------------


def test_coverage_guard_passes_when_the_counts_agree(tree: SkillTree) -> None:
    tree.valid_skill("alpha")
    tree.valid_skill("beta")
    assert validate_skills.coverage_errors(Path("skills"), 2) == []


def test_coverage_guard_rejects_a_zero_count(tree: SkillTree) -> None:
    (tree.base / "skills").mkdir()
    errors = validate_skills.coverage_errors(Path("skills"), 0)
    assert len(errors) == 1
    assert errors[0].startswith("::error::coverage guard: 0 skills validated")


def test_coverage_guard_rejects_a_count_that_disagrees_with_disk(tree: SkillTree) -> None:
    tree.valid_skill("alpha")
    errors = validate_skills.coverage_errors(Path("skills"), 7)
    assert len(errors) == 1
    assert errors[0] == (
        "::error::coverage guard: validated 7 skill dir(s) but 'skills' holds 1 "
        "SKILL.md file(s). The counts must agree or the pass is not evidence "
        "about the skills on disk."
    )


def test_coverage_guard_reports_both_failures_at_once(tree: SkillTree) -> None:
    tree.valid_skill("alpha")
    assert len(validate_skills.coverage_errors(Path("skills"), 0)) == 2


def test_main_refuses_to_pass_when_nothing_was_validated(
    tree: SkillTree, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Delete the coverage guard from `main()` and this test goes red: the run
    prints `OK: 0 skills validated cleanly.` and returns 0 -- green CI over an
    empty tree, which is the failure this whole file exists to prevent.
    """
    (tree.base / "skills").mkdir()
    monkeypatch.setattr(validate_skills, "run", lambda root: [])

    assert validate_skills.main() == 1
    out = capsys.readouterr().out
    assert "OK:" not in out
    assert "coverage guard: 0 skills validated" in out


def test_main_refuses_to_pass_when_the_count_disagrees_with_disk(
    tree: SkillTree, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The other half of the guard: two skill dirs walked, one SKILL.md on
    disk. Remove the guard and this reports success over a half-read tree.
    """
    tree.valid_skill("alpha")
    tree.skill("beta")  # dir, no SKILL.md
    monkeypatch.setattr(validate_skills, "run", lambda root: [])

    assert validate_skills.main() == 1
    out = capsys.readouterr().out
    assert "OK:" not in out
    assert "validated 2 skill dir(s) but 'skills' holds 1 SKILL.md file(s)" in out


# --- End to end, exactly as the workflow invokes it ------------------------


def run_entrypoint(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=cwd, capture_output=True, text=True
    )


def test_entrypoint_validates_the_real_catalog_from_the_repo_root() -> None:
    on_disk = len(list((REPO_ROOT / "skills").glob("*/SKILL.md")))
    assert on_disk > 0  # control: the glob really finds the catalog

    result = run_entrypoint(REPO_ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout == f"OK: {on_disk} skills validated cleanly.\n"


def test_entrypoint_never_reports_success_from_the_wrong_directory(tmp_path: Path) -> None:
    result = run_entrypoint(tmp_path)
    assert result.returncode == 1
    assert "OK:" not in result.stdout


# --- The catalog itself ----------------------------------------------------


def test_the_real_catalog_passes_every_rule() -> None:
    """The gate run against this repo's own skills/, in-process. Fails when a
    SKILL.md lands broken -- test.yml has no `paths:` filter, so this catches
    it even on a PR that validate-skills.yml's filter would skip.
    """
    assert validate_skills.run(REPO_ROOT / "skills") == []


def test_the_real_catalog_has_a_skill_md_in_every_directory() -> None:
    skills = REPO_ROOT / "skills"
    dirs = validate_skills._skill_dirs(skills)
    assert dirs  # control: the catalog is not empty
    assert validate_skills.coverage_errors(skills, len(dirs)) == []
