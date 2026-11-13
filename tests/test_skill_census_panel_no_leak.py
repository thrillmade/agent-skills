"""The census panel's in-process reporters print no exception text (second layer).

The guarantee is the workflow step's redirect, pinned in
test_skill_census_panel_boundary.py; this file pins the defence in depth that
makes a local run and the record clean as well.

The script runs in a public repository, next to a third-party SDK that holds an
API key; the Actions log is readable by anyone. Earlier rounds closed the model
call, then exceptions that are not `Exception`. The class is wider: an exception
raised importing the SDK, in a finaliser (the interpreter prints those itself,
as "Exception ignored in"), in a thread, at shutdown. So the script replaces the
interpreter's reporters before its first import and imports the SDK only inside
its guarded region.

Each case runs the REAL file as a subprocess, as the workflow does, with a stub
`anthropic` package on the path whose failure carries a request id, a header
dump and a fake key. The assertion is on what leaves the process: neither
stream, and no file written, may contain any of them; and on the exit code and
whether a record (panel_status.json) exists. Cases with no record rely on the
workflow's "the panel step ended without reporting" path (tested elsewhere).
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
PANEL = REPO_ROOT / ".github" / "scripts" / "census_panel.py"

REQUEST_ID = "req_011CNOLEAKFIXTURE0001"
FAKE_KEY = "sk-ant-api03-FAKEFIXTUREKEY-0000"
HEADERS = "x-api-key: " + FAKE_KEY + " Authorization: Bearer " + FAKE_KEY
SECRETS = (REQUEST_ID, FAKE_KEY, "x-api-key", "Authorization", "Bearer")
TEXT = f"Error code: 401 request_id={REQUEST_ID} {HEADERS}"

# Raised by the stub, at import time ("import_*") or from the client's
# constructor, which is inside the model call ("call_*").
STUB = '''
import os, sys, threading

TEXT = os.environ["LEAK_TEXT"]
MODE = os.environ["LEAK_MODE"]
where, _, kind = MODE.partition("_")

class Custom(BaseException):
    pass

class Quiet(Exception):
    def __str__(self):
        raise RuntimeError(TEXT)

class Bomb:
    def __del__(self):
        raise RuntimeError("finaliser " + TEXT)

_keep = []

def fail():
    if kind == "valueerror":
        raise ValueError(TEXT)
    if kind == "base":
        raise Custom(TEXT)
    if kind == "sysexit":
        raise SystemExit(TEXT)
    if kind == "strraises":
        raise Quiet()
    if kind == "chain":
        try:
            raise KeyError(TEXT)
        except KeyError as inner:
            raise RuntimeError("outer") from ValueError(TEXT)
    if kind == "context":
        try:
            raise KeyError(TEXT)
        except KeyError:
            raise RuntimeError("outer")
    if kind == "importerror":
        raise ImportError(TEXT)
    if kind == "delcall":
        Bomb()
        raise RuntimeError("benign")
    if kind == "delshutdown":
        _keep.append(Bomb())
        raise RuntimeError("benign")
    if kind == "thread":
        t = threading.Thread(target=lambda: (_ for _ in ()).throw(ValueError(TEXT)))
        t.start(); t.join()
        raise RuntimeError("benign")

if where == "import":
    fail()

class Anthropic:
    def __init__(self, *a, **k):
        fail()
        raise RuntimeError("fake client reached")
'''

# (mode, exit code, record state or None for "no record", class named on stderr)
CASES = [
    ("import_valueerror", 0, "unexpected", "ValueError"),
    ("import_base", 1, "unexpected", "Custom"),
    ("import_sysexit", 1, "unexpected", "SystemExit"),
    ("import_strraises", 0, "unexpected", "Quiet"),
    ("import_chain", 0, "unexpected", "RuntimeError"),
    ("import_context", 0, "unexpected", "RuntimeError"),
    ("import_importerror", 0, "sdk_missing", None),
    ("import_delcall", 0, "unexpected", "RuntimeError"),
    ("call_valueerror", 0, "unexpected", "ValueError"),
    ("call_base", 1, "unexpected", "Custom"),
    ("call_sysexit", 1, "unexpected", "SystemExit"),
    ("call_strraises", 0, "unexpected", "Quiet"),
    ("call_chain", 0, "unexpected", "RuntimeError"),
    ("call_context", 0, "unexpected", "RuntimeError"),
    ("call_delcall", 0, "unexpected", "RuntimeError"),
    ("call_delshutdown", 0, "unexpected", "RuntimeError"),
    ("call_thread", 0, "unexpected", "ValueError"),
]


def _run(tmp_path: Path, mode: str, script: Path = PANEL) -> tuple[subprocess.CompletedProcess, dict | None, str]:
    sdk = tmp_path / "sdk" / "anthropic"
    sdk.mkdir(parents=True)
    (sdk / "__init__.py").write_text(STUB, encoding="utf-8")
    census = tmp_path / "census"
    census.mkdir()
    (census / "census.json").write_text(json.dumps({"cycle": "census-2026-W47"}), encoding="utf-8")
    env = {
        "PATH": os.environ["PATH"],
        "PYTHONPATH": str(tmp_path / "sdk"),
        "ANTHROPIC_API_KEY": FAKE_KEY,
        "CENSUS_DIR": str(census),
        "LEAK_MODE": mode,
        "LEAK_TEXT": TEXT,
        "GH_TOKEN": "dummy",
    }
    proc = subprocess.run(
        [sys.executable, str(script)], cwd=REPO_ROOT, env=env, capture_output=True, text=True, timeout=120
    )
    status = census / "panel_status.json"
    record = json.loads(status.read_text(encoding="utf-8")) if status.exists() else None
    written = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in census.iterdir())
    return proc, record, proc.stdout + "\n" + proc.stderr + "\n" + written


def _assert_clean(everything: str) -> None:
    for secret in SECRETS:
        assert secret not in everything, f"{secret!r} reached an output:\n{everything}"
    assert "Traceback" not in everything and "Exception ignored" not in everything, everything


@pytest.mark.parametrize("mode,code,state,klass", CASES, ids=[c[0] for c in CASES])
def test_no_exception_text_reaches_any_stream_or_file(tmp_path, mode, code, state, klass):
    proc, record, everything = _run(tmp_path, mode)
    _assert_clean(everything)
    assert proc.returncode == code, (proc.returncode, proc.stderr)
    assert record is not None and record["state"] == "failed" and record["reason_code"] == state
    if klass:
        assert klass in proc.stderr, proc.stderr


def test_the_finaliser_report_names_the_class_only(tmp_path):
    proc, _, _ = _run(tmp_path, "call_delcall")
    [line] = [l for l in proc.stderr.splitlines() if "ignored" in l]
    assert line == "::warning::census panel: an exception of class RuntimeError was ignored in a finaliser or callback"


def test_a_finaliser_that_raises_at_shutdown_is_reported_by_class_after_the_record(tmp_path):
    proc, record, everything = _run(tmp_path, "call_delshutdown")
    assert proc.stderr.count("was ignored in a finaliser") == 1, proc.stderr
    assert record is not None
    _assert_clean(everything)


def test_a_standard_module_that_fails_to_import_prints_the_class_only_and_leaves_no_record(tmp_path):
    """Earliest possible failure: the first import block. No record can be
    written; the non-zero exit is what the workflow's no-report path catches."""
    work = tmp_path / "bin"
    work.mkdir()
    shutil.copy(PANEL, work / "census_panel.py")
    (work / "json.py").write_text(f"raise ValueError({TEXT!r})\n", encoding="utf-8")
    proc, record, everything = _run(tmp_path, "call_valueerror", script=work / "census_panel.py")
    _assert_clean(everything)
    assert proc.returncode == 1 and record is None
    assert "an unexpected ValueError" in proc.stderr


def test_an_exception_that_escapes_everything_is_reported_by_the_replaced_hook(tmp_path):
    """The uncaught-exception hook is the last net. Drive it directly: load the
    script as __main__ with `main` replaced by something that raises past it."""
    driver = tmp_path / "driver.py"
    driver.write_text(
        "import runpy, sys\n"
        f"sys.argv = [{str(PANEL)!r}]\n"
        "ns = runpy.run_path(%r, run_name='not_main')\n" % str(PANEL)
        + "ns['_install_reporters']()\n"
        f"raise ValueError({TEXT!r})\n",
        encoding="utf-8",
    )
    proc = subprocess.run([sys.executable, str(driver)], capture_output=True, text=True, timeout=60)
    _assert_clean(proc.stdout + proc.stderr)
    assert proc.returncode == 1
    assert "an uncaught ValueError" in proc.stderr


def test_other_printed_text_is_fixed_or_class_only(tmp_path):
    """A census.json that is not JSON: the log names the file and the class."""
    census = tmp_path / "census"
    census.mkdir()
    (census / "census.json").write_text("{" + TEXT, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(PANEL)],
        cwd=REPO_ROOT,
        env={"PATH": os.environ["PATH"], "ANTHROPIC_API_KEY": FAKE_KEY, "CENSUS_DIR": str(census)},
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 1
    assert "JSONDecodeError" in proc.stderr
    _assert_clean(proc.stdout + proc.stderr)


def _module():
    spec = importlib.util.spec_from_file_location("census_panel_no_leak", PANEL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_a_gh_failure_records_the_exit_status_and_not_gh_stderr(monkeypatch):
    """gh's stderr is text a token or request id could ride in, and the docket
    error reaches the prompt and verdicts.json: only the status is kept."""
    panel = _module()
    done = subprocess.CompletedProcess([], 4, "", f"HTTP 401 {TEXT}")
    monkeypatch.setattr(panel.subprocess, "run", lambda *a, **k: done)
    issues, error = panel.fetch_docket()
    assert issues == [] and error == "gh exited 4"

    def boom(*a, **k):
        raise OSError(TEXT)

    monkeypatch.setattr(panel.subprocess, "run", boom)
    _, error = panel.fetch_docket()
    assert error == "gh invocation error: OSError"
    monkeypatch.setattr(panel.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0, TEXT, ""))
    _, error = panel.fetch_docket()
    assert error == "gh output was not JSON"


def test_a_dropped_amend_target_is_not_echoed_into_the_log(capsys):
    panel = _module()
    answer = json.dumps(
        {
            "verdicts": [
                {"kind": "gap", "subject": "s", "grounds": "g", "disposition": "amend", "amend_target": TEXT}
            ]
        }
    )
    panel.validate_and_build(answer, "census-2026-W47", "x", {}, frozenset())
    captured = capsys.readouterr()
    assert "dropping verdict" in captured.err
    _assert_clean(captured.out + captured.err)
