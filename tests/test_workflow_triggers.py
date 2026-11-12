"""The gates must be able to see every input they read.

A `paths:` filter on a gate is a standing hazard here, for two reasons that are
both matters of record rather than opinion:

1. GitHub treats a filter-skipped check as "expected but never reported". Once a
   `required_status_checks` rule names that check, a pull request touching none
   of the filtered paths blocks forever. `check-doc-links.yml:8-12` documents
   this in this repository, in logmind's own words.

2. A filter has to enumerate every input, and the enumeration rots. The skill
   validator's filter never listed `skills/skill-size-budget.json`, so for the
   whole life of the size ratchet a pull request editing only the budget did not
   run the gate the budget configures. Raising the limit disabled the gate
   without triggering it.

These tests fail if a filter is reintroduced, so the second instance has to be
argued for rather than merely typed.
"""

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

# Gates whose result is (or is intended to be) a merge condition. A filter on
# one of these is the failure described above. Workflows NOT listed here are
# free to filter — a scheduled refresh or a notifier has no such constraint.
UNCONDITIONAL_GATES = [
    "validate-skills.yml",
    "test.yml",
    # A prose-retention filter would be the same mistake twice over: the gate
    # reads every SKILL.md plus docs/prose-removals.md, and that ledger is its
    # escape hatch — a filter omitting it would let a change edit the hatch
    # without running the gate the hatch configures, which is exactly how the
    # size gate came to be blind to its own budget file.
    "check-prose-retention.yml",
]


def _load(name):
    path = WORKFLOWS / name
    assert path.exists(), f"{name} is missing from {WORKFLOWS}"
    # `on:` is the YAML 1.1 boolean True, not the string "on" — PyYAML resolves
    # it before we see it. Look the key up both ways so this does not silently
    # pass by finding nothing.
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    triggers = doc.get("on", doc.get(True))
    assert triggers is not None, f"{name} declares no triggers at all"
    return doc, triggers


@pytest.mark.parametrize("name", UNCONDITIONAL_GATES)
def test_gate_has_no_paths_filter(name):
    """A merge gate must run on every pull request, not a guessed subset."""
    _, triggers = _load(name)
    assert isinstance(triggers, dict), f"{name}: expected a trigger mapping"

    for event, config in triggers.items():
        if not isinstance(config, dict):
            continue  # e.g. `pull_request:` with no body — the shape we want
        for key in ("paths", "paths-ignore"):
            assert key not in config, (
                f"{name} reintroduced a `{key}:` filter on `{event}`. "
                "A filter-skipped check reports as expected-but-missing and "
                "blocks the merge once it is required, and the path list rots "
                "— this repo already shipped a size gate that could not see "
                "edits to its own budget file. If a filter is genuinely "
                "needed, delete this assertion in the same commit and say why."
            )


@pytest.mark.parametrize("name", UNCONDITIONAL_GATES)
def test_gate_runs_on_pull_request(name):
    """A gate nobody triggers is not a gate."""
    _, triggers = _load(name)
    assert "pull_request" in triggers, (
        f"{name} does not run on `pull_request`, so it cannot gate anything."
    )


def test_validator_inputs_are_reachable():
    """Every path the validator reads must be reachable by its trigger.

    With no filter this holds by construction. The test states the obligation
    anyway, so that reintroducing a filter fails here with the reason attached
    rather than passing quietly and stranding one of these inputs.
    """
    _, triggers = _load("validate-skills.yml")
    reads = [
        "skills/*/SKILL.md",  # the subject
        "docs/placement-map.json",  # reconciled 1:1 against skills/
        ".github/scripts/validate_skills.py",  # the rules themselves
    ]
    pr = triggers.get("pull_request")
    unfiltered = pr is None or (isinstance(pr, dict) and "paths" not in pr)
    assert unfiltered, (
        "validate-skills.yml filters `pull_request`, so these inputs are no "
        f"longer guaranteed reachable: {reads}. Either drop the filter or "
        "prove every one of them is covered."
    )


def test_prose_retention_checks_out_full_history():
    """A comparison gate cannot run on a shallow clone.

    `check-prose-retention` reads each SKILL.md at two revisions. The default
    `actions/checkout` depth of 1 has neither the base nor the merge base, so
    the gate would fail to resolve its base on every run — and the fix would
    look like "the gate is flaky" rather than "the checkout is wrong". Assert
    the depth here so it cannot be dropped in passing.
    """
    doc, _ = _load("check-prose-retention.yml")
    steps = doc["jobs"]["prose-retention"]["steps"]
    checkout = next(s for s in steps if str(s.get("uses", "")).startswith("actions/checkout"))
    # `with:` YAML-loads as None once its last key is removed, so coalesce
    # rather than letting this fail with an AttributeError and no explanation.
    assert (checkout.get("with") or {}).get("fetch-depth") == 0, (
        "check-prose-retention.yml checks out shallow. The gate compares a "
        "base revision against a head revision; without the full history it "
        "cannot resolve the base and refuses to report success."
    )


def test_validate_skills_checks_out_full_history_for_the_ancestry_gate():
    """`gen_skill_versions.py --check` asks whether each history row's commit
    is an ancestor of the PR head. On a depth-1 checkout every older commit
    looks missing, so the gate would fail every run for the clone's sake."""
    doc, _ = _load("validate-skills.yml")
    steps = doc["jobs"]["validate"]["steps"]
    checkout = next(s for s in steps if str(s.get("uses", "")).startswith("actions/checkout"))
    assert (checkout.get("with") or {}).get("fetch-depth") == 0, (
        "validate-skills.yml checks out shallow, so the version-history "
        "ancestry check cannot see the commits it is asked about."
    )
    assert any("gen_skill_versions.py" in str(s.get("run", "")) and "--check" in str(s.get("run", ""))
               for s in steps), "validate-skills.yml no longer runs the ancestry check."


# --- skill-census: token scope, own name, alarms (#313) ---------------------
#
# The census stopped four Mondays running because its token request named a
# repository by a stale literal, and nothing alarmed. These pin the shape that
# fixes both: the token's scope comes from `census_counters.py --resolve`
# (CONSUMER_REPOS is the only list), no repository name is typed into the
# workflow, and two alarms — one on the day, one that does not depend on the
# census running at all — file into the same issue.

import re  # noqa: E402 -- grouped with the tests that use it

import census_counters  # noqa: E402 -- conftest puts .github/scripts on sys.path

CENSUS = "skill-census.yml"
WATCHDOG = "census-watchdog.yml"
APP_TOKEN_ACTION = "actions/create-github-app-token@"


def _census_steps():
    doc, _ = _load(CENSUS)
    return doc, doc["jobs"]["census"]["steps"]


def _step(steps, step_id):
    matches = [s for s in steps if s.get("id") == step_id]
    assert len(matches) == 1, f"expected one step with id {step_id!r}"
    return steps.index(matches[0]), matches[0]


def test_census_token_scope_comes_from_the_resolve_step():
    _, steps = _census_steps()
    i_lookup, lookup = _step(steps, "lookup_token")
    i_resolve, resolve = _step(steps, "resolve")
    i_token, token = _step(steps, "app_token")
    i_counters, _ = _step(steps, "counters")
    assert i_lookup < i_resolve < i_token < i_counters

    # The lookup token can list the installation and do nothing else.
    assert str(lookup["uses"]).startswith(APP_TOKEN_ACTION)
    lookup_with = lookup["with"]
    assert lookup_with.get("permission-metadata") == "read"
    assert not [k for k in lookup_with if k.startswith("permission-") and k != "permission-metadata"]
    assert "repositories" not in lookup_with

    assert "census_counters.py --resolve" in resolve["run"]
    assert resolve["env"]["LOOKUP_TOKEN"] == "${{ steps.lookup_token.outputs.token }}"

    # The steward token's scope is exactly what --resolve wrote, and the step
    # does not run on an empty list: an empty `repositories` input with
    # `owner` set is a token for every repository the App can see.
    assert str(token["uses"]).startswith(APP_TOKEN_ACTION)
    assert token["with"]["repositories"] == "${{ steps.resolve.outputs.repositories }}"
    assert token.get("if") == "${{ steps.resolve.outputs.repositories != '' }}"


def test_census_workflow_names_no_repository_literally():
    """CONSUMER_REPOS is the only list, and this repo's own name comes from
    the run context — so no repository name appears anywhere in the file,
    comments included."""
    text = (WORKFLOWS / CENSUS).read_text(encoding="utf-8")
    names = list(census_counters.CONSUMER_REPOS) + [
        census_counters._SELF_REPO_FALLBACK.split("/", 1)[1],
        "agent-skills",
    ]
    for name in names:
        hits = [
            line.strip()
            for line in text.splitlines()
            if re.search(rf"(?<![\w-]){re.escape(name)}(?![\w-])", line)
        ]
        assert not hits, f"{CENSUS} names {name!r} literally: {hits}"
    _, steps = _census_steps()
    _, file_issues = _step(steps, "file_issues")
    assert file_issues["env"]["GH_REPO"] == "${{ github.repository }}"


def test_census_alarm_job_runs_on_any_non_success_with_its_own_issues_write():
    doc, _ = _load(CENSUS)
    assert doc["permissions"] == {"contents": "read"}, (
        "workflow-level permissions widened; the alarm job carries its own"
    )
    alarm = doc["jobs"]["alarm"]
    assert alarm["needs"] == "census"
    cond = alarm["if"]
    assert "always()" in cond
    assert "needs.census.result != 'success'" in cond
    assert "github.event_name == 'schedule'" in cond
    assert alarm["permissions"] == {"issues": "write"}
    body = yaml.safe_dump(alarm)
    assert "secrets." not in body, "the alarm must not depend on the App secrets the census needs"
    assert "workflow-failure-key: skill-census" in body


def test_watchdog_lives_outside_the_census_failure_domain():
    doc, triggers = _load(WATCHDOG)
    assert triggers["schedule"] == [{"cron": "0 12 * * 2"}]
    assert "workflow_dispatch" in triggers
    assert "workflow_run" not in triggers
    text = (WORKFLOWS / WATCHDOG).read_text(encoding="utf-8")
    assert "secrets." not in text
    assert APP_TOKEN_ACTION not in text
    for job in doc["jobs"].values():
        assert "needs" not in job
    assert doc["permissions"] == {"actions": "read", "issues": "write"}

    env = doc["jobs"]["watchdog"]["steps"][0]["env"]
    assert env["CENSUS_WORKFLOW"] == CENSUS
    assert (WORKFLOWS / env["CENSUS_WORKFLOW"]).exists()
    # Two weekly cadences, while the census is weekly.
    _, census_triggers = _load(CENSUS)
    assert census_triggers["schedule"] == [{"cron": "0 12 * * 1"}]
    assert int(env["MAX_AGE_DAYS"]) == 2 * 7
    assert "workflow-failure-key: skill-census" in text
