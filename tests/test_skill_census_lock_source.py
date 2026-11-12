"""A lock entry sourced under the catalog's former name must stay drift-checkable.

The catalog repo was renamed; every subscriber's skills-lock.json written
before the rename still says `"source": "thrillmade/agent-skills"`. The census
treated any source that was not exactly the new name as a foreign catalog and
dropped it, so the drift section had nothing to check for every existing
subscriber and read as an all-clear. These tests drive the drift result and the
rendered digest section from fake lock payloads, so they pin what an operator
reads, not just the source-matching helper.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".github" / "scripts" / "census_counters.py"

OLD_NAME = "thrillmade/agent-skills"
NEW_NAME = "thrillmade/thrill-skills"
FOREIGN = "example-org/other-catalog"
# An invented future name, standing for the next rename.
RENAMED = "thrillmade/invented-future-catalog"


def _load(repository: str):
    """Load the module as a run in `repository` would. The current name is
    read from GITHUB_REPOSITORY at import, so pinning it here keeps these
    tests independent of whatever the environment running them sets.
    Importing only defines constants and functions: STEWARD_TOKEN, OUT_DIR and
    the network all live inside main()."""
    spec = importlib.util.spec_from_file_location(
        f"census_counters_as_{repository.replace('/', '_').replace('-', '_')}", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(os.environ, {"GITHUB_REPOSITORY": repository}):
        spec.loader.exec_module(module)
    return module


cc = _load(NEW_NAME)

NOT_CHECKABLE_LINE = "nothing to check"


def _lock(source: object, slug: str = "some-skill") -> dict:
    meta = {
        "skillPath": f"skills/{slug}/SKILL.md",
        "computedHash": "a" * 64,
    }
    if source is not None:
        meta["source"] = source
    return {"version": 1, "skills": {slug: meta}}


def _digest_for(lock: dict, module=None) -> tuple[list[dict], str]:
    """Run a lock through the parse -> drift -> digest path an operator reads."""
    cc_ = module or cc
    checkable, unscoped = cc_.parse_lock_hashes(lock)
    repos = {
        "fake-subscriber": {
            "subscribed": [],
            "local": [],
            "untracked": [],
            "lock_subscriptions": checkable,
            "unscoped_subscriptions": unscoped,
        }
    }
    signals = cc_.compute_signals([], repos)
    signals["subscription_drift"] = cc_.compute_subscription_drift(repos, algo=None)
    census = {
        "cycle": "2026-W01",
        "generated_at": "2026-01-01T00:00:00Z",
        "repos": repos,
        "signals": signals,
        "stale_docket": {"open_count": 0, "stale_count": 0, "stale": []},
    }
    return signals["subscription_drift"], cc_.render_digest(census)


def test_old_name_is_drift_checkable():
    drift, digest = _digest_for(_lock(OLD_NAME, "old-skill"))
    assert [(r["status"], r["skills"]) for r in drift] == [("indeterminate", ["old-skill"])]
    assert NOT_CHECKABLE_LINE not in digest
    assert "`old-skill`" in digest


def test_new_name_is_drift_checkable():
    drift, digest = _digest_for(_lock(NEW_NAME, "new-skill"))
    assert [(r["status"], r["skills"]) for r in drift] == [("indeterminate", ["new-skill"])]
    assert NOT_CHECKABLE_LINE not in digest


def test_foreign_source_is_excluded():
    drift, digest = _digest_for(_lock(FOREIGN))
    assert drift == []
    assert NOT_CHECKABLE_LINE in digest


def test_missing_or_empty_source_is_unscoped():
    for lock in (_lock(None, "no-src"), _lock("", "no-src")):
        drift, digest = _digest_for(lock)
        assert [(r["status"], r["skills"]) for r in drift] == [("unscoped", ["no-src"])]
        assert "unscoped" in digest


def test_digest_still_names_the_current_catalog():
    _, digest = _digest_for(_lock(None))
    assert NEW_NAME in digest
    assert OLD_NAME not in digest


def test_every_former_name_survives_the_next_rename():
    """After another rename the current name comes from the run context, and
    locks written under BOTH earlier names must still be recognised -- the
    silent drop the former-name alias was added to fix, one rename later."""
    renamed = _load(RENAMED)
    for source, slug in ((OLD_NAME, "old-skill"), (NEW_NAME, "new-skill"), (RENAMED, "renamed-skill")):
        drift, digest = _digest_for(_lock(source, slug), renamed)
        assert [(r["status"], r["skills"]) for r in drift] == [("indeterminate", [slug])], source
        assert NOT_CHECKABLE_LINE not in digest
    drift, digest = _digest_for(_lock(FOREIGN), renamed)
    assert drift == []
    assert NOT_CHECKABLE_LINE in digest

