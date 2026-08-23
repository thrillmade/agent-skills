"""The `Clud Bug Self-Update` compare step must not attempt a downgrade.

#192: the scheduled workflow failed every week from 2026-08-10 onward. The
proximate error was a `git push` rejection (a stale branch left on the
remote by a closed, unmerged PR), but the actual defect is upstream of
that: the "Compare installed vs npm latest" step treats any inequality
between the installed version and npm's `latest` dist-tag as "needs an
update", with no notion of version *direction*.

This repo's `.claude/skills/.clud-bug.json` records `lastUpdateVersion:
"0.7.0-rc.20"` (a 0.7.x prerelease). npm's `latest` tag is `0.6.34` — an
older release line. `0.6.34 != 0.7.0-rc.20`, so the naive check fires,
generates a downgrade PR (#187, closed by the CEO specifically because it
was a downgrade), and — every week since, because npm's `latest` tag does
not move — regenerates the exact same branch name and collides with the
undeleted remnant of that closed PR.

These tests execute the actual embedded bash from the step (not a
reimplementation of it), so they track the workflow file directly and
fail if a hand-edit reintroduces the naive `!=` check.
"""

import os
import stat
import subprocess
import tempfile
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "clud-bug-self-update.yml"


def _compare_step_script() -> str:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    steps = doc["jobs"]["check"]["steps"]
    step = next(s for s in steps if s.get("id") == "compare")
    return step["run"]


def _run_compare(installed: str, latest: str, pin: str = "") -> dict:
    """Execute the real 'Compare installed vs npm latest' run: block.

    Stubs `npm view clud-bug version` (via a fake `npm` on PATH) and the
    manifest file it reads, exactly as the real step reads both, then
    parses the GITHUB_OUTPUT file the step writes.
    """
    script = _compare_step_script()

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)

        manifest = tdp / ".clud-bug.json"
        fields = [f'"lastUpdateVersion": "{installed}"']
        if pin:
            fields.append(f'"pinVersion": "{pin}"')
        manifest.write_text("{" + ", ".join(fields) + "}", encoding="utf-8")

        # Fake `npm` that answers `npm view clud-bug version` with $LATEST,
        # same as the real step invokes it.
        bin_dir = tdp / "bin"
        bin_dir.mkdir()
        fake_npm = bin_dir / "npm"
        fake_npm.write_text(
            "#!/bin/sh\n"
            f'if [ "$1" = "view" ] && [ "$2" = "clud-bug" ] && [ "$3" = "version" ]; then\n'
            f'  echo "{latest}"\n'
            "  exit 0\n"
            "fi\n"
            'echo "unexpected npm invocation: $*" >&2\n'
            "exit 1\n",
            encoding="utf-8",
        )
        fake_npm.chmod(fake_npm.stat().st_mode | stat.S_IEXEC)

        github_output = tdp / "github_output"
        github_output.write_text("", encoding="utf-8")

        # The real step hardcodes MANIFEST=".claude/skills/.clud-bug.json"
        # relative to the checkout root — run with that cwd layout.
        cwd = tdp / "repo"
        (cwd / ".claude" / "skills").mkdir(parents=True)
        (cwd / ".claude" / "skills" / ".clud-bug.json").write_text(
            manifest.read_text(encoding="utf-8"), encoding="utf-8"
        )

        env = dict(os.environ)
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
        env["GITHUB_OUTPUT"] = str(github_output)

        proc = subprocess.run(
            ["bash", "-c", script],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert proc.returncode == 0, (
            f"compare step exited {proc.returncode}\n"
            f"stdout: {proc.stdout}\nstderr: {proc.stderr}"
        )

        out = {}
        for line in github_output.read_text(encoding="utf-8").splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                out[k] = v
        return out


# Control: a genuine forward upgrade must NOT be skipped. If this ever
# reports skip=true, the "absence of a downgrade" is not distinguishing
# anything — it would mean skip=true unconditionally.
def test_genuine_upgrade_is_not_skipped():
    out = _run_compare(installed="0.6.30", latest="0.6.34")
    assert out.get("skip") == "false", (
        f"a genuine upgrade (0.6.30 -> 0.6.34) must proceed, got {out}"
    )


def test_exact_match_is_skipped():
    out = _run_compare(installed="0.6.34", latest="0.6.34")
    assert out.get("skip") == "true"


def test_pin_is_skipped():
    out = _run_compare(installed="0.6.30", latest="0.6.34", pin="0.6.30")
    assert out.get("skip") == "true"


def test_downgrade_from_prerelease_is_skipped():
    """#192's actual failure mode: installed is a 0.7.x prerelease, npm's
    `latest` tag is still 0.6.34. This is not an update — it is the exact
    downgrade the CEO rejected in #187 — and must not be attempted again.
    """
    out = _run_compare(installed="0.7.0-rc.20", latest="0.6.34")
    assert out.get("skip") == "true", (
        "compare step attempted a downgrade (0.7.0-rc.20 -> 0.6.34) instead "
        f"of skipping it: {out}"
    )
