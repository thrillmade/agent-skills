"""Prove `test_check_prose_retention.py` can fail.

A check that has never failed on demand is not proven. This file breaks the
detector on purpose, one way per entry in MUTATIONS below, and asserts the suite
goes red each time -- committed, so the proof re-runs on every PR rather than
living in somebody's recollection of a terminal session.

How it works: copy the real detector into a scratch tree, apply one textual
mutation, copy the real suite in beside it, and run pytest there in a
subprocess. Red means the suite noticed. Every mutation also asserts it
*landed* -- a find-and-replace that silently matched nothing would otherwise
"prove" the suite works by testing an unmodified file, which is the same
mistake as a control-free grep.

`test_control_the_unmutated_detector_is_green` is the other half. Without it,
"the suite went red" could just mean the scratch harness is broken and would
report red for any input at all. Two ways of breaking THIS file -- a scratch
conftest that does not expose the mutated module, and fixtures that fail to
copy -- make every mutation test pass vacuously, and the control is the only
thing that catches either.

Every mutation carries the consequence it reintroduces. A mutation nobody can
name the defect for is not worth committing, and a mutation caught only by some
unrelated test proves less than it looks: each of these dies on the test that is
about its behaviour.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DETECTOR = REPO_ROOT / ".github" / "scripts" / "check_prose_retention.py"
SUITE = Path(__file__).parent / "test_check_prose_retention.py"
FIXTURES = Path(__file__).parent / "fixtures" / "prose-retention"
LEDGER = REPO_ROOT / "docs" / "prose-removals.md"

# Each entry: a name, the exact source text to replace, and what to replace it
# with.
MUTATIONS = [
    # -- the thresholds -----------------------------------------------------
    (
        # The gate stops firing on prose at all. Every historical case walks
        # through, because all three cut prose.
        "prose_floor_disabled",
        '    "prose": 2,',
        '    "prose": 999,',
    ),
    (
        # Off by one. The boundary pair either side of the measured prose noise
        # floor is what should catch this, not the large historical cases.
        "prose_floor_off_by_one",
        '    "prose": 2,',
        '    "prose": 3,',
    ),
    (
        # Gutting a `description:` stops being content loss, so a skill can be
        # made undiscoverable without a word of explanation.
        "frontmatter_floor_disabled",
        '    "frontmatter": 3,',
        '    "frontmatter": 999,',
    ),
    (
        # Worked examples stop being content, which reopens the byte arbitrage:
        # delete a code block, add filler prose, keep the gate green.
        "code_floor_disabled",
        '    "code": 3,',
        '    "code": 999,',
    ),
    # -- normalisation ------------------------------------------------------
    (
        # The load-bearing move deleted. Without it the #197 sweep reads as a
        # word gain and web-interface-guidelines-review goes green.
        "normalisation_removed",
        '    return URL_RE.sub(" ", LINK_RE.sub(lambda m: m.group(1), text))',
        "    return text",
    ),
    (
        # Narrowed back to links that end in SKILL.md, as it originally shipped.
        # De-linking any of the catalog's 37 external links then costs 3-8
        # invented words while the sentence keeps every real one -- the
        # false-positive direction, on the repo's own routine link maintenance.
        "link_pattern_narrowed_to_skill_files",
        r'LINK_RE = re.compile(r"!?\[([^\]\n]*)\]\([^)\n]*\)")',
        r'LINK_RE = re.compile(r"\[([^\]\n]+)\]\([^)\s]*?SKILL\.md(?:#[^)\s]*)?\)")',
    ),
    (
        # URLs become prose again, so dropping a rotted reference is charged as
        # a deletion of however many path segments it happened to have.
        "urls_counted_as_words",
        '    return URL_RE.sub(" ", LINK_RE.sub(lambda m: m.group(1), text))',
        "    return LINK_RE.sub(lambda m: m.group(1), text)",
    ),
    # -- the scopes ---------------------------------------------------------
    (
        # All three parts collapse into one, restoring whole-file scoring.
        # Padding the `description:` then pays for a deleted body section, and
        # filler prose pays for a deleted code example -- both reproduced, both
        # green, on the file that really did lose its CLUD_BUG_QUIET section.
        "scopes_netted_together",
        '    return {\n        "frontmatter": frontmatter,\n'
        '        "prose": "\\n".join(prose),\n        "code": "\\n".join(code),\n    }',
        '    return {"frontmatter": "", "prose": text, "code": ""}',
    ),
    (
        # The frontmatter folds into the prose scope, which is the specific
        # half of the evasion above: the size cap excludes the frontmatter, so
        # padding there is free against the constraint that caused the defect.
        "frontmatter_folded_into_the_body",
        "    frontmatter, body = (text[: m.end()], text[m.end() :]) if m else "
        '("", text)',
        '    frontmatter, body = "", text',
    ),
    (
        # Replacements stop offsetting removals, so every reword and typo fix
        # scores as loss. This is the false-positive direction: the gate turns
        # into noise and people route around it.
        "gains_ignored",
        "            self.scopes[name] = sum((b - a).values()) - sum((a - b).values())",
        "            self.scopes[name] = sum((b - a).values())",
    ),
    # -- scope of the gate --------------------------------------------------
    (
        # Every markdown file becomes a SKILL.md. A trimmed README then fails
        # the gate with a message calling it a SKILL.md and a ledger row for a
        # skill named "" -- unusable, and the false-positive direction again.
        "skill_glob_matches_any_md",
        r'SKILL_GLOB_RE = re.compile(r"^skills/[^/]+/SKILL\.md$")',
        r'SKILL_GLOB_RE = re.compile(r".*\.md$")',
    ),
    (
        # Renames stop being paired, so a skill renamed in the same change that
        # cuts it drops out of both sides of the comparison and the gate prints
        # OK over a deletion it never looked at.
        "rename_pairing_removed",
        '        "diff", "--name-status", "--find-renames=25%", base, head, "--", "skills"',
        '        "diff", "--name-status", "--no-renames", base, head, "--", "skills"',
    ),
    (
        # Unchanged files enter the comparison, so the success line reports
        # every skill in the repo as changed on a one-file pull request.
        "collect_includes_unchanged_files",
        "        if before != after:\n            self.cases[new] = (before, after)",
        "        self.cases[new] = (before, after)",
    ),
    (
        # The base becomes the trunk TIP rather than the merge base, so main's
        # own edits are charged to this branch and the number the author is
        # told to declare is not the number CI will demand.
        "base_defaults_to_the_trunk_tip",
        '        got = _git("merge-base", trunk, "HEAD")',
        '        got = _git("rev-parse", trunk)',
    ),
    # -- the escape hatch ---------------------------------------------------
    (
        # The ledger becomes a standing exemption: a row merged to main once
        # excuses every later deletion from that skill, silently.
        "ledger_not_scoped_to_the_change",
        "    added = collections.Counter() if withdrawn else surplus",
        "    added = after_rows",
    ),
    (
        # The append-only rule deleted, so a row taken back out of the ledger
        # costs nothing. An edit is a withdrawal plus an addition, so this
        # hands a free declaration to an edit of ANY column of an inherited
        # row -- the count worst of all, where one character covers any number
        # the author cares to type.
        "ledger_credits_rows_a_change_withdrew",
        "    added = collections.Counter() if withdrawn else surplus",
        "    added = surplus",
    ),
    (
        # The append-only rule narrowed to "the ledger got longer", which is
        # the near-miss fix: it stops a bare edit, and one throwaway row buys
        # it back. The row that grows the total and the row that covers the cut
        # are then allowed to be different rows.
        "ledger_void_replaced_by_a_growing_row_count",
        "    added = collections.Counter() if withdrawn else surplus",
        "    added = (\n"
        "        surplus\n"
        "        if sum(after_rows.values()) > sum(before_rows.values())\n"
        "        else collections.Counter()\n    )",
    ),
    (
        # Collapsing AFTER subtracting instead of before. Under the append-only
        # rule this no longer manufactures a declaration -- it voids one: an
        # edit to an inherited row's wording, a typo fix or a trailing full
        # stop, reads as that row withdrawn, so a copyedit to somebody else's
        # old row kills the author's own genuine declaration in the same PR.
        "ledger_collapsed_after_subtracting_not_before",
        "    surplus = after_rows - before_rows\n"
        "    withdrawn = before_rows - after_rows",
        "    _before, _after = parse_ledger(ledger_before), parse_ledger(ledger_after)\n"
        "    surplus = rows_by_size(_after - _before)\n"
        "    withdrawn = rows_by_size(_before - _after)",
    ),
    (
        # The failure stops naming the withdrawal that caused it. The author is
        # then looking at a ledger row that covers their cut and a gate that
        # fails anyway with no reason given -- which is how a gate stops being
        # read and starts being routed around.
        "withdrawal_not_explained_in_the_message",
        "            if withdrawn and declares(surplus, skill, loss.net)",
        "            if False",
    ),
    (
        # The count stops binding. A row can then be written blind, and the
        # size of the cut never reaches the reviewer's eye.
        "ledger_count_ignored",
        "    return any(s == skill and c >= net for s, c in added)",
        "    return any(s == skill for s, c in added)",
    ),
    (
        # The count binds exactly instead of as a floor, so any later commit in
        # the pull request that ADDS words invalidates a correct declaration and
        # demands a fresh number -- a review round breaks the gate.
        "ledger_count_must_match_exactly",
        "    return any(s == skill and c >= net for s, c in added)",
        "    return any(s == skill and c == net for s, c in added)",
    ),
    (
        # Rows lose their multiplicity and their reason, so a skill that has
        # already declared a cut of this size can never declare another. The
        # author follows the printed instruction, git shows the row added by
        # their change, and the gate fails anyway -- an escape hatch that
        # cannot be opened is a bypass with extra steps.
        "ledger_rows_lose_their_multiplicity",
        "            found[(skill, int(count), reason)] += 1",
        '            found[(skill, int(count), "")] = 1',
    ),
    (
        # An undeclared declaration starts counting -- a row with no reason.
        "ledger_reason_not_required",
        '        if not reason.strip("- ") or REASON_PLACEHOLDER in reason:',
        "        if False:",
    ),
    (
        # The unfilled placeholder starts counting, so the hatch becomes
        # automatic: paste the row the failure printed, ship, say nothing.
        "ledger_placeholder_accepted",
        'if not reason.strip("- ") or REASON_PLACEHOLDER in reason:',
        'if not reason.strip("- "):',
    ),
    (
        # Fences and comments stop being stripped, so the ledger's own worked
        # example -- printed in a fence directly above the table -- parses as a
        # live declaration. The hatch could then be used while the table a
        # reader actually reads stayed empty, which is the whole point of it.
        "ledger_fences_not_stripped",
        '    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)',
        "    return text",
    ),
    (
        # Parsing stops being anchored to the table, so any pipe-shaped line
        # anywhere in the document declares a removal.
        "ledger_not_anchored_to_the_table",
        "        if not in_table:\n            continue",
        "        if False:\n            continue",
    ),
    # -- the message --------------------------------------------------------
    (
        # Replaced blocks become quotable again, so "Gone:" starts quoting
        # passages that are still in the file. An author whose first encounter
        # with a gate is a message wrong about their own diff routes around it.
        "excerpt_quotes_replaced_blocks",
        '            if tag != "delete":',
        '            if tag not in ("delete", "replace"):',
    ),
    (
        # The breakdown lists only the parts that fired, so it no longer sums
        # to the total the author is told to write into the ledger -- leaving
        # two numbers in one message and no way to tell which is real.
        "breakdown_omits_parts_below_their_floor",
        "            for n, v in sorted(self.scopes.items(), key=lambda kv: -kv[1])",
        "            for n, v in sorted(self.over.items(), key=lambda kv: -kv[1])",
    ),
]


def _scratch(tmp_path: Path, source: str) -> Path:
    """A runnable copy of the suite against `source` as the detector."""
    tests = tmp_path / "tests"
    tests.mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "check_prose_retention.py").write_text(
        source, encoding="utf-8"
    )

    # The suite asserts the shipped ledger declares nothing; it resolves that
    # path relative to itself, so the scratch tree needs the real file.
    (tmp_path / "docs").mkdir()
    shutil.copy(LEDGER, tmp_path / "docs" / "prose-removals.md")

    shutil.copy(SUITE, tests / SUITE.name)
    shutil.copytree(FIXTURES, tests / "fixtures" / "prose-retention")
    (tests / "conftest.py").write_text(
        "import sys\n"
        "from pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))\n",
        encoding="utf-8",
    )
    return tests


def _run_suite(tests: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            str(tests),
            "-q",
            "-p",
            "no:cacheprovider",
            *extra,
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=tests.parent,
    )


def test_control_the_unmutated_detector_is_green(tmp_path):
    """The scratch harness can report success. Without this, every red below
    is equally explained by a broken harness.
    """
    tests = _scratch(tmp_path, DETECTOR.read_text(encoding="utf-8"))
    result = _run_suite(tests)
    assert result.returncode == 0, (
        "the unmutated suite is not green in the scratch tree, so nothing "
        f"below is evidence:\n{result.stdout}\n{result.stderr}"
    )


def test_every_mutation_is_named_once():
    """Two entries under one name would report as one parametrized case and
    quietly halve the evidence.
    """
    names = [m[0] for m in MUTATIONS]
    assert len(names) == len(set(names)), sorted(
        n for n in names if names.count(n) > 1
    )


@pytest.mark.parametrize("name,old,new", MUTATIONS, ids=[m[0] for m in MUTATIONS])
def test_mutation_turns_the_suite_red(tmp_path, name, old, new):
    source = DETECTOR.read_text(encoding="utf-8")

    assert source.count(old) == 1, (
        f"mutation {name!r} does not match the detector exactly once "
        f"({source.count(old)} matches). The detector changed shape; update "
        "the mutation so it keeps testing what it claims to."
    )
    mutated = source.replace(old, new)
    assert mutated != source, f"mutation {name!r} did not land"

    tests = _scratch(tmp_path, mutated)
    result = _run_suite(tests, "-x")
    assert result.returncode != 0, (
        f"mutation {name!r} was applied and the suite still passed, so nothing "
        f"in it constrains that behaviour:\n{result.stdout}"
    )
