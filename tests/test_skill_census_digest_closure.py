"""The skill-census `File issues` step must close prior digest issues.

#249: `skill-census.yml` files a fresh "census <ISO-week> digest" issue every
Monday and closes nothing. A weekly snapshot is superseded by construction
the moment the next one ships, so four digests (W31-W34) sat open at once
with only the newest current — an issue tracker nobody prunes trains
everyone to ignore it, which is what hides the real [gap]/[placement]/
[revise] verdict issues the same step files alongside it.

These tests execute the actual embedded bash from the "File issues (digest +
verdicts)" step (not a reimplementation of it), so they track the workflow
file directly and fail if a hand-edit reintroduces the silent leak or widens
the close to something the census did not file.

Scope is the load-bearing part: a digest issue carries the `census` label
and NO OTHER census-scheme label (a verdict always adds one of gap /
placement / revise / promotion-candidate / demotion-candidate on top of
census), and its title is the exact "census <ISO-week> digest" string this
workflow itself generates. Both signals are required together — see the
close-prior-digests comment in skill-census.yml for why neither alone is
safe.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "skill-census.yml"

FAKE_CYCLE_WEEK = "2026-W35"
CURRENT_DIGEST_TITLE = f"census {FAKE_CYCLE_WEEK} digest"

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
        sys.stdout.write(os.environ.get("GH_SEARCH_DIGEST_JSON", "[]"))
        sys.exit(0)
    if "--label" in rest:
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


def _file_issues_script() -> str:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["census"]["steps"]
    step = next(s for s in steps if s.get("id") == "file_issues")
    return step["run"]


# Realistic-shaped fixtures, matching the exact numbering this repo's real
# backlog had at the time #249 was filed (issues 177/184/185/186/190/191).
PRIOR_DIGESTS = [
    {"number": 177, "title": "census 2026-W31 digest", "labels": [{"name": "census"}]},
    {"number": 184, "title": "census 2026-W32 digest", "labels": [{"name": "census"}]},
    {"number": 190, "title": "census 2026-W33 digest", "labels": [{"name": "census"}]},
]

VERDICT_ISSUES = [
    {
        "number": 185,
        "title": "[placement] census-2026-W32: placement: ...",
        "labels": [{"name": "census"}, {"name": "placement"}],
    },
    {
        "number": 186,
        "title": "[gap] census-2026-W32: revise: ...",
        "labels": [{"name": "census"}, {"name": "gap"}],
    },
    {
        "number": 191,
        "title": "[revise] census-2026-W33: revise: ...",
        "labels": [{"name": "census"}, {"name": "revise"}],
    },
]

# Edge cases the scope guard must reject even though a naive check would not:
EDGE_CASES = [
    # A verdict-shaped title carrying the exact digest title, but with a
    # SECOND label riding along census (verdicts always add one) — the
    # labels-length==1 half of the guard must reject this on its own.
    {
        "number": 998,
        "title": "census 2024-W01 digest",
        "labels": [{"name": "census"}, {"name": "gap"}],
    },
    # A single "census" label (e.g. a verdict whose declared label fell
    # through the allow-list, or a human hand-labelling some other issue
    # "census") whose title does NOT match the digest format — the
    # title-regex half of the guard must reject this on its own.
    {"number": 999, "title": "gap: some odd verdict title", "labels": [{"name": "census"}]},
    # Same single-label shape, but the title merely CONTAINS "digest" as a
    # substring rather than matching the exact "census <ISO-week> digest"
    # format — the human-authored issue the brief specifically warns a
    # title-substring match would misfire on. Catches a regex that drops
    # its anchors even though the labels-length clause alone would not.
    {
        "number": 997,
        "title": "the census digest generator double-counts untracked skills",
        "labels": [{"name": "census"}],
    },
]


def _run_file_issues(
    *,
    dry_run: bool,
    search_digest_json: list,
    label_census_json: list,
    new_issue_num: str = "500",
    digest_body: str = "# Skill census digest\n\nbody\n",
) -> dict:
    """Execute the real 'File issues (digest + verdicts)' run: block.

    Stubs `gh` (records every comment/create/close call to a JSON-lines log)
    and `date -u +%G-W%V` (pins the cycle so the digest title is
    deterministic), exactly as the real step invokes both. No
    `verdicts.json` is written, so the run takes the Mode-B (digest-only)
    exit — the verdict-filing loop below the digest-close logic under test
    never executes, keeping these tests scoped to the digest-close guard.
    """
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
        (census_dir / "digest.md").write_text(digest_body, encoding="utf-8")

        call_log = tdp / "gh_calls.jsonl"

        env = dict(os.environ)
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        env["FAKE_CYCLE_WEEK"] = FAKE_CYCLE_WEEK
        env["GH_CALL_LOG"] = str(call_log)
        env["GH_SEARCH_DIGEST_JSON"] = json.dumps(search_digest_json)
        env["GH_LABEL_CENSUS_JSON"] = json.dumps(label_census_json)
        env["GH_NEW_ISSUE_NUM"] = new_issue_num
        env["GH_TOKEN"] = "dummy-token"
        env["GH_REPO"] = "thrillmade/agent-skills"
        env["CENSUS_DIR"] = str(census_dir)
        env["DRY_RUN"] = "true" if dry_run else "false"

        proc = subprocess.run(
            ["bash", "-c", script],
            cwd=tdp,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert proc.returncode == 0, (
            f"file_issues step exited {proc.returncode}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )

        calls = []
        if call_log.exists():
            for line in call_log.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    calls.append(json.loads(line))

        return {"stdout": proc.stdout, "stderr": proc.stderr, "calls": calls}


def _closed_numbers(calls: list) -> set:
    # gh's real argv is all strings; normalize to int so callers can compare
    # against plain issue numbers regardless of how the fake logged them.
    return {int(c["number"]) for c in calls if c["cmd"] == "close"}


# Control: with nothing filed yet under the current cycle's title, and no
# prior digests open at all, the close block must be a genuine no-op — if
# this ever closes something, "closes nothing extra" is not being measured.
def test_no_prior_digests_closes_nothing():
    out = _run_file_issues(
        dry_run=False,
        search_digest_json=[],
        label_census_json=VERDICT_ISSUES + EDGE_CASES,
    )
    assert _closed_numbers(out["calls"]) == set()
    creates = [c for c in out["calls"] if c["cmd"] == "create"]
    assert creates == [{"cmd": "create", "number": "500", "title": CURRENT_DIGEST_TITLE}]


def test_prior_digests_are_closed_with_a_forward_link():
    out = _run_file_issues(
        dry_run=False,
        search_digest_json=[],
        label_census_json=PRIOR_DIGESTS + VERDICT_ISSUES + EDGE_CASES,
        new_issue_num="500",
    )
    assert _closed_numbers(out["calls"]) == {177, 184, 190}

    comments_by_number = {
        int(c["number"]): c["body"] for c in out["calls"] if c["cmd"] == "comment"
    }
    for prior in (177, 184, 190):
        body = comments_by_number.get(prior)
        assert body is not None, f"prior digest #{prior} was closed without a comment"
        assert "#500" in body, f"comment on #{prior} does not link forward to #500: {body!r}"
        assert "Superseded" in body


def test_verdict_and_edge_case_issues_are_never_closed():
    """The scope guard: a verdict (always carries a second label) and the
    two adversarial edge cases (digest-shaped title + extra label; single
    census label + non-digest title) must all survive.
    """
    out = _run_file_issues(
        dry_run=False,
        search_digest_json=[],
        label_census_json=PRIOR_DIGESTS + VERDICT_ISSUES + EDGE_CASES,
    )
    closed = _closed_numbers(out["calls"])
    for untouchable in (185, 186, 191, 998, 999, 997):
        assert untouchable not in closed, f"issue #{untouchable} was closed but must not be"


def test_rerun_same_cycle_is_idempotent():
    """A re-run after prior digests are already closed (so `--state open`
    would no longer surface them) and the current cycle's digest already
    exists must neither re-close anything nor re-create the digest, and must
    not close the digest it just updated.
    """
    out = _run_file_issues(
        dry_run=False,
        search_digest_json=[{"number": 500, "title": CURRENT_DIGEST_TITLE}],
        label_census_json=[
            {"number": 500, "title": CURRENT_DIGEST_TITLE, "labels": [{"name": "census"}]}
        ]
        + VERDICT_ISSUES,
    )
    assert _closed_numbers(out["calls"]) == set()
    creates = [c for c in out["calls"] if c["cmd"] == "create"]
    assert creates == [], "a re-run under the same cycle title must not create a second digest"
    # It still updates the existing digest via comment (existing behaviour).
    updates = [c for c in out["calls"] if c["cmd"] == "comment" and int(c["number"]) == 500]
    assert len(updates) == 1


def test_dry_run_prints_and_files_nothing():
    out = _run_file_issues(
        dry_run=True,
        search_digest_json=[],
        label_census_json=PRIOR_DIGESTS + VERDICT_ISSUES + EDGE_CASES,
    )
    # Dry run must honour the same guard as the real filing path: no gh
    # mutation (comment/create/close) call is ever made.
    assert out["calls"] == []
    for prior in (177, 184, 190):
        assert f"#{prior}" in out["stdout"], (
            f"dry run did not print the would-be close of prior digest #{prior}:\n{out['stdout']}"
        )
    assert "DRY-RUN" in out["stdout"]
