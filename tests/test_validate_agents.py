"""Characterization tests for `.github/scripts/validate_agents.py` -- the
SPEC §2.4 agent-roster gate.

Mirrors `tests/test_validate_skills.py`'s own layout and conventions (a
throwaway tree fixture, one rule broken at a time off a valid baseline, `::
error file=...::` messages pinned verbatim) one directory over: `.claude/
agents/<name>.md` in place of `skills/<name>/SKILL.md`, and the `agents/`
slice of `docs/placement-map.json` in place of the whole file.

`conftest.py`'s `SCRIPTS` sys.path insertion (needed to `import
validate_skills`) already makes `validate_agents` importable the same way --
nothing here adds a second sys.path entry.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import validate_agents

# Every per-role error is filed against the role file, relative to the cwd.
ALPHA = "::error file=.claude/agents/alpha.md::"
PM = "::error file=docs/placement-map.json::"

VALID_ROLE = """---
name: {name}
description: What this role does and when to reach for it.
---

Body.
"""


def only(errors: list[str]) -> str:
    """Assert the tree produced exactly one error and return it -- guards the
    common false pass where a fixture trips a second rule by accident.
    """
    assert len(errors) == 1, f"expected exactly one error, got {errors}"
    return errors[0]


class RoleTree:
    """A throwaway repo-shaped tree: `.claude/agents/<name>.md` plus an
    optional `docs/placement-map.json`. The fixture chdirs into it, because
    the gate resolves both paths relative to the cwd.
    """

    def __init__(self, base: Path) -> None:
        self.base = base

    def role(self, name: str, text: str | None = None) -> Path:
        """Create `.claude/agents/<name>.md`. `text=None` leaves the file
        unwritten (the "no role files" case, when it is the only one).
        """
        d = self.base / ".claude" / "agents"
        d.mkdir(parents=True, exist_ok=True)
        path = d / f"{name}.md"
        if text is not None:
            path.write_text(text, encoding="utf-8")
        return path

    def valid_role(self, name: str = "alpha") -> Path:
        return self.role(name, VALID_ROLE.format(name=name))

    def role_dir(self, name: str) -> Path:
        """Create a DIRECTORY at `.claude/agents/<name>.md` -- `_role_files`
        globs `*.md` with no type filter, so this reaches the per-file loop
        exactly like a real role file would.
        """
        d = self.base / ".claude" / "agents" / f"{name}.md"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def frontmatter(self, name: str = "alpha", extra: str = "", body: str = "\nBody.\n") -> Path:
        """A valid role with `extra` YAML lines spliced into the frontmatter."""
        fm = f"---\nname: {name}\ndescription: What this role does.\n{extra}---\n"
        return self.role(name, fm + body)

    def placement_map(self, obj: object = None, raw: str | None = None) -> Path:
        d = self.base / "docs"
        d.mkdir(parents=True, exist_ok=True)
        path = d / "placement-map.json"
        path.write_text(raw if raw is not None else json.dumps(obj), encoding="utf-8")
        return path

    def validate(self) -> list[str]:
        return validate_agents.run(Path(".claude/agents"))


@pytest.fixture
def roles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> RoleTree:
    monkeypatch.chdir(tmp_path)
    return RoleTree(tmp_path)


# --- File and frontmatter presence ------------------------------------------


def test_clean_tree_produces_no_errors(roles: RoleTree) -> None:
    roles.valid_role()
    assert roles.validate() == []


def test_multiple_valid_roles_produce_no_errors(roles: RoleTree) -> None:
    roles.valid_role("alpha")
    roles.valid_role("beta")
    roles.valid_role("gamma")
    assert roles.validate() == []


def test_a_directory_named_like_a_role_is_reported_not_crashed(roles: RoleTree) -> None:
    # `_role_files` globs `*.md` with no `is_file()` filter, so a directory
    # under `.claude/agents/` whose name happens to end `.md` reaches the
    # per-file loop too. Before the guard, `role_path.read_bytes()` raised
    # `IsADirectoryError` uncaught, taking the whole run down instead of
    # producing an annotation -- confirmed by reverting the guard locally.
    roles.role_dir("alpha")
    assert only(roles.validate()) == ALPHA + ".claude/agents/alpha.md is not a file"


def test_missing_frontmatter(roles: RoleTree) -> None:
    roles.role("alpha", "No frontmatter at all.\n")
    assert only(roles.validate()) == (
        ALPHA + "missing YAML frontmatter (must start with --- ... --- block)"
    )


def test_frontmatter_must_start_at_byte_zero(roles: RoleTree) -> None:
    roles.role("alpha", "\n---\nname: alpha\ndescription: d\n---\n\nBody.\n")
    assert only(roles.validate()) == (
        ALPHA + "missing YAML frontmatter (must start with --- ... --- block)"
    )


def test_invalid_yaml_frontmatter(roles: RoleTree) -> None:
    roles.role("alpha", "---\nname: alpha\n  bad: [unclosed\n---\n\nBody.\n")
    error = only(roles.validate())
    assert error.startswith(ALPHA + "frontmatter is not valid YAML: ")


def test_frontmatter_must_be_a_mapping(roles: RoleTree) -> None:
    roles.role("alpha", "---\n- one\n- two\n---\n\nBody.\n")
    assert only(roles.validate()) == ALPHA + "frontmatter must be a YAML mapping"


def test_empty_frontmatter_reports_name_and_description(roles: RoleTree) -> None:
    roles.role("alpha", "---\n\n---\n\nBody.\n")
    assert roles.validate() == [
        ALPHA + "frontmatter is missing a non-empty `name:` field",
        ALPHA + "frontmatter is missing a non-empty `description:` field",
    ]


# --- name --------------------------------------------------------------------


def test_missing_name(roles: RoleTree) -> None:
    roles.role("alpha", "---\ndescription: d\n---\n\nBody.\n")
    assert only(roles.validate()) == ALPHA + "frontmatter is missing a non-empty `name:` field"


def test_whitespace_only_name(roles: RoleTree) -> None:
    roles.role("alpha", '---\nname: "   "\ndescription: d\n---\n\nBody.\n')
    assert only(roles.validate()) == ALPHA + "frontmatter is missing a non-empty `name:` field"


def test_non_string_name_reads_as_missing(roles: RoleTree) -> None:
    roles.role("alpha", "---\nname: 42\ndescription: d\n---\n\nBody.\n")
    assert only(roles.validate()) == ALPHA + "frontmatter is missing a non-empty `name:` field"


def test_name_must_match_filename(roles: RoleTree) -> None:
    roles.role("alpha", "---\nname: beta\ndescription: d\n---\n\nBody.\n")
    assert only(roles.validate()) == (
        ALPHA + "frontmatter name='beta' does not match filename 'alpha'"
    )


@pytest.mark.parametrize("name", ["Alpha", "9alpha", "al pha", "al_pha", ""])
def test_name_must_match_the_slug_regex(roles: RoleTree, name: str) -> None:
    if not name:
        pytest.skip("empty name is covered by the missing-name test")
    roles.role("alpha", f"---\nname: {name}\ndescription: d\n---\n\nBody.\n")
    errors = roles.validate()
    assert any("does not match the SPEC §2.4 slug regex" in e for e in errors), errors


# --- description ---------------------------------------------------------


def test_missing_description(roles: RoleTree) -> None:
    roles.role("alpha", "---\nname: alpha\n---\n\nBody.\n")
    assert only(roles.validate()) == (
        ALPHA + "frontmatter is missing a non-empty `description:` field"
    )


def test_whitespace_only_description(roles: RoleTree) -> None:
    roles.role("alpha", '---\nname: alpha\ndescription: "   "\n---\n\nBody.\n')
    assert only(roles.validate()) == (
        ALPHA + "frontmatter is missing a non-empty `description:` field"
    )


# --- trigger (SPEC §2.4: optional, default on-demand) -----------------------


@pytest.mark.parametrize("trigger", ["on-demand", "on-merge", "scheduled", "on-release"])
def test_valid_trigger_values(roles: RoleTree, trigger: str) -> None:
    roles.frontmatter("alpha", extra=f"trigger: {trigger}\n")
    assert roles.validate() == []


def test_absent_trigger_is_tolerated(roles: RoleTree) -> None:
    # No `trigger:` line at all -- SPEC §2.4 defaults it to on-demand, and
    # this gate never requires the field.
    roles.valid_role("alpha")
    assert roles.validate() == []


def test_invalid_trigger_value(roles: RoleTree) -> None:
    roles.frontmatter("alpha", extra="trigger: hourly\n")
    assert only(roles.validate()) == (
        ALPHA + "`trigger: 'hourly'` is not one of "
        "['on-demand', 'on-merge', 'on-release', 'scheduled'] (SPEC §2.4)"
    )


# --- optional fields round-trip untouched (tools/model/effort/color) --------


def test_tools_model_effort_color_are_never_validated(roles: RoleTree) -> None:
    # SPEC §2.4 places no enum or shape constraint on any of these -- unlike
    # a skill's `kind`/`source`, there is nothing here to check.
    roles.frontmatter(
        "alpha",
        extra=(
            "tools: Glob, Grep, LS, Read, Edit, Write, Bash, TodoWrite\n"
            "model: opus\n"
            "effort: high\n"
            "color: green\n"
        ),
    )
    assert roles.validate() == []


# --- errors accumulate across roles ------------------------------------------


def test_errors_accumulate_across_roles(roles: RoleTree) -> None:
    roles.role("alpha", "---\nname: beta\n---\n\nBody.\n")
    roles.valid_role("gamma")
    assert roles.validate() == [
        ALPHA + "frontmatter name='beta' does not match filename 'alpha'",
        ALPHA + "frontmatter is missing a non-empty `description:` field",
    ]


# --- docs/placement-map.json: the `agents/` slice ----------------------------


def valid_pm(**agent_entries: dict) -> dict:
    skills = {
        f"agents/{name}": entry for name, entry in agent_entries.items()
    }
    return {"version": 1, "updated": "2026-09-15", "families": [], "skills": skills}


ENTRY = {"authoring_home": "catalog", "distribution": "catalog-only", "subscribers": []}


def test_absent_placement_map_is_tolerated(roles: RoleTree) -> None:
    roles.valid_role()
    assert roles.validate() == []


def test_valid_placement_map(roles: RoleTree) -> None:
    roles.valid_role("alpha")
    roles.placement_map(valid_pm(alpha=ENTRY))
    assert roles.validate() == []


def test_malformed_placement_map_json_yields_exactly_one_error(roles: RoleTree) -> None:
    # This gate does not assume validate_skills.py ran first or at all --
    # each is a self-contained CI step, so a broken file must not read as
    # clean here just because another gate also reports it. Mirrors
    # validate_skills.py's own posture (`test_malformed_placement_map_json_
    # skips_the_shape_rules`): one error for the parse failure, and nothing
    # further -- reconciliation cannot run against an object that does not
    # exist.
    roles.valid_role("alpha")
    roles.placement_map(raw="{not json")
    error = only(roles.validate())
    assert error.startswith(PM + "docs/placement-map.json is not valid JSON: ")


def test_placement_map_top_level_not_an_object_is_tolerated(roles: RoleTree) -> None:
    roles.valid_role("alpha")
    roles.placement_map([1, 2, 3])
    assert roles.validate() == []


def test_placement_map_skills_not_an_object_is_tolerated(roles: RoleTree) -> None:
    roles.valid_role("alpha")
    roles.placement_map({"version": 1, "updated": "d", "families": [], "skills": []})
    assert roles.validate() == []


def test_a_bare_skill_slug_is_not_this_gates_business(roles: RoleTree) -> None:
    # A key with no `agents/` prefix is a skill, and validate_skills.py owns
    # it -- this gate must never look at it, valid or not.
    roles.valid_role("alpha")
    roles.placement_map(
        {
            "version": 1,
            "updated": "d",
            "families": [],
            "skills": {"some-skill": {"nonsense": True}},
        }
    )
    # Only the missing-agents-entry reconciliation fires; the bare skill key
    # produces nothing.
    assert only(roles.validate()) == (
        PM + "docs/placement-map.json is missing an `agents/` entry for: agents/alpha"
    )


def test_entry_must_be_an_object(roles: RoleTree) -> None:
    roles.valid_role("alpha")
    roles.placement_map(valid_pm(alpha="catalog"))
    assert only(roles.validate()) == (
        PM + "skills.agents/alpha must be an object (unknown per-entry keys are "
        "tolerated; the value itself must still be a mapping)"
    )


@pytest.mark.parametrize(
    "home", ["repo-mirrored:Bad_Name", "repo-mirrored:", "elsewhere", None, 7]
)
def test_invalid_authoring_home(roles: RoleTree, home: object) -> None:
    roles.valid_role("alpha")
    roles.placement_map(valid_pm(alpha={**ENTRY, "authoring_home": home}))
    assert only(roles.validate()) == (
        PM + f"skills.agents/alpha.authoring_home={home!r} must match "
        r"^(catalog|undecided|repo-mirrored:[a-z0-9-]+)$"
    )


@pytest.mark.parametrize("home", ["catalog", "undecided", "repo-mirrored:clud-bug"])
def test_valid_authoring_home(roles: RoleTree, home: str) -> None:
    roles.valid_role("alpha")
    roles.placement_map(valid_pm(alpha={**ENTRY, "authoring_home": home}))
    assert roles.validate() == []


@pytest.mark.parametrize("distribution", ["everywhere", None, ""])
def test_invalid_distribution(roles: RoleTree, distribution: object) -> None:
    roles.valid_role("alpha")
    roles.placement_map(valid_pm(alpha={**ENTRY, "distribution": distribution}))
    assert only(roles.validate()) == (
        PM + f"skills.agents/alpha.distribution={distribution!r} is not one of "
        "['catalog-only', 'default-on', 'opt-in']"
    )


@pytest.mark.parametrize("distribution", ["default-on", "opt-in", "catalog-only"])
def test_valid_distribution(roles: RoleTree, distribution: str) -> None:
    roles.valid_role("alpha")
    roles.placement_map(valid_pm(alpha={**ENTRY, "distribution": distribution}))
    assert roles.validate() == []


@pytest.mark.parametrize("subscribers", ["logmind", None, [1], [None]])
def test_subscribers_must_be_a_list_of_strings(roles: RoleTree, subscribers: object) -> None:
    roles.valid_role("alpha")
    roles.placement_map(valid_pm(alpha={**ENTRY, "subscribers": subscribers}))
    assert only(roles.validate()) == (
        PM + "skills.agents/alpha.subscribers must be a list of strings"
    )


def test_empty_subscribers_is_allowed(roles: RoleTree) -> None:
    roles.valid_role("alpha")
    roles.placement_map(valid_pm(alpha={**ENTRY, "subscribers": []}))
    assert roles.validate() == []


def test_placement_map_keys_reconcile_against_the_roster(roles: RoleTree) -> None:
    roles.valid_role("alpha")
    roles.valid_role("beta")
    roles.placement_map(valid_pm(alpha=ENTRY, ghost=ENTRY))
    assert roles.validate() == [
        PM + "docs/placement-map.json is missing an `agents/` entry for: agents/beta",
        PM + "docs/placement-map.json has an `agents/` entry for non-existent "
        ".claude/agents/ role(s): agents/ghost",
    ]


def test_reconciliation_lists_every_name(roles: RoleTree) -> None:
    roles.valid_role("alpha")
    roles.valid_role("beta")
    roles.valid_role("gamma")
    roles.placement_map(valid_pm(ghost=ENTRY, phantom=ENTRY))
    assert roles.validate() == [
        PM + "docs/placement-map.json is missing an `agents/` entry for: "
        "agents/alpha, agents/beta, agents/gamma",
        PM + "docs/placement-map.json has an `agents/` entry for non-existent "
        ".claude/agents/ role(s): agents/ghost, agents/phantom",
    ]


def test_a_role_with_a_bad_name_is_never_counted_as_present(roles: RoleTree) -> None:
    # `role_names` only gains an entry once `name` is validly formed AND
    # matches the filename -- a role failing that check must not silently
    # satisfy the placement-map reconcile too. The map's `agents/alpha`
    # entry therefore reads as EXTRA (nothing on disk validly claims
    # `alpha`), not as satisfied by the mismatched file sitting right there.
    roles.role("alpha", "---\nname: beta\ndescription: d\n---\n\nBody.\n")
    roles.placement_map(valid_pm(alpha=ENTRY))
    errors = roles.validate()
    assert ALPHA + "frontmatter name='beta' does not match filename 'alpha'" in errors
    assert (
        PM + "docs/placement-map.json has an `agents/` entry for non-existent "
        ".claude/agents/ role(s): agents/alpha"
        in errors
    )


# --- The coverage guard ------------------------------------------------------
#
# Mirrors validate_skills.py's own coverage guard one directory over: **if
# this gate discovers zero roles, that is a FAILURE, not a pass.** A clean
# list of errors is only evidence if it was produced against real roles.


def test_coverage_guard_passes_when_the_counts_agree(roles: RoleTree) -> None:
    roles.valid_role("alpha")
    roles.valid_role("beta")
    assert validate_agents.coverage_errors(Path(".claude/agents"), 2) == []


def test_coverage_guard_rejects_a_zero_count(roles: RoleTree) -> None:
    (roles.base / ".claude" / "agents").mkdir(parents=True)
    errors = validate_agents.coverage_errors(Path(".claude/agents"), 0)
    assert len(errors) == 1
    assert errors[0].startswith("::error::coverage guard: 0 agent roles validated")


def test_coverage_guard_rejects_a_count_that_disagrees_with_disk(roles: RoleTree) -> None:
    roles.valid_role("alpha")
    errors = validate_agents.coverage_errors(Path(".claude/agents"), 7)
    assert len(errors) == 1
    assert errors[0] == (
        "::error::coverage guard: validated 7 role file(s) but '.claude/agents' "
        "holds 1 .md file(s). The counts must agree or the pass is not evidence "
        "about the roles on disk."
    )


def test_coverage_guard_reports_both_failures_at_once(roles: RoleTree) -> None:
    roles.valid_role("alpha")
    assert len(validate_agents.coverage_errors(Path(".claude/agents"), 0)) == 2


def test_main_refuses_to_pass_when_nothing_was_validated(
    roles: RoleTree, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Delete the coverage guard from `main()` and this test goes red: the run
    prints `OK: 0 agent roles validated cleanly.` and returns 0 -- green CI
    over an empty roster, which is the failure this file exists to prevent.

    This is the mutation this gate has to survive: `run()` is monkeypatched
    to a version that vacuously reports clean (exactly what a broken `run()`
    that never actually walked the tree would do), over a roster directory
    that exists but holds nothing. If `main()` trusted `run()`'s empty list
    on its own, this would print OK and return 0.
    """
    (roles.base / ".claude" / "agents").mkdir(parents=True)
    monkeypatch.setattr(validate_agents, "run", lambda root: [])

    assert validate_agents.main() == 1
    out = capsys.readouterr().out
    assert "coverage guard: 0 agent roles validated" in out


# --- Infra-fatal conditions (exit 1, and deliberately no summary line) ------


def test_missing_agents_dir_exits_1_without_a_summary(
    roles: RoleTree, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit) as exc:
        validate_agents.main()
    assert exc.value.code == 1
    assert (
        capsys.readouterr().out == "::error::.claude/agents directory not found at repo root\n"
    )


def test_empty_agents_dir_exits_1_without_a_summary(
    roles: RoleTree, capsys: pytest.CaptureFixture[str]
) -> None:
    (roles.base / ".claude" / "agents").mkdir(parents=True)
    with pytest.raises(SystemExit) as exc:
        validate_agents.main()
    assert exc.value.code == 1
    assert capsys.readouterr().out == "::error::no role files under .claude/agents\n"


def test_a_file_named_agents_is_not_an_agents_dir(
    roles: RoleTree, capsys: pytest.CaptureFixture[str]
) -> None:
    (roles.base / ".claude").mkdir(parents=True)
    (roles.base / ".claude" / "agents").write_text("not a directory", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        validate_agents.main()
    assert exc.value.code == 1
    assert (
        capsys.readouterr().out == "::error::.claude/agents directory not found at repo root\n"
    )


# --- CLI summary + exit code -------------------------------------------------


def test_main_prints_ok_and_returns_0_on_a_clean_roster(
    roles: RoleTree, capsys: pytest.CaptureFixture[str]
) -> None:
    roles.valid_role("alpha")
    assert validate_agents.main() == 0
    assert capsys.readouterr().out == "OK: 1 agent roles validated cleanly.\n"


def test_main_prints_the_summary_line_and_returns_1_on_errors(
    roles: RoleTree, capsys: pytest.CaptureFixture[str]
) -> None:
    roles.role("alpha", "---\nname: beta\n---\n\nBody.\n")
    assert validate_agents.main() == 1
    out = capsys.readouterr().out
    assert "::error::2 agent role validation errors" in out
