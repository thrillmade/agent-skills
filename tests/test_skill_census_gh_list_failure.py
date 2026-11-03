"""#250: `skill-census.yml` swallows a failed `gh issue list` with no
annotation, at two sites in the "File issues" step -- the digest lookup
(`EXISTING_DIGEST`) and the prior-digest lookup (`PRIOR_DIGESTS`), both of the
shape `X=$(gh issue list ... ) || X=""`.

Neither site is dangerous -- a lookup failure can only make the step treat an
issue as ABSENT, never invent or misidentify one, so the worst case is a
duplicate digest created or a stale one left open, both self-healing on the
next successful run (#249's own reasoning for why this was not a blocker).
What #250 asks for is not a behaviour change but an annotation: the same
`::warning::` the file already prints for a missing `census_key` or an unknown
label, so a run that quietly could not check GitHub reads differently from a
run that checked and found nothing.

Executes the real embedded bash from the "File issues" step, same harness as
test_skill_census_digest_closure.py -- these are additions to that file's
`FAKE_GH`, not a reimplementation of the step's logic.
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
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "skill-census.yml"

FAKE_CYCLE_WEEK = "2026-W35"
CURRENT_DIGEST_TITLE = f"census {FAKE_CYCLE_WEEK} digest"

# Like test_skill_census_digest_closure.py's FAKE_GH, but either `gh issue
# list` call can be made to fail on command -- exit 1, nothing on stdout,
# mirroring a rate limit or a transient API error rather than a malformed
# response. `label create`/`comment`/`create`/`close` behave exactly as the
# existing harness's fake does, so a lookup failure's downstream effect (does
# it still create a digest? does it still skip closing anything?) is exercised
# through the real code path rather than asserted separately.
FAKE_GH = """#!/usr/bin/env python3
import json
import os
import sys


def fail(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)


argv = sys.argv[1:]
log_path = os.environ.get("GH_CALL_LOG")
if not log_path:
    fail("GH_CALL_LOG not set")


def log(record):
    with open(log_path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\\n")


if len(argv) >= 2 and argv[0] == "label" and argv[1] == "create":
    sys.exit(0)

if len(argv) >= 2 and argv[0] == "issue" and argv[1] == "list":
    rest = argv[2:]
    if "--search" in rest:
        if os.environ.get("GH_SEARCH_DIGEST_FAILS") == "1":
            print("HTTP 502: transient error", file=sys.stderr)
            sys.exit(1)
        sys.stdout.write(os.environ.get("GH_SEARCH_DIGEST_JSON", "[]"))
        sys.exit(0)
    if "--label" in rest:
        if os.environ.get("GH_LABEL_CENSUS_FAILS") == "1":
            print("HTTP 502: transient error", file=sys.stderr)
            sys.exit(1)
        sys.stdout.write(os.environ.get("GH_LABEL_CENSUS_JSON", "[]"))
        sys.exit(0)
    fail(f"unexpected gh issue list invocation: {rest}")

if len(argv) >= 2 and argv[0] == "issue" and argv[1] == "comment":
    num = argv[2]
    rest = argv[3:]
    body = ""
    i = 0
    while i < len(rest):
        if rest[i] == "--body-file":
            body = open(rest[i + 1], encoding="utf-8").read()
            i += 2
        elif rest[i] == "--body":
            body = rest[i + 1]
            i += 2
        else:
            i += 1
    log({"cmd": "comment", "number": num, "body": body})
    sys.exit(0)

if len(argv) >= 2 and argv[0] == "issue" and argv[1] == "create":
    rest = argv[2:]
    title = ""
    i = 0
    while i < len(rest):
        if rest[i] == "--title":
            title = rest[i + 1]
            i += 2
        elif rest[i] in ("--label", "--body-file"):
            i += 2
        else:
            i += 1
    new_num = os.environ.get("GH_NEW_ISSUE_NUM", "9999")
    log({"cmd": "create", "number": new_num, "title": title})
    print(f"https://github.com/thrillmade/agent-skills/issues/{new_num}")
    sys.exit(0)

if len(argv) >= 2 and argv[0] == "issue" and argv[1] == "close":
    num = argv[2]
    log({"cmd": "close", "number": num})
    sys.exit(0)

fail(f"unexpected gh invocation: {argv}")
"""

FAKE_DATE = """#!/bin/sh
if [ "$1" = "-u" ] && [ "$2" = "+%G-W%V" ]; then
  if [ -z "${FAKE_CYCLE_WEEK:-}" ]; then
    echo "FAKE_CYCLE_WEEK not set" >&2
    exit 1
  fi
  echo "$FAKE_CYCLE_WEEK"
  exit 0
fi
echo "unexpected date invocation: $*" >&2
exit 1
"""

# Same fixture shape as test_skill_census_digest_closure.py, trimmed to what
# these tests need: one prior digest that a working lookup WOULD close.
PRIOR_DIGESTS = [
    {"number": 177, "title": "census 2026-W31 digest", "labels": [{"name": "census"}]},
]


def _file_issues_script() -> str:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["census"]["steps"]
    step = next(s for s in steps if s.get("id") == "file_issues")
    return step["run"]


def _run_file_issues(
    *,
    search_digest_fails: bool = False,
    label_census_fails: bool = False,
    search_digest_json: list | None = None,
    label_census_json: list | None = None,
    new_issue_num: str = "500",
) -> dict:
    script = _file_issues_script()

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)

        bin_dir = tdp / "bin"
        bin_dir.mkdir()
        fake_gh = bin_dir / "gh"
        fake_gh.write_text(FAKE_GH, encoding="utf-8")
        fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IEXEC)
        fake_date = bin_dir / "date"
        fake_date.write_text(FAKE_DATE, encoding="utf-8")
        fake_date.chmod(fake_date.stat().st_mode | stat.S_IEXEC)

        census_dir = tdp / "census"
        census_dir.mkdir()
        (census_dir / "digest.md").write_text(
            "# Skill census digest\n\nbody\n", encoding="utf-8"
        )

        call_log = tdp / "gh_calls.jsonl"

        env = dict(os.environ)
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        env["FAKE_CYCLE_WEEK"] = FAKE_CYCLE_WEEK
        env["GH_CALL_LOG"] = str(call_log)
        env["GH_SEARCH_DIGEST_JSON"] = json.dumps(search_digest_json or [])
        env["GH_LABEL_CENSUS_JSON"] = json.dumps(label_census_json or [])
        env["GH_SEARCH_DIGEST_FAILS"] = "1" if search_digest_fails else "0"
        env["GH_LABEL_CENSUS_FAILS"] = "1" if label_census_fails else "0"
        env["GH_NEW_ISSUE_NUM"] = new_issue_num
        env["GH_TOKEN"] = "dummy-token"
        env["GH_REPO"] = "thrillmade/agent-skills"
        env["CENSUS_DIR"] = str(census_dir)
        env["DRY_RUN"] = "false"

        proc = subprocess.run(
            ["bash", "-c", script],
            cwd=tdp,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )

        calls = []
        if call_log.exists():
            for line in call_log.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    calls.append(json.loads(line))

        return {"stdout": proc.stdout, "stderr": proc.stderr, "calls": calls, "returncode": proc.returncode}


def test_digest_lookup_failure_fails_safe_and_warns():
    """A failed digest lookup must not fail the step (it fails safe -- worst
    case is a duplicate digest, not a wrong close) but MUST print a
    `::warning::` naming what could not be checked.
    """
    out = _run_file_issues(search_digest_fails=True, label_census_json=[])
    assert out["returncode"] == 0, (
        f"a gh issue list failure must not fail the step -- it fails safe\n"
        f"stdout: {out['stdout']}\nstderr: {out['stderr']}"
    )
    assert "::warning::" in out["stdout"]
    assert "digest" in out["stdout"].lower()
    # Treated as absent: the step falls through to CREATE rather than comment.
    creates = [c for c in out["calls"] if c["cmd"] == "create"]
    assert creates == [{"cmd": "create", "number": "500", "title": CURRENT_DIGEST_TITLE}]


def test_prior_digest_lookup_failure_fails_safe_and_warns():
    """Same shape, the other site: a failed prior-digest lookup must not fail
    the step, must warn, and must close nothing (treated as none, not as
    "close everything" or a crash).
    """
    out = _run_file_issues(
        label_census_fails=True,
        search_digest_json=[],
        label_census_json=PRIOR_DIGESTS,  # ignored -- the fake fails before reading this
    )
    assert out["returncode"] == 0, (
        f"a gh issue list failure must not fail the step -- it fails safe\n"
        f"stdout: {out['stdout']}\nstderr: {out['stderr']}"
    )
    assert "::warning::" in out["stdout"]
    assert "prior" in out["stdout"].lower()
    closed = {c["number"] for c in out["calls"] if c["cmd"] == "close"}
    assert closed == set(), "a failed lookup must not be read as \"close everything\""


def test_a_successful_run_prints_no_warning_for_either_site():
    """Control: the two new `::warning::`s are conditional on failure, not
    printed on every run -- otherwise they are noise, not a signal.
    """
    out = _run_file_issues(search_digest_json=[], label_census_json=PRIOR_DIGESTS)
    assert out["returncode"] == 0
    assert "::warning::" not in out["stdout"], out["stdout"]
