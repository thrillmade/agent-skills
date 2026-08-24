"""The `File issues` step must fail loudly, not silently skip, when the
minted App token cannot actually write to this repo.

#183: `skill-census.yml` used to file under `github.token` because the App
token's `repositories:` scope omitted `agent-skills`. The fix flips both
`GH_TOKEN` lines to the App token now that `agent-skills` is in scope. That
flip introduces a new way for the token handed to `gh` to be wrong (mint
succeeds but the resulting token still can't write here — repo dropped from
the list again, installation permission revoked, etc.). The brief for that
fix names the failure mode to avoid: "the census silently filing nothing."

This test does not exercise the workflow's token-minting step (that needs a
live App installation — see the fix's report for what remains unverified
until the next scheduled run). It proves the narrower, fully-local claim:
given a `gh` that behaves the way GitHub's API behaves when a token cannot
write to a repo (`issue create`/`issue comment` exit non-zero), the file_issues
step's OWN script — unchanged by the token flip, since the flip only touches
`env:` — exits non-zero rather than exiting 0 having filed nothing. It does
so via `set -euo pipefail` plus the primary create/comment calls being
unguarded (no `|| ...` swallowing a non-zero exit), NOT via a new guard this
fix adds — so there is nothing here to mutation-test per the fix's own
verification bar.

Executes the real embedded bash from the "File issues" step, same as
test_skill_census_digest_closure.py, rather than reimplementing its logic.
"""

from __future__ import annotations

import os
import stat
import subprocess
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "skill-census.yml"

FAKE_CYCLE_WEEK = "2026-W35"

# A `gh` that answers exactly like GitHub's API does when the caller's token
# cannot write to this repo: reads (`issue list`) still succeed — listing is
# permitted more broadly than writing — but every mutating call (`issue
# create`, `issue comment`) exits 1 with a 403-shaped message on stderr, the
# same shape a scope-dropped or permission-revoked App token would produce.
FAKE_GH_BAD_TOKEN = """#!/usr/bin/env python3
import sys

argv = sys.argv[1:]

if len(argv) >= 2 and argv[0] == "label" and argv[1] == "create":
    sys.exit(0)

if len(argv) >= 2 and argv[0] == "issue" and argv[1] == "list":
    # No existing digest, no prior digests open — forces the create path.
    sys.stdout.write("[]")
    sys.exit(0)

if len(argv) >= 2 and argv[0] == "issue" and argv[1] in ("create", "comment"):
    print(
        "HTTP 403: Resource not accessible by integration "
        "(https://api.github.com/repos/thrillmade/agent-skills/issues)",
        file=sys.stderr,
    )
    sys.exit(1)

print(f"unexpected gh invocation: {argv}", file=sys.stderr)
sys.exit(1)
"""

FAKE_DATE = """#!/bin/sh
if [ "$1" = "-u" ] && [ "$2" = "+%G-W%V" ]; then
  echo "__WEEK__"
  exit 0
fi
echo "unexpected date invocation: $*" >&2
exit 1
""".replace("__WEEK__", FAKE_CYCLE_WEEK)


def _file_issues_script() -> str:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["census"]["steps"]
    step = next(s for s in steps if s.get("id") == "file_issues")
    return step["run"]


def _run_with_bad_token(*, dry_run: bool) -> subprocess.CompletedProcess:
    script = _file_issues_script()

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)

        bin_dir = tdp / "bin"
        bin_dir.mkdir()
        fake_gh = bin_dir / "gh"
        fake_gh.write_text(FAKE_GH_BAD_TOKEN, encoding="utf-8")
        fake_gh.chmod(fake_gh.stat().st_mode | stat.S_IEXEC)
        fake_date = bin_dir / "date"
        fake_date.write_text(FAKE_DATE, encoding="utf-8")
        fake_date.chmod(fake_date.stat().st_mode | stat.S_IEXEC)

        census_dir = tdp / "census"
        census_dir.mkdir()
        (census_dir / "digest.md").write_text("# Skill census digest\n\nbody\n", encoding="utf-8")

        env = dict(os.environ)
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        # Empty string models the shape the brief calls out: the mint step
        # "succeeded" (no non-zero exit to fail the job outright) but the
        # token it produced does not work.
        env["GH_TOKEN"] = ""
        env["GH_REPO"] = "thrillmade/agent-skills"
        env["CENSUS_DIR"] = str(census_dir)
        env["DRY_RUN"] = "true" if dry_run else "false"

        return subprocess.run(
            ["bash", "-c", script],
            cwd=tdp,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )


def test_bad_token_fails_loud_not_silent():
    """The real (non-dry-run) path: a token that cannot write must make the
    step — and therefore the job — fail, not exit 0 having filed nothing.
    """
    proc = _run_with_bad_token(dry_run=False)
    assert proc.returncode != 0, (
        "file_issues step exited 0 with a token that cannot write — this is "
        f"exactly the silent-filing-nothing failure mode the fix must avoid.\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
    assert "403" in proc.stderr or "not accessible" in proc.stderr, (
        f"expected the 403 from the failed gh call to reach the step's own "
        f"stderr (not be swallowed): {proc.stderr}"
    )


# Control: dry_run's whole point is to print instead of calling `gh issue
# create`/`comment`, so a bad token is invisible in that mode by design — it
# never reaches a mutating call. This is not the silent-filing-nothing
# failure mode (nothing is filed either way, on request), but it does mean
# dry_run cannot be used to pre-flight token health. Asserting it here keeps
# that a documented, tested boundary rather than an implicit one — if this
# ever starts failing, dry_run has started exercising real calls and the
# claim above needs re-checking.
def test_dry_run_does_not_surface_a_bad_token():
    proc = _run_with_bad_token(dry_run=True)
    assert proc.returncode == 0, (
        f"dry_run started failing on a bad token — re-check the claim in "
        f"test_bad_token_fails_loud_not_silent's docstring boundary.\n"
        f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
