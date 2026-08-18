"""Characterization + regression tests for the markdown link gate (#234).

`check-links` (the logmind-installed workflow) never reads `skills/` -- the
catalog IS `skills/`, so a required merge gate was reporting green over the
one directory it exists to protect. This pins the REPLACEMENT gate, built
directly into `validate_skills.py` rather than routed through
`check-doc-links.yml` (see that decision recorded in AGENTS.md / the #234
issue body: the Go linkchecker's roots are hardcoded and its self-heal job
can push commits that delete the very link line the gate exists to
protect).

Layout mirrors `test_validate_skills.py`: `tree` fixture, `only()` helper.
"""

from __future__ import annotations

import validate_skills
from conftest import SkillTree

ALPHA = "::error file=skills/alpha/SKILL.md::"


def only(errors: list[str]) -> str:
    assert len(errors) == 1, f"expected exactly one error, got {errors}"
    return errors[0]


# --- broken relative links are caught ---------------------------------------


def test_broken_relative_link_in_a_skill_body_is_caught(tree: SkillTree) -> None:
    # This is the control from the issue body itself: a relative link to a
    # skill directory that does not exist, inside a skill BODY (not a doc).
    # The old `check-links` gate reported this clean because it never reads
    # skills/ at all.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "[deliberately broken](../zzz-not-a-real-skill/SKILL.md)\n",
    )
    errors = tree.validate()
    broken = [e for e in errors if "broken relative link" in e]
    assert len(broken) == 1, errors
    assert broken[0].startswith(ALPHA)
    assert "../zzz-not-a-real-skill/SKILL.md" in broken[0]


def test_broken_relative_link_into_references_subdir_is_caught(tree: SkillTree) -> None:
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "[missing ref](references/nope.md)\n",
    )
    errors = tree.validate()
    broken = [e for e in errors if "broken relative link" in e]
    assert len(broken) == 1, errors
    assert "references/nope.md" in broken[0]


def test_valid_relative_link_into_references_subdir_is_clean(tree: SkillTree) -> None:
    d = tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "[ref](references/present.md)\n",
    )
    (d / "references").mkdir()
    (d / "references" / "present.md").write_text("stuff\n", encoding="utf-8")
    errors = tree.validate()
    assert [e for e in errors if "broken relative link" in e] == []


def test_valid_sibling_skill_link_is_clean(tree: SkillTree) -> None:
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "[sibling](../beta/SKILL.md)\n",
    )
    tree.valid_skill("beta")
    errors = tree.validate()
    assert [e for e in errors if "broken relative link" in e] == []


# --- false-positive guards: fenced code, inline code, same-page anchors ----


def test_link_syntax_inside_a_fenced_code_block_is_not_checked(tree: SkillTree) -> None:
    # A fenced code block SHOWING markdown link syntax as an example must
    # not be resolved as a real link -- firing here would redden every PR
    # that documents the syntax itself, which is worse than the gap #234
    # names for absolute URLs.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "```markdown\n[fake](../not-real/SKILL.md)\n```\n",
    )
    errors = tree.validate()
    assert [e for e in errors if "broken relative link" in e] == []


def test_link_syntax_inside_inline_code_is_not_checked(tree: SkillTree) -> None:
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "Write it as `[fake](../not-real/SKILL.md)` in the body.\n",
    )
    errors = tree.validate()
    assert [e for e in errors if "broken relative link" in e] == []


def test_same_page_anchor_link_is_not_checked(tree: SkillTree) -> None:
    # `[jump](#section)` has no path component to resolve -- it is not a
    # broken link, it is a same-page anchor, and flagging it would be a
    # false positive on every skill with a table of contents.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "[jump](#section)\n\n## Section\n",
    )
    errors = tree.validate()
    assert [e for e in errors if "broken relative link" in e] == []


def test_absolute_http_link_is_never_flagged_broken(tree: SkillTree) -> None:
    # #234's decision: absolute http(s) links are counted, never fetched.
    # A reference file's absolute GitHub URL 404s until its own PR merges
    # (the PR #233 case in the issue) -- a checker that fetches would block
    # its own PR. So even a URL that plainly does not resolve must not be
    # reported as an error by THIS gate.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "[ext](https://example.invalid/definitely-not-a-real-path-xyz)\n",
    )
    errors = tree.validate()
    assert [e for e in errors if "broken relative link" in e] == []


# --- the gate states its own scope ------------------------------------------


def test_link_stats_counts_relative_and_absolute_separately() -> None:
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "skills"
        d = root / "alpha"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(
            "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
            "[sibling](../beta/SKILL.md)\n"
            "[ext](https://example.invalid/x)\n"
            "[anchor](#section)\n",
            encoding="utf-8",
        )
        (root / "beta").mkdir()
        (root / "beta" / "SKILL.md").write_text("placeholder\n", encoding="utf-8")

        relative, absolute = validate_skills.link_stats(root)
        assert relative == 1
        assert absolute == 1


def test_main_prints_a_scope_line_naming_what_it_checked(tmp_path, monkeypatch) -> None:
    """The issue requires the gate SAY which bound it checked, so a reader
    of green CI output knows relative links were verified and absolute
    ones were not -- not left to infer it from silence.
    """
    import subprocess
    import sys

    from conftest import REPO_ROOT, SCRIPTS

    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "validate_skills.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    combined = result.stdout + result.stderr
    assert "relative" in combined and "absolute" in combined, combined
    assert "http" in combined, combined
