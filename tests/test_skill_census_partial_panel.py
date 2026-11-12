"""#313: the LLM panel does not judge a partial census.

A census that could not read some consumers holds no evidence about them, and
the panel would read their empty records as "subscribes nothing" -- a gap or a
demotion verdict about a repository nobody looked at. So when census.json says
coverage is partial, the panel writes nothing and warns once; the File issues
step then takes the digest-only path it already has for a missing
verdicts.json.

Runs the real census_panel.py in a subprocess, then the real embedded bash of
the "File issues" step on the same directory, with fake `gh`, `date` and
`anthropic` -- no network.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PANEL = REPO_ROOT / ".github" / "scripts" / "census_panel.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "skill-census.yml"

# The panel only reads the docket; File issues lists, labels and creates.
FAKE_GH = """#!/usr/bin/env python3
import json, os, sys
argv = sys.argv[1:]
def log(r):
    with open(os.environ["GH_CALL_LOG"], "a", encoding="utf-8") as fh:
        fh.write(json.dumps(r) + "\\n")
if argv[:2] == ["label", "create"]:
    sys.exit(0)
if argv[:2] == ["issue", "list"]:
    sys.stdout.write("[]")
    sys.exit(0)
if argv[:2] == ["issue", "create"]:
    log({"cmd": "create", "title": argv[argv.index("--title") + 1]})
    print("https://github.example/thrillmade/thrill-skills/issues/500")
    sys.exit(0)
print(f"unexpected gh invocation: {argv}", file=sys.stderr)
sys.exit(1)
"""

FAKE_DATE = """#!/bin/sh
echo "2026-W47"
"""

# Stands in for the SDK so a run that gets past the gate fails at a known
# point instead of reaching the network.
FAKE_ANTHROPIC = """
class Anthropic:
    def __init__(self, *args, **kwargs):
        raise RuntimeError("fake client reached")
"""


def _census(complete: bool) -> dict:
    not_read = {} if complete else {"rezgen": "the repository does not answer under this name"}
    return {
        "cycle": "census-2026-W47",
        "generated_at": "2026-11-16T12:00:00+00:00",
        "coverage": {
            "consumers": 8,
            "read": 8 - len(not_read),
            "complete": complete,
            "not_read": not_read,
        },
        "repos": {},
        "catalog": [],
        "signals": {},
        "stale_docket": {"open_count": 0, "stale_count": 0, "stale": []},
    }


def _file_issues_script() -> str:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return next(s for s in doc["jobs"]["census"]["steps"] if s.get("id") == "file_issues")["run"]


def _run_panel_then_file(complete: bool) -> dict:
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        bin_dir = tdp / "bin"
        bin_dir.mkdir()
        for name, body in (("gh", FAKE_GH), ("date", FAKE_DATE)):
            path = bin_dir / name
            path.write_text(body, encoding="utf-8")
            path.chmod(path.stat().st_mode | stat.S_IEXEC)
        sdk_dir = tdp / "sdk"
        sdk_dir.mkdir()
        (sdk_dir / "anthropic.py").write_text(FAKE_ANTHROPIC, encoding="utf-8")
        census_dir = tdp / "census"
        census_dir.mkdir()
        (census_dir / "census.json").write_text(json.dumps(_census(complete)), encoding="utf-8")
        (census_dir / "digest.md").write_text("# Skill census digest\n\nbody\n", encoding="utf-8")
        call_log = tdp / "calls.jsonl"

        env = dict(os.environ)
        env.update(
            {
                "PATH": f"{bin_dir}:{env['PATH']}",
                "PYTHONPATH": str(sdk_dir),
                "ANTHROPIC_API_KEY": "fake-key",
                "CENSUS_DIR": str(census_dir),
                "GH_CALL_LOG": str(call_log),
                "GH_TOKEN": "dummy",
                "GH_REPO": "thrillmade/thrill-skills",
                "DRY_RUN": "false",
            }
        )
        panel = subprocess.run(
            [sys.executable, str(PANEL)], cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=60
        )
        produced = sorted(p.name for p in census_dir.iterdir())
        marker = census_dir / "panel_failed.marker"
        marker_text = marker.read_text(encoding="utf-8") if marker.exists() else ""
        if marker.exists():
            marker.unlink()  # so File issues sees the same thing either way
        filing = subprocess.run(
            ["bash", "-c", _file_issues_script()], cwd=tdp, env=env, capture_output=True, text=True, timeout=30
        )
        calls = []
        if call_log.exists():
            calls = [json.loads(l) for l in call_log.read_text(encoding="utf-8").splitlines() if l.strip()]
        return {
            "panel": panel,
            "produced": produced,
            "marker": marker_text,
            "filing": filing,
            "calls": calls,
        }


def test_partial_census_holds_back_verdicts_and_files_the_digest_alone():
    out = _run_panel_then_file(complete=False)
    panel = out["panel"]
    assert panel.returncode == 0, panel.stderr
    log = panel.stdout + panel.stderr
    warnings = [l for l in log.splitlines() if l.startswith("::warning::")]
    assert len(warnings) == 1, log
    assert "held back" in warnings[0] and "7 of 8" in warnings[0] and "partial" in warnings[0]
    assert "fake client reached" not in out["marker"], "the panel ran on a partial census"
    assert out["produced"] == ["census.json", "digest.md"], "the panel wrote something on a partial census"

    filing = out["filing"]
    assert filing.returncode == 0, filing.stderr
    assert "No verdicts.json present" in filing.stdout
    assert [c["title"] for c in out["calls"]] == ["census 2026-W47 digest"]


def test_complete_census_still_reaches_the_panel():
    """Control: the gate is conditional -- a full census goes past it to the
    (fake) model client."""
    out = _run_panel_then_file(complete=True)
    assert out["panel"].returncode == 0, out["panel"].stderr
    assert "fake client reached" in out["marker"]
    assert "held back" not in out["panel"].stdout + out["panel"].stderr
