"""#313: the panel reads the docket of the repository it runs in.

The panel's `gh issue list -R` named this repository by a literal, the same
kind of literal whose staleness stopped the census four Mondays running. It
now comes from the run context (GITHUB_REPOSITORY), with the literal kept only
for a local run. Pinned on the `gh` command line the panel actually runs.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".github" / "scripts" / "census_panel.py"

_spec = importlib.util.spec_from_file_location("census_panel_under_test", SCRIPT)
panel = importlib.util.module_from_spec(_spec)
sys.modules["census_panel_under_test"] = panel
_spec.loader.exec_module(panel)


def _docket_argv(monkeypatch, repository: str | None) -> list[str]:
    seen: list[list[str]] = []

    def fake_run(argv, **kwargs):
        seen.append(list(argv))
        return subprocess.CompletedProcess(argv, 0, stdout="[]", stderr="")

    if repository is None:
        monkeypatch.delenv("GITHUB_REPOSITORY", raising=False)
    else:
        monkeypatch.setenv("GITHUB_REPOSITORY", repository)
    monkeypatch.setattr(panel.subprocess, "run", fake_run)
    issues, err = panel.fetch_docket()
    assert (issues, err) == ([], None)
    assert len(seen) == 1
    return seen[0]


def _repo_flag(argv: list[str]) -> str:
    return argv[argv.index("-R") + 1]


def test_docket_is_read_from_the_run_context_repository(monkeypatch):
    argv = _docket_argv(monkeypatch, "thrillmade/renamed-fixture")
    assert argv[:3] == ["gh", "issue", "list"]
    assert _repo_flag(argv) == "thrillmade/renamed-fixture"


def test_local_run_falls_back_to_the_literal(monkeypatch):
    argv = _docket_argv(monkeypatch, None)
    assert _repo_flag(argv) == "thrillmade/thrill-skills"
