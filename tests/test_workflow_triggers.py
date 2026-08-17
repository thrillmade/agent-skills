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
