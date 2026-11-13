"""The census panel: what it records, what the digest says, when the run fails.

#313: the LLM panel does not judge a partial census. A census that could not
read some consumers holds no evidence about them, and the panel would read
their empty records as "subscribes nothing" -- a gap or a demotion verdict
about a repository nobody looked at. So when census.json says coverage is
partial, the panel writes no verdicts and warns once; the File issues step
then takes the digest-only path it already has for a missing verdicts.json.

The panel failed authentication on every run for weeks while the run stayed
green and the digest said nothing. So now the panel leaves panel_status.json
on every handled path, the digest opens with one line saying what the panel
did, and a failure that needs a person, or a missing record, fails the run in
the last step ("Panel health"), after the digest is filed. Failures are classified from the HTTP
status and the exception's class name only: the provider's error text carries
a request id and this repository's Actions logs are public.

Runs the real embedded bash of the panel step (which sends the script's streams
to /dev/null and checks the record), then of the "File issues" and "Panel
health" steps on the same directory, with fake `gh`, `date` and `anthropic` --
no network. The panel step prints nothing: what the log may carry is pinned in
test_skill_census_panel_boundary.py.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PANEL = REPO_ROOT / ".github" / "scripts" / "census_panel.py"
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "skill-census.yml"

FAKE_REQUEST_ID = "req_FAKEID0123456789"
FAKE_KEY = "sk-ant-FAKEKEY-abcdef"

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
    body = open(argv[argv.index("--body-file") + 1], encoding="utf-8").read()
    log({"cmd": "create", "title": argv[argv.index("--title") + 1], "body": body})
    print("https://github.example/thrillmade/thrill-skills/issues/500")
    sys.exit(0)
print(f"unexpected gh invocation: {argv}", file=sys.stderr)
sys.exit(1)
"""

FAKE_DATE = """#!/bin/sh
echo "2026-W47"
"""

# Stands in for the SDK so a run that gets past the gate fails at a known
# point instead of reaching the network. FAKE_MODE picks the failure; the
# provider-style errors carry a request id and the key in their TEXT, which
# the panel must never print or write.
FAKE_ANTHROPIC = """
import os

class AuthenticationError(Exception):
    status_code = 401

class RateLimitError(Exception):
    status_code = 429

class BadRequestError(Exception):
    status_code = 400

class APITimeoutError(Exception):
    pass

class FakeBaseFailure(BaseException):
    pass

class Anthropic:
    def __init__(self, *args, **kwargs):
        mode = os.environ.get("FAKE_MODE", "")
        text = "Error code: 4xx - {'message': 'invalid x-api-key', 'request_id': '" + os.environ["FAKE_REQUEST_ID"] + "', 'key': '" + os.environ["ANTHROPIC_API_KEY"] + "'}"
        if mode == "custombase":
            raise FakeBaseFailure(text)
        if mode == "sysexit":
            raise SystemExit(text)
        if mode == "genexit":
            raise GeneratorExit(text)
        if mode == "sysexitcode":
            raise SystemExit(3)
        if mode == "auth":
            raise AuthenticationError(text)
        if mode == "ratelimit":
            raise RateLimitError(text)
        if mode == "timeout":
            raise APITimeoutError(text)
        if mode == "badrequest":
            raise BadRequestError(text)
        if mode == "valueerror":
            raise ValueError(text)
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


def _step_script(step_id: str) -> str:
    doc = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return next(s for s in doc["jobs"]["census"]["steps"] if s.get("id") == step_id)["run"]


def _install_checker(workspace: Path) -> None:
    """The File issues and Panel health steps run from the workspace root; give
    a scratch workspace the record checker they call."""
    (workspace / ".github" / "scripts").mkdir(parents=True, exist_ok=True)
    shutil.copy(REPO_ROOT / ".github" / "scripts" / "panel_record.sh", workspace / ".github" / "scripts")


def _run_panel_then_file(complete: bool = True, mode: str = "", panel_enabled: bool = True, key: str = FAKE_KEY) -> dict:
    """The panel, then File issues, then Panel health, on one directory. With
    panel_enabled False the panel step is skipped, as the guard step would."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        bin_dir = tdp / "bin"
        bin_dir.mkdir()
        for name, body in (("gh", FAKE_GH), ("date", FAKE_DATE)):
            path = bin_dir / name
            path.write_text(body, encoding="utf-8")
            path.chmod(path.stat().st_mode | stat.S_IEXEC)
        (bin_dir / "python3").symlink_to(sys.executable)
        # The steps run from the workspace root; File issues and Panel health
        # run from this scratch directory, so the record checker goes there too.
        _install_checker(tdp)
        sdk_dir = tdp / "sdk"
        sdk_dir.mkdir()
        (sdk_dir / "anthropic.py").write_text(FAKE_ANTHROPIC, encoding="utf-8")
        census_dir = tdp / "census"
        census_dir.mkdir()
        (census_dir / "census.json").write_text(json.dumps(_census(complete)), encoding="utf-8")
        (census_dir / "digest.md").write_text("# Skill census digest\n\nbody\n", encoding="utf-8")
        call_log = tdp / "calls.jsonl"
        summary = tdp / "summary.md"

        env = dict(os.environ)
        env.update(
            {
                "PATH": f"{bin_dir}:{env['PATH']}",
                "PYTHONPATH": str(sdk_dir),
                "ANTHROPIC_API_KEY": key,
                "CENSUS_DIR": str(census_dir),
                "GH_CALL_LOG": str(call_log),
                "GH_TOKEN": "dummy",
                "GH_REPO": "thrillmade/thrill-skills",
                "DRY_RUN": "false",
                "FAKE_MODE": mode,
                "FAKE_REQUEST_ID": FAKE_REQUEST_ID,
                "GITHUB_STEP_SUMMARY": str(summary),
                "PANEL_ENABLED": "true" if panel_enabled else "false",
                "PANEL_OUTCOME": "success" if panel_enabled else "skipped",
            }
        )
        if panel_enabled:
            panel = subprocess.run(
                ["bash", "-c", _step_script("panel")], cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=60
            )
        else:
            panel = subprocess.CompletedProcess([], 0, "", "")
        produced = sorted(p.name for p in census_dir.iterdir())
        status_path = census_dir / "panel_status.json"
        status_text = status_path.read_text(encoding="utf-8") if status_path.exists() else ""
        filing = subprocess.run(
            ["bash", "-c", _step_script("file_issues")], cwd=tdp, env=env, capture_output=True, text=True, timeout=30
        )
        health = subprocess.run(
            ["bash", "-c", _step_script("panel_health")], cwd=tdp, env=env, capture_output=True, text=True, timeout=30
        )
        calls = []
        if call_log.exists():
            calls = [json.loads(l) for l in call_log.read_text(encoding="utf-8").splitlines() if l.strip()]
        everything = "\n".join(
            [panel.stdout, panel.stderr, status_text, filing.stdout, filing.stderr, health.stdout, health.stderr]
            + [json.dumps(c) for c in calls]
            + [(census_dir / n).read_text(encoding="utf-8") for n in produced]
            + [summary.read_text(encoding="utf-8") if summary.exists() else ""]
        )
        return {
            "panel": panel,
            "produced": produced,
            "status": json.loads(status_text) if status_text else None,
            "filing": filing,
            "health": health,
            "calls": calls,
            "body": next((c["body"] for c in calls if c["cmd"] == "create"), ""),
            "summary": summary.read_text(encoding="utf-8") if summary.exists() else "",
            "everything": everything,
        }


def _panel_line(out: dict) -> str:
    """The one line under the digest's title."""
    lines = out["body"].splitlines()
    assert lines[0] == "# Skill census digest", lines[:3]
    assert lines[1] == "" and lines[2].startswith("> **Panel"), lines[:4]
    return lines[2]


# --- held back: a partial census ---------------------------------------------


def test_partial_census_holds_back_verdicts_and_files_the_digest_alone():
    out = _run_panel_then_file(complete=False)
    panel = out["panel"]
    assert panel.returncode == 0, panel.stderr
    assert (panel.stdout, panel.stderr) == ("", ""), "the panel step must print nothing"
    assert out["status"]["state"] == "held_back" and out["status"]["reason_code"] == "partial_census" and out["status"]["verdicts"] == 0
    assert out["produced"] == ["census.json", "digest.md", "panel_status.json"], (
        "the panel wrote something else on a partial census"
    )

    filing = out["filing"]
    assert filing.returncode == 0, filing.stderr
    assert "No verdicts.json present" in filing.stdout
    assert [c["title"] for c in out["calls"]] == ["census 2026-W47 digest"]
    assert _panel_line(out) == (
        "> **Panel:** held back: the census is partial, so there are no verdicts about "
        "repositories it did not read."
    )
    assert out["health"].returncode == 0, out["health"].stdout + out["health"].stderr


def test_complete_census_still_reaches_the_panel():
    """Control: the gate is conditional -- a full census goes past it to the
    (fake) model client, whose stand-in error is unclassified."""
    out = _run_panel_then_file(complete=True)
    assert out["panel"].returncode == 0, out["panel"].stderr
    assert out["status"]["state"] == "failed" and out["status"]["reason_code"] == "unexpected"
    assert out["status"]["reason"] == "an unexpected exception was raised"
    assert out["status"]["exc_class"] == "RuntimeError" and out["status"]["stage"] == "client"
    assert "fake client reached" not in out["everything"], "exception text reached an output"


# --- failed: authentication --------------------------------------------------


def test_authentication_failure_is_named_in_the_digest_and_fails_the_run():
    out = _run_panel_then_file(mode="auth")
    panel = out["panel"]
    assert panel.returncode == 0, "the panel exits 0 so the digest still files"
    assert (panel.stdout, panel.stderr) == ("", ""), "the panel step must print nothing"
    assert out["status"] == {
        "state": "failed",
        "reason_code": "authentication",
        "reason": "the API key was refused (HTTP 401)",
        "stage": "client",
        "exc_class": "AuthenticationError",
        "background_error_class": None,
        "http_status": 401,
        "exit_status": None,
        "verdicts": 0,
        "keeps": 0,
    }
    assert _panel_line(out) == (
        "> **Panel did not run this cycle:** the API key was refused (HTTP 401). "
        "This digest carries no verdicts."
    )
    assert "panel=failed:authentication did not run: the API key was refused (HTTP 401)." in out["summary"]
    # The digest filed first; then Panel health fails the run.
    assert [c["title"] for c in out["calls"]] == ["census 2026-W47 digest"]
    health = out["health"]
    assert health.returncode == 1, health.stdout + health.stderr
    assert "::error::census panel needs attention: state=failed reason=the API key was refused (HTTP 401) code=authentication stage=client http=401 class=AuthenticationError." in health.stdout


def test_nothing_raised_prints_its_text_even_when_it_is_not_an_exception():
    """BaseException subclasses (a custom one, SystemExit and GeneratorExit
    carrying a message) skip `except Exception`. The panel, run as the workflow
    runs it, must still print the class name only, write the record, and exit
    non-zero."""
    header_dump = "headers={'x-api-key': 'sk-ant-FAKEKEY-abcdef', 'authorization': 'Bearer sk-ant-FAKEKEY-abcdef'}"
    for mode, cls in (("custombase", "unrecognised"), ("sysexit", "SystemExit"), ("genexit", "GeneratorExit")):
        out = _run_panel_then_file(mode=mode)
        panel = out["panel"]
        assert panel.returncode != 0, (mode, panel.returncode)
        assert (panel.stdout, panel.stderr) == ("", ""), mode
        for secret in (FAKE_REQUEST_ID, "req_", FAKE_KEY, "sk-ant", "invalid x-api-key", "Error code", header_dump, "Traceback"):
            assert secret not in out["everything"], f"{secret!r} leaked in mode {mode!r}"
        assert out["status"] is not None, mode
        assert out["status"]["state"] == "failed" and out["status"]["exc_class"] == cls, (mode, out["status"])
        assert out["health"].returncode == 1, mode


def test_a_deliberate_system_exit_code_is_kept_and_still_recorded():
    out = _run_panel_then_file(mode="sysexitcode")
    assert out["panel"].returncode == 3
    assert out["status"]["state"] == "failed" and out["status"]["exc_class"] == "SystemExit"


def test_no_request_id_or_key_reaches_any_log_artifact_issue_or_summary():
    for mode in ("auth", "ratelimit", "timeout", "badrequest", "valueerror", ""):
        out = _run_panel_then_file(mode=mode)
        for secret in (FAKE_REQUEST_ID, "req_", FAKE_KEY, "sk-ant", "invalid x-api-key", "Error code"):
            assert secret not in out["everything"], f"{secret!r} leaked in mode {mode!r}"


# --- failed: transient -------------------------------------------------------


def test_rate_limit_stays_green_and_the_digest_says_so():
    out = _run_panel_then_file(mode="ratelimit")
    assert out["status"]["reason_code"] == "rate_limited" and out["status"]["http_status"] == 429
    assert _panel_line(out) == (
        "> **Panel did not run this cycle:** the API rate limit was hit (HTTP 429). "
        "This digest carries no verdicts."
    )
    health = out["health"]
    assert health.returncode == 0, health.stdout + health.stderr
    assert "::error::" not in health.stdout


def test_timeout_stays_green_and_is_named():
    out = _run_panel_then_file(mode="timeout")
    assert out["status"]["reason_code"] == "timeout"
    assert _panel_line(out).startswith("> **Panel did not run this cycle:** the API call timed out.")
    assert out["health"].returncode == 0


# --- off, ran, no record -----------------------------------------------------


def test_no_key_is_a_deliberate_mode_and_stays_green():
    out = _run_panel_then_file(panel_enabled=False)
    assert _panel_line(out) == (
        "> **Panel:** off: no API key is visible to this repository, so this digest carries no verdicts."
    )
    assert "panel=off off: no API key is visible to this repository." in out["summary"]
    # The step is skipped in the workflow when the panel is off; run here to
    # show it would not fail on its own.
    assert out["filing"].returncode == 0, out["filing"].stderr


def test_the_panel_itself_records_off_when_no_key_reaches_it():
    out = _run_panel_then_file(key="")
    assert out["panel"].returncode == 0
    assert out["status"]["state"] == "off" and out["status"]["reason_code"] == "no_key"
    assert out["health"].returncode == 0


def test_a_blank_key_is_a_misconfiguration_that_fails_the_run():
    """Set but whitespace-only (a pasted newline) is not the deliberate no-key
    mode: the digest says so and Panel health fails."""
    for key in (" ", "\n", " \t \n"):
        out = _run_panel_then_file(key=key)
        assert out["status"]["state"] == "failed" and out["status"]["reason_code"] == "key_blank", repr(key)
        assert out["health"].returncode == 1, repr(key)
        assert out["panel"].stderr == "", repr(key)
        assert _panel_line(out) == (
            "> **Panel did not run this cycle:** the API key is set but blank. "
            "This digest carries no verdicts."
        ), repr(key)


def test_a_run_with_no_record_says_so_and_fails_the_run():
    """A panel step that crashed before writing anything: the digest names the
    step outcome, and Panel health fails rather than reading silence as fine."""
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        census_dir = tdp / "census"
        census_dir.mkdir()
        (census_dir / "digest.md").write_text("# Skill census digest\n\nbody\n", encoding="utf-8")
        bin_dir = tdp / "bin"
        bin_dir.mkdir()
        for name, body in (("gh", FAKE_GH), ("date", FAKE_DATE)):
            (bin_dir / name).write_text(body, encoding="utf-8")
            (bin_dir / name).chmod(0o755)
        env = dict(os.environ)
        env.update(
            {
                "PATH": f"{bin_dir}:{env['PATH']}",
                "CENSUS_DIR": str(census_dir),
                "GH_CALL_LOG": str(tdp / "calls.jsonl"),
                "GH_TOKEN": "dummy",
                "GH_REPO": "thrillmade/thrill-skills",
                "DRY_RUN": "false",
                "PANEL_ENABLED": "true",
                "PANEL_OUTCOME": "failure",
            }
        )
        _install_checker(tdp)
        filing = subprocess.run(
            ["bash", "-c", _step_script("file_issues")], cwd=tdp, env=env, capture_output=True, text=True, timeout=30
        )
        health = subprocess.run(
            ["bash", "-c", _step_script("panel_health")], cwd=tdp, env=env, capture_output=True, text=True, timeout=30
        )
        body = json.loads((tdp / "calls.jsonl").read_text(encoding="utf-8").splitlines()[0])["body"]
    assert filing.returncode == 0, filing.stderr
    assert body.splitlines()[2] == (
        "> **Panel did not run this cycle:** the panel step ended without reporting "
        "(step outcome: failure). See the run log."
    )
    assert health.returncode == 1
    assert "left no record" in health.stdout


def test_a_panel_that_ran_says_how_many_verdicts_and_keeps(tmp_path):
    """The `ran` line, from a panel_status.json as the panel writes it."""
    census_dir = tmp_path / "census"
    census_dir.mkdir()
    (census_dir / "digest.md").write_text("# Skill census digest\n\nbody\n", encoding="utf-8")
    (census_dir / "panel_status.json").write_text(
        json.dumps({"state": "ran", "reason_code": None, "reason": None, "http_status": None, "verdicts": 2, "keeps": 7}),
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in (("gh", FAKE_GH), ("date", FAKE_DATE)):
        (bin_dir / name).write_text(body, encoding="utf-8")
        (bin_dir / name).chmod(0o755)
    env = dict(os.environ)
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "CENSUS_DIR": str(census_dir),
            "GH_CALL_LOG": str(tmp_path / "calls.jsonl"),
            "GH_TOKEN": "dummy",
            "GH_REPO": "thrillmade/thrill-skills",
            "DRY_RUN": "false",
            "PANEL_ENABLED": "true",
            "PANEL_OUTCOME": "success",
        }
    )
    _install_checker(tmp_path)
    subprocess.run(["bash", "-c", _step_script("file_issues")], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)
    body = json.loads((tmp_path / "calls.jsonl").read_text(encoding="utf-8").splitlines()[0])["body"]
    assert body.splitlines()[2] == "> **Panel:** ran: 2 verdict(s), 7 kept."
    health = subprocess.run(["bash", "-c", _step_script("panel_health")], cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)
    assert health.returncode == 0


def test_every_person_needed_class_fails_panel_health_and_the_others_do_not():
    """The exit code per failure class, from the status the panel writes."""
    classes = {
        "authentication": 1,
        "permission": 1,
        "model_unavailable": 1,
        "sdk_missing": 1,
        "client_error": 1,
        "unexpected": 1,
        "an_unlisted_code": 1,
        "": 1,
        "rate_limited": 0,
        "service_error": 0,
        "timeout": 0,
        "connection": 0,
        "invalid_answer": 0,
    }
    for code, expected in classes.items():
        with tempfile.TemporaryDirectory() as td:
            census_dir = Path(td)
            (census_dir / "panel_status.json").write_text(
                json.dumps({"state": "failed", "reason_code": code, "reason": "a reason", "http_status": None, "verdicts": 0, "keeps": 0}),
                encoding="utf-8",
            )
            env = dict(os.environ, CENSUS_DIR=str(census_dir))
            health = subprocess.run(["bash", "-c", _step_script("panel_health")], cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=30)
            assert health.returncode == expected, (code, health.stdout, health.stderr)


def _health_on(content: str | None):
    with tempfile.TemporaryDirectory() as td:
        if content is not None:
            (Path(td) / "panel_status.json").write_text(content, encoding="utf-8")
        env = dict(os.environ, CENSUS_DIR=td)
        return subprocess.run(["bash", "-c", _step_script("panel_health")], cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=30)


def test_an_unreadable_record_fails_the_run():
    """The step's own script, against every shape of record that is not a
    readable status: each must fail the run (fail closed)."""
    for label, content in (
        ("empty", ""),
        ("garbage", "{not json at all"),
        ("array", "[]"),
        ("null", "null"),
        ("empty object", "{}"),
        ("non-string state", json.dumps({"state": 5})),
    ):
        health = _health_on(content)
        assert health.returncode == 1, (label, health.stdout, health.stderr)
        assert "::error::" in health.stdout, label
    assert _health_on(None).returncode == 1


def test_green_outcomes_print_no_error_annotation_and_failures_print_one():
    for code in ("rate_limited", "service_error", "timeout", "connection", "invalid_answer"):
        health = _health_on(json.dumps({"state": "failed", "reason_code": code, "reason": "r"}))
        assert health.returncode == 0 and "::error::" not in health.stdout, code
        assert "::warning::" in health.stdout, code
    for code in ("client_error", "unexpected", "authentication"):
        health = _health_on(json.dumps({"state": "failed", "reason_code": code, "reason": "r"}))
        assert health.returncode == 1 and "::error::" in health.stdout, code
    for state in ("ran", "off", "held_back"):
        health = _health_on(json.dumps({"state": state}))
        assert health.returncode == 0 and "::error::" not in health.stdout, state


def test_a_400_and_a_local_exception_fail_the_run_through_the_real_panel():
    for mode, code in (("badrequest", "client_error"), ("valueerror", "unexpected")):
        out = _run_panel_then_file(mode=mode)
        assert out["status"]["reason_code"] == code, mode
        assert out["health"].returncode == 1, (mode, out["health"].stdout)
        assert [c["title"] for c in out["calls"]] == ["census 2026-W47 digest"], "the digest files before the run fails"
        assert "did not run" in _panel_line(out)


def test_the_workflow_green_list_is_the_panels_transient_list():
    sys.path.insert(0, str(PANEL.parent))
    try:
        import census_panel
    finally:
        sys.path.pop(0)
    for code in census_panel.TRANSIENT_CODES:
        health = _health_on(json.dumps({"state": "failed", "reason_code": code, "reason": "r"}))
        assert health.returncode == 0, code


def test_a_panel_failure_annotates_by_whether_it_fails_the_run():
    """The annotation the workflow prints matches the run's conclusion: warning
    for a transient class, error for one that fails the run."""
    for mode, level in (("ratelimit", "warning"), ("timeout", "warning"), ("auth", "error"), ("badrequest", "error"), ("valueerror", "error"), ("", "error")):
        out = _run_panel_then_file(mode=mode)
        other = "error" if level == "warning" else "warning"
        health = out["health"].stdout
        assert f"::{level}::" in health, (mode, health)
        assert f"::{other}::" not in health, (mode, health)
        assert (out["panel"].stdout, out["panel"].stderr) == ("", ""), mode


def test_classify_failure_reads_status_and_class_name_only():
    sys.path.insert(0, str(PANEL.parent))
    try:
        import census_panel
    finally:
        sys.path.pop(0)

    def make(name, status=None, text="req_x sk-ant-y"):
        exc = type(name, (Exception,), {"status_code": status})(text)
        return census_panel.classify_failure(exc)

    assert make("AuthenticationError", 401)[0:3:2] == ("authentication", 401)
    assert make("PermissionDeniedError", 403)[0] == "permission"
    assert make("NotFoundError", 404)[0] == "model_unavailable"
    assert make("RateLimitError", 429)[0] == "rate_limited"
    assert make("InternalServerError", 503)[0] == "service_error"
    assert make("APITimeoutError")[0] == "timeout"
    assert make("APIConnectionError")[0] == "connection"
    assert census_panel.classify_failure(census_panel.PanelValidationError("x"))[0] == "invalid_answer"
    assert make("Weird")[1] == "an unexpected Weird"
    assert make("BadRequestError", 400)[0:3:2] == ("client_error", 400)
    assert make("ConflictError", 409)[0] == "client_error"
    assert make("TimeoutLikeError", 408)[0] == "client_error"
    # Name-matching is exact: a class merely named like a transient one, with
    # no HTTP status, is unexpected (red). The listed standard-library and SDK
    # classes are transient.
    for name in ("ConnectionConfigError", "BadKeyTimeoutError", "TimeoutLikeError", "ReadTimeout", "ConnectionFooError"):
        assert make(name)[0] == "unexpected", name
    for name in ("TimeoutError", "APITimeoutError"):
        assert make(name)[0] == "timeout", name
    for name in ("ConnectionError", "ConnectionResetError", "ConnectionAbortedError", "ConnectionRefusedError", "APIConnectionError"):
        assert make(name)[0] == "connection", name
    assert make("ConnectionConfigError", 401)[0] == "authentication"
    assert make("ValueError")[0] == "unexpected"
    assert census_panel.classify_failure(census_panel.PanelSdkMissing("x"))[0] == "sdk_missing"
    assert census_panel.classify_failure(census_panel.PanelNoText("x"))[0] == "invalid_answer"
    for result in (make("AuthenticationError", 401), make("Weird"), make("BadRequestError", 400), make("ValueError")):
        assert "req_x" not in result[1] and "sk-ant" not in result[1]
