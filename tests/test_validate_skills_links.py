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


# --- false-positive guard: CommonMark's OTHER code-block spelling ----------
#
# #247 panel finding 1: `FENCE_RE` only ever recognised ``` / ~~~. A worked
# example written as a 4-space-INDENTED block (no fence) was never blanked,
# so link-shaped text inside one resolved as a real link and reddened a PR
# that merely documented the syntax -- on a REQUIRED gate, so this false
# positive blocks every PR in the repo until it is reverted.


def test_link_syntax_inside_an_indented_code_block_is_not_checked(tree: SkillTree) -> None:
    # The panel's own reproduction, verbatim: an isolated 4-space block
    # (blank line above it, so CommonMark reads it as code and not as a
    # paragraph's lazy continuation) containing a link-shaped example.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "    Indented code block (4-space) containing a link-shaped example:\n"
        "    [indented fake](totally-not-real.md)\n",
    )
    errors = tree.validate()
    assert [e for e in errors if "broken relative link" in e] == []


def test_a_genuinely_broken_link_inside_an_indented_code_block_stays_hidden(
    tree: SkillTree,
) -> None:
    # The mirror of the case above: a link-shaped EXAMPLE inside a real
    # indented block is source material and must not be checked AT ALL,
    # broken target or not -- the same posture the fenced-block guard
    # already has, so an author cannot "fix" this false positive by
    # switching spellings and getting a different false positive instead.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "Example:\n\n"
        "    [x](../this-does-not-exist/SKILL.md)\n",
    )
    errors = tree.validate()
    assert [e for e in errors if "broken relative link" in e] == []


def test_a_broken_link_right_after_an_indented_code_block_is_still_caught(
    tree: SkillTree,
) -> None:
    # The block ends and ordinary prose resumes -- a real link there must
    # still be checked, so the indented-block guard is scoped to the block
    # itself and not to everything after it.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "    indented example line one\n"
        "    indented example line two\n\n"
        "[deliberately broken](../zzz-not-a-real-skill/SKILL.md)\n",
    )
    errors = tree.validate()
    broken = [e for e in errors if "broken relative link" in e]
    assert len(broken) == 1, errors
    assert "line 11" in broken[0], broken[0]


def test_list_item_continuation_at_its_own_content_column_is_not_mistaken_for_code(
    tree: SkillTree,
) -> None:
    # The subtlety a naive `^    ` rule gets wrong, and the wrong direction
    # is the worse one: ordinary list-item prose that happens to be
    # indented four spaces because it sits under a four-character marker
    # ("10. ") is NOT a code block -- CommonMark measures the four spaces
    # FROM the item's own content column, not from the left margin.
    # Blanking it anyway would hide a REAL broken link from this gate
    # rather than merely mis-scoping a worked example, which is the
    # trade #247's panel named as worse than the false positive this fix
    # exists to close.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "10. Item text with a link inside it later:\n"
        "    [broken](../not-a-real-skill/SKILL.md)\n",
    )
    errors = tree.validate()
    broken = [e for e in errors if "broken relative link" in e]
    assert len(broken) == 1, errors


def test_a_shallow_lazy_continuation_does_not_evict_the_list_column_for_a_link_below(
    tree: SkillTree,
) -> None:
    # The sharper form of the same subtlety, and the one an implementation
    # that pops a list's content column on ANY shallower line -- rather
    # than only on one that is NOT a lazy paragraph continuation -- gets
    # wrong. CommonMark: `1. Item one starts a paragraph` opens a list item
    # at content column 3; `lazily continued at column zero`, though
    # indented 0, is a LAZY CONTINUATION of that SAME paragraph and does
    # NOT close the item. After the blank line, four spaces is only ONE
    # past that item's own column (3+4=7 would be needed for code) -- so
    # the block below is the item's own SECOND paragraph, not code, and
    # the link inside it must still be checked. An implementation that
    # evicts the column on the shallow line ends up with an EMPTY list
    # stack by the time it reaches the indented text, reads a bare
    # four-space threshold, and wrongly blanks a real link out of the scan
    # -- hiding a genuinely broken link from this gate instead of merely
    # mis-scoping an example, exactly the trade the panel named as worse.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "1. Item one starts a paragraph\n"
        "lazily continued at column zero\n\n"
        "    [broken](../not-a-real-skill/SKILL.md) more text\n",
    )
    errors = tree.validate()
    broken = [e for e in errors if "broken relative link" in e]
    assert len(broken) == 1, errors


def test_an_ordered_marker_not_starting_at_one_does_not_evict_the_next_indented_block(
    tree: SkillTree,
) -> None:
    # A related carve-out to the one above, in the OTHER direction: an
    # ordered-list marker that does not start at "1" (`2)` here) cannot
    # itself INTERRUPT an open paragraph (CommonMark) -- it is read as
    # literal continuation text, not as a genuine new list item. Reading
    # it as a real marker anyway leaves a phantom list column on the
    # stack, which raises the threshold for a LATER, unrelated indented
    # block enough that it stops looking like code -- letting a
    # link-shaped EXAMPLE inside it leak through as a real link and
    # reintroducing the false positive #247 exists to close, on a
    # narrower trigger.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "text text\n"
        "2) brown quick fox\n\n"
        "    [fake](not-real.md)\n",
    )
    errors = tree.validate()
    assert [e for e in errors if "broken relative link" in e] == []


def test_a_shallow_setext_underline_does_not_convert_and_stays_list_prose(
    tree: SkillTree,
) -> None:
    # A setext underline is the opposite carve-out from the ATX/thematic
    # one above: CommonMark says it can NEVER interrupt a paragraph at
    # all, so one written shallower than the enclosing list item's own
    # content column does not convert that paragraph into a heading --
    # it stays literal continuation text of the SAME paragraph.
    # Converting it anyway closes the paragraph early, and a later line
    # deep enough to clear the list's own threshold (but written with NO
    # blank line before it, so nothing else resets the paragraph state)
    # then reads as fresh indented code instead of that same paragraph's
    # continuation -- wrongly hiding a real link inside it.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "1. the quick fox\n"
        "brown the\n"
        "===\n"
        "       [broken](../not-a-real-skill/SKILL.md)\n",
    )
    errors = tree.validate()
    broken = [e for e in errors if "broken relative link" in e]
    assert len(broken) == 1, errors


def test_a_shallow_heading_exits_the_list_so_the_block_under_it_is_real_code(
    tree: SkillTree,
) -> None:
    # The direction opposite the two carve-outs above: a heading (unlike a
    # lazy paragraph continuation) CAN interrupt an open paragraph even
    # when shallow, so it closes both the paragraph AND the list it fails
    # to indent into -- the four spaces under it, with no blank line
    # needed, are a genuine top-level indented code block, and a
    # link-shaped example inside it must NOT be checked. Treating the
    # heading as just more lazy list text instead (the naive reading) keeps
    # a phantom list column alive, raises the threshold the line under it
    # has to clear, and reports the fake example as a broken real link.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "1. the quick fox\n"
        "brown the\n"
        "# Heading\n"
        "    [fake](not-real.md)\n",
    )
    errors = tree.validate()
    assert [e for e in errors if "broken relative link" in e] == []


def test_line_number_is_correct_after_a_long_fenced_code_block(tree: SkillTree) -> None:
    # Blanking has to preserve LINE COUNT exactly, whichever code spelling
    # is blanked -- deletion would shift every line number after it, and a
    # wrong line number in the annotation sends a reviewer to the wrong
    # place in the diff.
    filler = "\n".join(f"line {i} of the fenced example" for i in range(20))
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        f"```text\n{filler}\n```\n\n"
        "[deliberately broken](../zzz-not-a-real-skill/SKILL.md)\n",
    )
    errors = tree.validate()
    broken = [e for e in errors if "broken relative link" in e]
    assert len(broken) == 1, errors
    assert "line 31" in broken[0], broken[0]


def test_line_number_is_correct_after_a_long_indented_code_block(tree: SkillTree) -> None:
    filler = "\n".join(f"    line {i} of the indented example" for i in range(20))
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        f"{filler}\n\n"
        "[deliberately broken](../zzz-not-a-real-skill/SKILL.md)\n",
    )
    errors = tree.validate()
    broken = [e for e in errors if "broken relative link" in e]
    assert len(broken) == 1, errors
    assert "line 29" in broken[0], broken[0]


# --- false-positive guard: percent-encoded paths ----------------------------
#
# #247 panel finding 2: `[x](with%20space.txt)` pointing at a real
# `with space.txt` was reported broken -- no `%xx` decoding happened before
# `Path.is_file()`. Latent in this catalog today (0 hits, control-tested
# against a synthetic case that DOES hit, below and via the probe run over
# skills/ itself) but real the first time an author names a file with a
# space, a `#`, or any other character markdown requires escaped in a link.


def test_percent_encoded_path_to_a_real_file_is_clean(tree: SkillTree) -> None:
    d = tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "[x](with%20space.txt)\n",
    )
    (d / "with space.txt").write_text("stuff\n", encoding="utf-8")
    errors = tree.validate()
    assert [e for e in errors if "broken relative link" in e] == []


def test_percent_encoded_path_to_a_missing_file_is_still_caught(tree: SkillTree) -> None:
    # Decoding must not turn INTO a new false negative: a %-encoded path to
    # something that genuinely is not there still has to be flagged.
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "[x](with%20space%20missing.txt)\n",
    )
    errors = tree.validate()
    broken = [e for e in errors if "broken relative link" in e]
    assert len(broken) == 1, errors
    assert "with space missing.txt" in broken[0], broken[0]


# --- an unreadable file annotates instead of crashing the whole run --------
#
# #247 panel finding 3: `_iter_links` called `.read_text(encoding="utf-8")`
# unguarded on every `.md` under skills/, including references/. A
# non-UTF-8 file or a dangling symlink ending `.md` crashed the whole
# script with an unhandled traceback -- exit non-zero (no false green), but
# it discarded every OTHER annotation the per-skill loop had already
# collected and printed a traceback instead of this gate's normal
# `::error file=` form.


def test_an_unreadable_file_gets_a_proper_annotation_not_a_crash(tree: SkillTree) -> None:
    d = tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\nok\n",
    )
    (d / "references").mkdir()
    (d / "references" / "bad.md").write_bytes(b"\xff\xfe not utf-8 \x80\x81")
    errors = tree.validate()
    unreadable = [e for e in errors if "could not read" in e]
    assert len(unreadable) == 1, errors
    assert "bad.md" in unreadable[0], unreadable[0]


def test_an_unreadable_file_does_not_hide_a_real_broken_link_elsewhere(
    tree: SkillTree,
) -> None:
    # The point of annotating rather than raising: the rest of the run
    # still reports. A crash here used to discard this OTHER finding too.
    d = tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "[deliberately broken](../zzz-not-a-real-skill/SKILL.md)\n",
    )
    (d / "references").mkdir()
    (d / "references" / "bad.md").write_bytes(b"\xff\xfe not utf-8 \x80\x81")
    errors = tree.validate()
    broken = [e for e in errors if "broken relative link" in e]
    unreadable = [e for e in errors if "could not read" in e]
    assert len(broken) == 1, errors
    assert len(unreadable) == 1, errors


# --- a link resolving to a directory is not a valid target ------------------
#
# #247 panel finding 4: `Path.exists()` is true for directories, so
# `[x](references)` passed even though nothing at that path is a document a
# reader can open.


def test_a_link_resolving_to_a_directory_is_flagged_broken(tree: SkillTree) -> None:
    d = tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: d\n---\n\n# Title\n\n"
        "[dirlink](references)\n",
    )
    (d / "references").mkdir()
    errors = tree.validate()
    broken = [e for e in errors if "broken relative link" in e]
    assert len(broken) == 1, errors
    assert "directory" in broken[0], broken[0]


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
