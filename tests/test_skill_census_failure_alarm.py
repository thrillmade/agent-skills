"""#313: a census that stops, or never runs, must raise an alarm.

The census failed four scheduled Mondays in a row and nobody noticed: the
census is the thing that files issues, so a census that stops files nothing,
and no other workflow watched it. Two alarms now file into ONE issue (same
marker, so one incident is one issue):

- the `alarm` job in skill-census.yml, on the day a scheduled census does not
  succeed — the pattern logmind-self-update.yml's "Notify on failure" uses;
- census-watchdog.yml, a separate weekly workflow with no secrets and no App,
  which alarms when the newest successful scheduled census is more than two
  weekly cadences old — it catches a census that never started at all.

Both are tested by executing the real embedded bash against a fake `gh` and a
fake `date` on PATH, the same harness as test_skill_census_digest_closure.py,
and asserted on what an operator sees: the `gh issue` calls made, the log
lines and the exit code.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"

MARKER = "<!-- workflow-failure-key: skill-census -->"
TITLE = "Scheduled workflow failing: skill-census"
LABEL = "automation-failure"
RUN_URL = "https://github.example/thrillmade/thrill-skills/actions/runs/777"

# 2026-11-17T12:00:00Z, a Tuesday — when the watchdog runs.
NOW = 1794916800
DAY = 86400

FAKE_GH = """#!/usr/bin/env python3
import json
import os
import sys

argv = sys.argv[1:]


def log(record):
    with open(os.environ["GH_CALL_LOG"], "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\\n")


def flag(name, rest):
    return rest[rest.index(name) + 1] if name in rest else None


if argv[:2] == ["label", "create"]:
    sys.exit(0)

if argv[:2] == ["run", "list"]:
    log({"cmd": "run list", "argv": argv[2:]})
    if os.environ.get("GH_RUN_LIST_FAILS") == "1":
        print("HTTP 502: transient error", file=sys.stderr)
        sys.exit(1)
    sys.stdout.write(os.environ.get("GH_RUN_LIST_JSON", "[]"))
    sys.exit(0)

if argv[:2] == ["issue", "list"]:
    log({"cmd": "issue list", "search": flag("--search", argv)})
    sys.stdout.write(os.environ.get("GH_ISSUE_LIST_JSON", "[]"))
    sys.exit(0)

if argv[:2] == ["issue", "comment"]:
    rest = argv[3:]
    body = flag("--body", rest)
    if body is None and "--body-file" in rest:
        body = open(flag("--body-file", rest), encoding="utf-8").read()
    log({"cmd": "comment", "number": argv[2], "body": body})
    sys.exit(0)

if argv[:2] == ["issue", "create"]:
    rest = argv[2:]
    body = open(flag("--body-file", rest), encoding="utf-8").read()
    log({"cmd": "create", "title": flag("--title", rest), "label": flag("--label", rest), "body": body})
    print("https://github.example/thrillmade/thrill-skills/issues/900")
    sys.exit(0)

print(f"unexpected gh invocation: {argv}", file=sys.stderr)
sys.exit(1)
"""

FAKE_DATE = """#!/bin/sh
if [ "$1" = "-u" ] && [ "$2" = "+%s" ]; then
  echo "$FAKE_NOW"
  exit 0
fi
if [ "$1" = "-u" ] && [ "$2" = "+%Y-%m-%dT%H:%MZ" ]; then
  echo "2026-11-17T12:00Z"
  exit 0
fi
echo "unexpected date invocation: $*" >&2
exit 1
"""


def _script(workflow: str, job: str) -> tuple[str, dict]:
    doc = yaml.safe_load((WORKFLOWS / workflow).read_text(encoding="utf-8"))
    steps = doc["jobs"][job]["steps"]
    runs = [s for s in steps if "run" in s]
    assert len(runs) == 1, f"{workflow}:{job} should have exactly one run step"
    return runs[0]["run"], runs[0].get("env", {})


def _execute(workflow: str, job: str, env_extra: dict) -> dict:
    script, step_env = _script(workflow, job)
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        bin_dir = tdp / "bin"
        bin_dir.mkdir()
        for name, body in (("gh", FAKE_GH), ("date", FAKE_DATE)):
            path = bin_dir / name
            path.write_text(body, encoding="utf-8")
            path.chmod(path.stat().st_mode | stat.S_IEXEC)
        call_log = tdp / "calls.jsonl"

        env = dict(os.environ)
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        # The step's own literal env (MAX_AGE_DAYS, CENSUS_WORKFLOW); the
        # `${{ }}` ones are supplied below as the runner would.
        env.update({k: str(v) for k, v in step_env.items() if "${{" not in str(v)})
        env.update(
            {
                "GH_CALL_LOG": str(call_log),
                "GH_TOKEN": "dummy",
                "GH_REPO": "thrillmade/thrill-skills",
                "GITHUB_SERVER_URL": "https://github.example",
                "GITHUB_REPOSITORY": "thrillmade/thrill-skills",
                "GITHUB_RUN_ID": "777",
                "FAKE_NOW": str(NOW),
            }
        )
        env.update(env_extra)
        proc = subprocess.run(
            ["bash", "-c", script], cwd=tdp, env=env, capture_output=True, text=True, timeout=30
        )
        calls = []
        if call_log.exists():
            calls = [json.loads(l) for l in call_log.read_text(encoding="utf-8").splitlines() if l.strip()]
        return {"rc": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr, "calls": calls}


def _issue_calls(out: dict) -> list[dict]:
    return [c for c in out["calls"] if c["cmd"] in ("create", "comment")]


GH_ACTIONS = {"login": "app/github-actions", "is_bot": True}
OUTSIDER = {"login": "someone-else", "is_bot": False}

# The genuine alarm issue: bot-authored AND carrying the alarm's exact title.
GENUINE = {"number": 900, "author": GH_ACTIONS, "title": TITLE}
# Another bot-authored issue (a digest, a verdict) on which a stranger has
# left the marker. It must never capture the alarm: the repo is public, and
# several such issues are open at any time.
DECOY = {"number": 284, "author": GH_ACTIONS, "title": "census 2026-W42 digest"}


def _alarm_lookups(out: dict) -> list[str]:
    return [c["search"] for c in out["calls"] if c["cmd"] == "issue list"]


# --- the alarm job, on the day ---------------------------------------------


def _alarm(existing: list | None = None) -> dict:
    return _execute(
        "skill-census.yml",
        "alarm",
        {"GH_ISSUE_LIST_JSON": json.dumps(existing or []), "CENSUS_RESULT": "failure"},
    )


def test_census_failure_files_one_issue_then_comments():
    first = _alarm()
    assert first["rc"] == 0, first["stderr"]
    [create] = _issue_calls(first)
    assert create["cmd"] == "create"
    assert create["title"] == TITLE
    assert create["label"] == LABEL
    assert MARKER in create["body"]
    assert RUN_URL in create["body"]

    second = _alarm([GENUINE])
    assert second["rc"] == 0, second["stderr"]
    [comment] = _issue_calls(second)
    assert comment["cmd"] == "comment" and comment["number"] == "900"
    assert RUN_URL in comment["body"]
    searches = [c["search"] for c in second["calls"] if c["cmd"] == "issue list"]
    assert searches and MARKER in searches[0]


def test_marker_on_an_issue_not_by_github_actions_is_ignored():
    out = _alarm([{"number": 13, "author": OUTSIDER, "title": TITLE}])
    assert out["rc"] == 0, out["stderr"]
    [call] = _issue_calls(out)
    assert call["cmd"] == "create", "an outsider's issue carrying the marker must not capture the alarm"


# --- the watchdog, when the census never ran --------------------------------


def _iso(epoch: int) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


NEWEST_URL = "https://github.example/thrillmade/thrill-skills/actions/runs/555"


def _watchdog(*, age_seconds: int | None = None, runs: list | None = None, lookup_fails=False, existing=None):
    if runs is None and age_seconds is not None:
        runs = [{"createdAt": _iso(NOW - age_seconds), "url": NEWEST_URL, "databaseId": 555}]
    return _execute(
        "census-watchdog.yml",
        "watchdog",
        {
            "GH_RUN_LIST_JSON": json.dumps(runs if runs is not None else []),
            "GH_RUN_LIST_FAILS": "1" if lookup_fails else "0",
            "GH_ISSUE_LIST_JSON": json.dumps(existing or []),
        },
    )


def _errors(out: dict) -> list[str]:
    return [l for l in out["stdout"].splitlines() if l.startswith("::error::")]


def test_watchdog_asks_for_the_newest_successful_scheduled_census():
    out = _watchdog(age_seconds=1 * DAY)
    [lookup] = [c for c in out["calls"] if c["cmd"] == "run list"]
    argv = lookup["argv"]
    assert argv[argv.index("--workflow") + 1] == "skill-census.yml"
    assert argv[argv.index("--event") + 1] == "schedule"
    assert argv[argv.index("--status") + 1] == "success"


def test_watchdog_is_silent_when_fresh():
    out = _watchdog(age_seconds=1 * DAY)
    assert out["rc"] == 0, out["stdout"] + out["stderr"]
    assert _issue_calls(out) == []
    assert not [c for c in out["calls"] if c["cmd"] == "issue list"]
    assert _errors(out) == []
    assert out["stdout"].startswith("ok "), out["stdout"]


def test_watchdog_alarms_when_newest_scheduled_success_is_over_14_days_old():
    out = _watchdog(age_seconds=15 * DAY)
    assert out["rc"] == 1, out["stdout"] + out["stderr"]
    [error] = _errors(out)
    assert "15 days old" in error
    assert "14-day" in error
    assert NEWEST_URL in error
    [create] = _issue_calls(out)
    assert create["cmd"] == "create" and create["title"] == TITLE and create["label"] == LABEL
    assert MARKER in create["body"] and RUN_URL in create["body"]


def test_watchdog_threshold_is_exactly_two_cadences():
    """14 days to the second is still fresh; one second more is stale."""
    assert _watchdog(age_seconds=14 * DAY)["rc"] == 0
    assert _watchdog(age_seconds=14 * DAY + 1)["rc"] == 1


def test_watchdog_comments_on_the_open_alarm_instead_of_refiling():
    out = _watchdog(age_seconds=20 * DAY, existing=[GENUINE])
    assert out["rc"] == 1
    [comment] = _issue_calls(out)
    assert comment["cmd"] == "comment" and comment["number"] == "900"
    assert "20 days old" in comment["body"]


def test_watchdog_alarms_on_lookup_error():
    out = _watchdog(lookup_fails=True)
    assert out["rc"] == 1
    [error] = _errors(out)
    assert "lookup" in error
    assert [c["cmd"] for c in _issue_calls(out)] == ["create"]


def test_watchdog_alarms_when_there_are_no_runs():
    out = _watchdog(runs=[])
    assert out["rc"] == 1
    [error] = _errors(out)
    assert "no successful scheduled run" in error
    assert [c["cmd"] for c in _issue_calls(out)] == ["create"]


def test_watchdog_alarms_on_an_unreadable_answer():
    out = _watchdog(runs=[{"url": NEWEST_URL}])  # no createdAt
    assert out["rc"] == 1
    assert len(_errors(out)) == 1
    assert [c["cmd"] for c in _issue_calls(out)] == ["create"]


# --- the alarm issue cannot be captured (both alarms) -----------------------


def test_alarm_job_ignores_a_bot_issue_with_another_title():
    out = _alarm([DECOY])
    assert out["rc"] == 0, out["stderr"]
    [call] = _issue_calls(out)
    assert call["cmd"] == "create", "a bot-authored issue with another title captured the alarm"


def test_alarm_job_searches_bodies_only():
    out = _alarm([GENUINE])
    [search] = _alarm_lookups(out)
    assert search.endswith(" in:body"), search
    assert "comments" not in search


def test_alarm_job_still_finds_the_genuine_issue_beside_a_decoy():
    out = _alarm([DECOY, GENUINE])
    [call] = _issue_calls(out)
    assert call == {**call, "cmd": "comment", "number": "900"}


def test_watchdog_ignores_a_bot_issue_with_another_title():
    out = _watchdog(age_seconds=20 * DAY, existing=[DECOY])
    assert out["rc"] == 1
    [call] = _issue_calls(out)
    assert call["cmd"] == "create"


def test_watchdog_ignores_an_outsider_issue_with_the_right_title():
    out = _watchdog(age_seconds=20 * DAY, existing=[{"number": 13, "author": OUTSIDER, "title": TITLE}])
    assert out["rc"] == 1
    [call] = _issue_calls(out)
    assert call["cmd"] == "create", "an outsider's issue captured the watchdog's alarm"


def test_watchdog_searches_bodies_only_and_finds_the_genuine_issue():
    out = _watchdog(age_seconds=20 * DAY, existing=[DECOY, GENUINE])
    [call] = _issue_calls(out)
    assert call["cmd"] == "comment" and call["number"] == "900"
    [search] = _alarm_lookups(out)
    assert search.endswith(" in:body") and "comments" not in search
