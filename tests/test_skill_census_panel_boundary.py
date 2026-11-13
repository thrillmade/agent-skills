"""The census panel's output never reaches the public log: the boundary is the
workflow step, and it is tested from outside the process.

`census_panel.py` runs in a public repository's Actions next to a third-party
SDK that holds an API key. Four rounds tried to stop sensitive text leaving
that process, one reporting channel at a time (the call's exception, then
exceptions outside `Exception`, then import time and finalisers, then
`logging`, `warnings`, asyncio, `traceback`, a library that restores the stock
hooks, a library that simply prints). A process cannot police everything
written to its own streams, so the guarantee moved to the step:

  * the "Census panel (judgment)" step sends the script's stdout and stderr to
    /dev/null; it prints nothing;
  * `.github/scripts/panel_record.sh` checks every field of panel_status.json
    against a closed vocabulary and rewrites the record from fixed phrases;
  * the "File issues" and "Panel health" steps print only from that record.

These tests run the workflow's own embedded shell for those three steps for
real, against a HOSTILE stub `anthropic` package that prints, logs, warns,
raises every class of exception, restores the stock hooks, starts a thread
that raises, leaves an asyncio task un-awaited, registers an atexit handler
that raises, and names an exception class after a secret. The assertion is on
everything that could reach a reader: what the steps print, the job summary,
the issues filed, and every file the upload step would upload (its paths are
resolved from the workflow). A last pair of tests mutate the redirect and the
class allow-list and assert the leak comes back, so the guards can fail.
"""

from __future__ import annotations

import builtins
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "skill-census.yml"
CHECKER = REPO_ROOT / ".github" / "scripts" / "panel_record.sh"
PANEL = REPO_ROOT / ".github" / "scripts" / "census_panel.py"

REQUEST_ID = "req_011CNOLEAKFIXTURE0001"
FAKE_KEY = "sk-ant-api03-FAKEFIXTUREKEY-0000"
HEADERS = "x-api-key: " + FAKE_KEY + " Authorization: Bearer " + FAKE_KEY
HEADER_DUMP = "headers={" + HEADERS + "}"
PLANTS = (REQUEST_ID, FAKE_KEY, HEADER_DUMP, "x-api-key", "Bearer")
TEXT = f"Error code: 401 request_id={REQUEST_ID} {HEADER_DUMP}"

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

# Hostile on purpose. The first block runs at import; `fail()` and the rest run
# in the call. MODE picks what the call does in the end.
STUB = '''
import asyncio, atexit, gc, logging, os, sys, threading, traceback, warnings

SEC = os.environ["LEAK_TEXT"]
MODE = os.environ["LEAK_MODE"]
PLANT_CLASS = os.environ["LEAK_CLASS"]

class Custom(BaseException):
    pass

class Quiet(Exception):
    def __str__(self):
        raise RuntimeError(SEC)

class Bomb:
    def __del__(self):
        raise RuntimeError("finaliser " + SEC)

class RateLimitError(Exception):
    status_code = 429

class InternalServerError(Exception):
    status_code = 503

class AuthenticationError(Exception):
    status_code = 401

class APITimeoutError(Exception):
    pass

NamedAfterSecret = type(PLANT_CLASS, (Exception,), {})

def noise():
    print(SEC)
    print(SEC, file=sys.stderr)
    sys.stderr.write("headers: " + SEC + "\\n")
    logging.getLogger().setLevel(logging.DEBUG)
    logging.error(SEC)
    logging.getLogger("anthropic").error(SEC)
    logging.getLogger("httpx").error(SEC)
    warnings.warn(SEC)
    warnings.warn(SEC, DeprecationWarning)
    try:
        raise RuntimeError(SEC)
    except RuntimeError:
        traceback.print_exc()
        logging.exception(SEC)
    async def boom():
        raise RuntimeError(SEC)
    loop = asyncio.new_event_loop()
    task = loop.create_task(boom())
    loop.run_until_complete(asyncio.sleep(0))
    del task
    gc.collect()
    loop.close()

def restore_stock_hooks():
    sys.excepthook = sys.__excepthook__
    sys.unraisablehook = sys.__unraisablehook__
    threading.excepthook = threading.__excepthook__

noise()
if "restore" in MODE:
    restore_stock_hooks()
atexit.register(lambda: (_ for _ in ()).throw(RuntimeError("atexit " + SEC)))

def thread_raises():
    t = threading.Thread(target=lambda: (_ for _ in ()).throw(ValueError(SEC)))
    t.start(); t.join()

class _Block:
    type = "text"
    def __init__(self, text):
        self.text = text

class _Msg:
    stop_reason = "end_turn"
    def __init__(self, text):
        self.content = [_Block(text)]

GOOD = '{"verdicts": [], "digest_addendum_md": ""}'

class _Messages:
    def create(self, **kw):
        noise()
        if "restore" in MODE:
            restore_stock_hooks()
        if "thread" in MODE:
            thread_raises()
        if "finaliser" in MODE:
            Bomb()
        if MODE.startswith("ok"):
            return _Msg(GOOD)
        if MODE == "garbage":
            return _Msg("not json " + SEC)
        if MODE == "exit_nonzero_after_ran":
            atexit.register(lambda: os._exit(7))
            return _Msg(GOOD)
        if MODE == "vanish":
            os._exit(0)
        if MODE == "valueerror":
            raise ValueError(SEC)
        if MODE == "base":
            raise Custom(SEC)
        if MODE == "sysexit":
            raise SystemExit(SEC)
        if MODE == "keyboard":
            raise KeyboardInterrupt(SEC)
        if MODE == "strraises":
            raise Quiet()
        if MODE == "chain":
            try:
                raise KeyError(SEC)
            except KeyError:
                raise RuntimeError("outer") from ValueError(SEC)
        if MODE == "importerror":
            raise ImportError(SEC)
        if MODE == "secretclass":
            raise NamedAfterSecret(SEC)
        if MODE == "ratelimit":
            raise RateLimitError(SEC)
        if MODE == "server":
            raise InternalServerError(SEC)
        if MODE == "auth":
            raise AuthenticationError(SEC)
        if MODE == "timeout":
            raise APITimeoutError(SEC)
        raise RuntimeError(SEC)

class Anthropic:
    def __init__(self, *a, **k):
        noise()
        self.messages = _Messages()
'''

# mode -> (record state, reason code, health exit code, panel step exit code != 0)
CASES = {
    "ok": ("ran", None, 0),
    "ok_restore": ("ran", None, 0),
    "ok_restore_thread_finaliser": ("ran", None, 0),
    "ok_thread": ("ran", None, 0),
    "ok_finaliser": ("ran", None, 0),
    "garbage": ("failed", "invalid_answer", 0),
    "ratelimit": ("failed", "rate_limited", 0),
    "server": ("failed", "service_error", 0),
    "timeout": ("failed", "timeout", 0),
    "auth": ("failed", "authentication", 1),
    "valueerror": ("failed", "unexpected", 1),
    "valueerror_restore": ("failed", "unexpected", 1),
    "base": ("failed", "unexpected", 1),
    "sysexit": ("failed", "unexpected", 1),
    "keyboard": ("failed", "unexpected", 1),
    "strraises": ("failed", "unexpected", 1),
    "chain": ("failed", "unexpected", 1),
    "importerror": ("failed", "unexpected", 1),
    "secretclass": ("failed", "unexpected", 1),
    "secretclass_restore_thread_finaliser": ("failed", "unexpected", 1),
    "exit_nonzero_after_ran": ("failed", "script_exit", 1),
    "vanish": (None, None, 1),
}


def _steps() -> list[dict]:
    return yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["census"]["steps"]


def _step_script(step_id: str) -> str:
    return next(s for s in _steps() if s.get("id") == step_id)["run"]


def _upload_paths(runner_temp: Path) -> list[Path]:
    step = next(s for s in _steps() if str(s.get("uses", "")).startswith("actions/upload-artifact"))
    paths = [p.strip() for p in step["with"]["path"].splitlines() if p.strip()]
    return [Path(p.replace("${{ runner.temp }}", str(runner_temp))) for p in paths]


def _resolve_upload(runner_temp: Path) -> list[Path]:
    """The files the upload action would upload: every named path, a directory
    expanded to its descendants and links followed (what upload-artifact does)."""
    found: list[Path] = []
    for path in _upload_paths(runner_temp):
        if path.is_dir():
            found += [p for p in path.rglob("*") if p.is_file()]
        elif path.is_file():
            found.append(path)
    return found


def _exe(path: Path, body: str) -> None:
    path.write_text(body, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _exercise(
    tmp_path: Path,
    mode: str,
    *,
    key: str = FAKE_KEY,
    complete: bool = True,
    panel_script: str | None = None,
    checker: str | None = None,
    python_shim: str | None = None,
    extra_env: dict | None = None,
) -> dict:
    """Run the workflow's panel step, File issues and Panel health for real, in
    that order, as the runner does, from a scratch workspace holding copies of
    the two scripts (so a test can mutate the checker)."""
    work = tmp_path / "work"
    bin_dir = work / "bin"
    bin_dir.mkdir(parents=True)
    _exe(bin_dir / "gh", FAKE_GH)
    _exe(bin_dir / "date", FAKE_DATE)
    if python_shim is not None:
        _exe(bin_dir / "python3", python_shim)
    else:
        (bin_dir / "python3").symlink_to(sys.executable)
    sdk = work / "sdk" / "anthropic"
    sdk.mkdir(parents=True)
    (sdk / "__init__.py").write_text(STUB, encoding="utf-8")
    scripts = work / ".github" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "panel_record.sh").write_text(
        checker if checker is not None else CHECKER.read_text(encoding="utf-8"), encoding="utf-8"
    )
    shutil.copy(PANEL, scripts / "census_panel.py")
    runner_temp = work
    census = runner_temp / "census"
    census.mkdir()
    cov = {"consumers": 8, "read": 8, "complete": True} if complete else {"consumers": 8, "read": 7, "complete": False}
    (census / "census.json").write_text(json.dumps({"cycle": "census-2026-W47", "coverage": cov}), encoding="utf-8")
    (census / "digest.md").write_text("# Skill census digest\n\nbody\n", encoding="utf-8")
    summary = work / "summary.md"
    calls = work / "calls.jsonl"

    env = dict(os.environ)
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "PYTHONPATH": str(work / "sdk"),
            "ANTHROPIC_API_KEY": key,
            "CENSUS_DIR": str(census),
            "GH_TOKEN": "dummy",
            "GH_REPO": "thrillmade/thrill-skills",
            "GH_CALL_LOG": str(calls),
            "DRY_RUN": "false",
            "GITHUB_STEP_SUMMARY": str(summary),
            "GITHUB_ENV": str(work / "github_env"),
            "GITHUB_OUTPUT": str(work / "github_output"),
            "GITHUB_PATH": str(work / "github_path"),
            "GITHUB_STATE": str(work / "github_state"),
            "STAGE_DIR": str(runner_temp / "census-upload"),
            "PANEL_ENABLED": "true",
            "LEAK_MODE": mode,
            "LEAK_TEXT": TEXT,
            "LEAK_CLASS": REQUEST_ID,
        }
    )
    env.update(extra_env or {})

    def run(script: str, cwd: Path) -> subprocess.CompletedProcess:
        return subprocess.run(["bash", "-c", script], cwd=cwd, env=env, capture_output=True, text=True, timeout=180)

    panel = run(panel_script if panel_script is not None else _step_script("panel"), work)
    env["PANEL_OUTCOME"] = "success" if panel.returncode == 0 else "failure"
    filing = run(_step_script("file_issues"), work)
    stage = run(_step_script("stage_upload"), work)
    health = run(_step_script("panel_health"), work)

    printed = "\n".join(p.stdout + "\n" + p.stderr for p in (panel, filing, stage, health))
    resolved = _resolve_upload(runner_temp)
    uploaded = [path.read_text(encoding="utf-8", errors="replace") for path in resolved]
    # Everything on disk outside the stub, the shims and the scripts: the digest, the issues filed,
    # the summary, the record, anything else the run left.
    on_disk = []
    for path in work.rglob("*"):
        if path.is_file() and not {"sdk", "bin", ".github"} & set(path.relative_to(work).parts):
            on_disk.append(path.read_text(encoding="utf-8", errors="replace"))
    record_path = census / "panel_status.json"
    return {
        "panel": panel,
        "filing": filing,
        "health": health,
        "printed": printed,
        "uploaded": uploaded,
        "resolved": resolved,
        "work": work,
        "everything": printed + "\n" + "\n".join(uploaded) + "\n" + "\n".join(on_disk),
        "record": json.loads(record_path.read_text(encoding="utf-8")) if record_path.exists() else None,
        "summary": summary.read_text(encoding="utf-8") if summary.exists() else "",
        "calls": [json.loads(l) for l in calls.read_text(encoding="utf-8").splitlines()] if calls.exists() else [],
    }


def _assert_no_plants(text: str, label: str) -> None:
    for plant in PLANTS:
        assert plant not in text, f"{plant!r} reached an output ({label}):\n{text[:2000]}"
    assert "Traceback" not in text and "Exception ignored" not in text, (label, text[:2000])


# --- the guarantee: nothing the panel process writes reaches a reader -----------


@pytest.mark.parametrize("mode", sorted(CASES))
def test_hostile_sdk_output_reaches_no_reader_and_the_conclusion_is_right(tmp_path, mode):
    state, code, health_rc = CASES[mode]
    out = _exercise(tmp_path, mode)
    _assert_no_plants(out["everything"], mode)
    assert out["panel"].stdout == "" and out["panel"].stderr == "", "the panel step must print nothing"
    if state is None:
        assert out["record"] is None
    else:
        assert out["record"]["state"] == state and out["record"]["reason_code"] == code, out["record"]
    assert out["health"].returncode == health_rc, (mode, out["health"].stdout)
    if health_rc == 1:
        assert "::error::" in out["health"].stdout and "::warning::" not in out["health"].stdout.replace(
            "withheld", ""
        ), out["health"].stdout
    # The digest is filed before the failing exit, whatever happened.
    assert [c["title"] for c in out["calls"]] == ["census 2026-W47 digest"], mode


def test_a_class_named_after_the_secret_is_reported_as_unrecognised_not_echoed(tmp_path):
    out = _exercise(tmp_path, "secretclass")
    assert out["record"]["exc_class"] == "unrecognised"
    assert "class=an unrecognised exception class" in out["health"].stdout
    assert REQUEST_ID not in out["everything"]


def test_an_operator_can_work_a_failure_from_the_log_line(tmp_path):
    out = _exercise(tmp_path, "auth")
    assert (
        "::error::census panel needs attention: state=failed reason=the API key was refused (HTTP 401) "
        "code=authentication stage=call http=401 class=AuthenticationError."
    ) in out["health"].stdout
    assert "withheld on purpose" in out["health"].stdout
    assert "census_panel.py locally" in out["health"].stdout
    assert out["record"]["stage"] == "call"


def test_a_background_error_in_a_run_that_completed_is_a_warning_not_a_failure(tmp_path):
    """Policy: a finaliser or thread error during a run that otherwise
    completed is not a failure. The record says ran, the run is green, the
    workflow warns (not an error, not 'did not run') with the class only."""
    out = _exercise(tmp_path, "ok_thread")
    assert out["record"]["state"] == "ran" and out["record"]["background_error_class"] == "ValueError"
    assert out["panel"].returncode == 0 and out["health"].returncode == 0
    health = out["health"].stdout
    assert "Panel health: ran." in health
    assert "::warning::census panel: a background error of class ValueError was ignored" in health
    assert "::error::" not in health and "did not run" not in health
    _assert_no_plants(out["everything"], "ok_thread")


def test_a_finaliser_error_in_a_run_that_completed_is_a_warning_not_a_failure(tmp_path):
    out = _exercise(tmp_path, "ok_finaliser")
    assert out["record"]["state"] == "ran" and out["record"]["background_error_class"] == "RuntimeError"
    assert out["health"].returncode == 0
    assert "a background error of class RuntimeError was ignored" in out["health"].stdout
    assert "::error::" not in out["health"].stdout


def test_a_partial_census_and_no_key_stay_green_and_a_blank_key_is_red(tmp_path):
    held = _exercise(tmp_path / "a", "ok", complete=False)
    assert held["record"]["state"] == "held_back" and held["health"].returncode == 0
    off = _exercise(tmp_path / "b", "ok", key="")
    assert off["record"]["state"] == "off" and off["health"].returncode == 0
    blank = _exercise(tmp_path / "c", "ok", key=" \n")
    assert blank["record"]["reason_code"] == "key_blank" and blank["health"].returncode == 1
    for out in (held, off, blank):
        _assert_no_plants(out["everything"], "state")


def test_the_step_exit_status_is_kept_whatever_the_record_says(tmp_path):
    out = _exercise(tmp_path, "exit_nonzero_after_ran")
    assert out["panel"].returncode == 7
    assert out["record"]["state"] == "failed" and out["record"]["reason_code"] == "script_exit"
    assert out["health"].returncode == 1


# --- a record whose fields carry the plants --------------------------------------

SHIM = """#!/bin/sh
printf '%s' "$PLANTED_RECORD" > "$CENSUS_DIR/panel_status.json"
exit 0
"""

FIXED_PHRASE = "panel_status.json held a value outside the allowed set"


def _planted(tmp_path: Path, record: dict) -> dict:
    return _planted_raw(tmp_path, json.dumps(record))


@pytest.mark.parametrize(
    "field,value",
    [
        ("state", TEXT),
        ("reason_code", TEXT),
        ("stage", TEXT),
        ("http_status", TEXT),
        ("http_status", "401"),
        ("http_status", 99),
        ("http_status", 600),
        ("http_status", 401.5),
        ("verdicts", TEXT),
        ("keeps", -1),
        ("exc_class", {"x": TEXT}),
        ("exc_class", 5),
    ],
)
def test_a_record_field_outside_its_vocabulary_is_replaced_by_a_fixed_phrase_and_the_run_is_red(
    tmp_path, field, value
):
    record = {"state": "failed", "reason_code": "timeout", "stage": "call", "http_status": 429, "verdicts": 0, "keeps": 0}
    record[field] = value
    out = _planted(tmp_path, record)
    assert out["health"].returncode == 1
    assert "code=bad_record" in out["health"].stdout and FIXED_PHRASE in out["health"].stdout, out["health"].stdout
    _assert_no_plants(out["everything"], field)
    assert out["record"]["reason_code"] == "bad_record"


def test_a_planted_class_name_is_never_echoed(tmp_path):
    record = {"state": "failed", "reason_code": "unexpected", "stage": "call", "exc_class": REQUEST_ID}
    out = _planted(tmp_path, record)
    assert out["health"].returncode == 1
    assert "class=an unrecognised exception class" in out["health"].stdout
    _assert_no_plants(out["everything"], "exc_class")


def test_a_planted_reason_is_never_read(tmp_path):
    record = {"state": "failed", "reason_code": "authentication", "reason": TEXT, "stage": "call", "http_status": 401}
    out = _planted(tmp_path, record)
    assert out["health"].returncode == 1
    assert "the API key was refused (HTTP 401)" in out["health"].stdout
    _assert_no_plants(out["everything"], "reason")


def test_a_planted_background_class_is_a_warning_with_the_fixed_phrase(tmp_path):
    record = {"state": "ran", "reason_code": None, "stage": "write", "background_error_class": REQUEST_ID}
    out = _planted(tmp_path, record)
    assert out["health"].returncode == 0
    assert "a background error of class an unrecognised exception class was ignored" in out["health"].stdout
    _assert_no_plants(out["everything"], "background")


@pytest.mark.parametrize("content", ["", "{not json" + TEXT, "[]", "null", '"' + TEXT + '"'])
def test_an_unreadable_record_is_red_and_never_echoed(tmp_path, content):
    out = _planted_raw(tmp_path, content)
    assert out["health"].returncode == 1
    _assert_no_plants(out["everything"], "raw")


def _planted_raw(tmp_path: Path, content: str) -> dict:
    """The script is replaced by a shim that writes `content` as the record, so
    the record is whatever a compromised process could have left."""
    return _exercise(tmp_path, "ok", python_shim=SHIM, extra_env={"PLANTED_RECORD": content})


# --- the vocabulary is the writer's ----------------------------------------------


def _checker_list(name: str) -> set[str]:
    text = CHECKER.read_text(encoding="utf-8")
    match = re.search(rf'^{name}="((?:[^"\\]|\\.)*)"', text, re.M | re.S)
    assert match, name
    return set(match.group(1).replace("\\\n", " ").split())


def test_every_builtin_exception_name_is_on_the_allow_list():
    names = {n for n, v in vars(builtins).items() if isinstance(v, type) and issubclass(v, BaseException)}
    missing = names - _checker_list("EXC_CLASSES")
    # PythonFinalizationError is 3.13+; the list names it for the workflow's newer interpreters.
    assert not missing, sorted(missing)


def test_the_codes_the_panel_writes_are_all_known_to_the_checker():
    sys.path.insert(0, str(PANEL.parent))
    try:
        import census_panel
    finally:
        sys.path.pop(0)
    codes = _checker_list("CODES")
    source = PANEL.read_text(encoding="utf-8")
    written = set(re.findall(r'return "([a-z_]+)", ', source)) | {"no_key", "partial_census", "key_blank", "unexpected"}
    assert written <= codes, sorted(written - codes)
    assert set(census_panel.TRANSIENT_CODES) <= codes
    stages = _checker_list("STAGES")
    assert set(re.findall(r'_STAGE = "([a-z_]+)"', source)) | {"write"} <= stages


def test_the_sdk_exception_names_are_listed():
    classes = _checker_list("EXC_CLASSES")
    for name in ("AnthropicError", "APIError", "APIStatusError", "APIConnectionError", "APITimeoutError",
                 "AuthenticationError", "PermissionDeniedError", "NotFoundError", "RateLimitError",
                 "InternalServerError", "BadRequestError", "UnprocessableEntityError", "OverloadedError"):
        assert name in classes, name


# --- the second layer: logging and warnings are silenced in the script -------------


def test_logging_and_warnings_are_silenced_inside_the_script(tmp_path):
    """Defence in depth: the script itself silences logging and warnings, so a
    local run does not print them either. The guarantee is the redirect."""
    driver = tmp_path / "driver.py"
    driver.write_text(
        "import runpy, sys, logging, warnings\n"
        f"ns = runpy.run_path({str(PANEL)!r}, run_name='not_main')\n"
        "ns['_install_reporters']()\n"
        f"logging.warning({TEXT!r}); logging.exception({TEXT!r}); warnings.warn({TEXT!r})\n",
        encoding="utf-8",
    )
    proc = subprocess.run([sys.executable, str(driver)], capture_output=True, text=True, timeout=60)
    _assert_no_plants(proc.stdout + proc.stderr, "logging")
    assert proc.returncode == 0


# --- the guards can fail ------------------------------------------------------------


def test_removing_the_redirect_brings_the_leak_back(tmp_path):
    original = _step_script("panel")
    assert ">/dev/null 2>&1 || rc=$?" in original
    mutated = original.replace(">/dev/null 2>&1 || rc=$?", "|| rc=$?")
    assert mutated != original
    out = _exercise(tmp_path, "ok", panel_script=mutated)
    assert any(p in out["printed"] for p in PLANTS), "the hostile stub must leak once the redirect is gone"


def test_removing_the_class_allow_list_check_brings_the_leak_back(tmp_path):
    original = CHECKER.read_text(encoding="utf-8")
    needle = '! in_list "$v" "$EXC_CLASSES"'
    assert needle in original
    mutated = original.replace(needle, "false")
    assert mutated != original
    out = _exercise(tmp_path, "secretclass", checker=mutated)
    assert REQUEST_ID in out["health"].stdout, "a class named after the secret must be echoed without the check"


# --- the record is checked at each use, and only regular files cross ---------------

# The shim stands in for the panel script: it writes a valid record, then does
# what a compromised process could do on the way out. `PLANT` is the text a
# reader must never see.
PLANT = "PLANT-" + REQUEST_ID
OK_RECORD = '{"state":"ran","reason_code":null,"stage":"write","verdicts":0,"keeps":0}'


def _shim(body: str) -> str:
    return "#!/bin/sh\n" + body


def _assert_upload_clean(out: dict) -> None:
    for path in out["resolved"]:
        assert path.name in {"census.json", "digest.md", "verdicts.json", "panel_status.json"}, path
        assert not path.is_symlink(), path
        assert PLANT not in path.read_text(encoding="utf-8", errors="replace"), path
    assert PLANT not in out["everything"]


@pytest.mark.parametrize("kind", ["dir", "symlink", "fifo"])
def test_a_non_regular_record_is_removed_red_and_nothing_under_it_is_uploaded(tmp_path, kind):
    make = {
        "dir": 'mkdir "$CENSUS_DIR/panel_status.json"; echo "$PLANT" > "$CENSUS_DIR/panel_status.json/leak.txt"',
        "symlink": 'echo "$PLANT" > "$TARGET"; ln -s "$TARGET" "$CENSUS_DIR/panel_status.json"',
        "fifo": 'mkfifo "$CENSUS_DIR/panel_status.json"',
    }[kind]
    out = _exercise(tmp_path, "ok", python_shim=_shim(make + "\nexit 0\n"),
                    extra_env={"PLANT": PLANT, "TARGET": str(tmp_path / "outside.txt")})
    assert out["health"].returncode == 1, out["health"].stdout
    assert "code=bad_record" in out["health"].stdout
    assert out["record"]["reason_code"] == "bad_record"
    assert (out["work"] / "census" / "panel_status.json").is_file()
    _assert_upload_clean(out)


@pytest.mark.parametrize("name", ["verdicts.json", "digest.md", "census.json"])
def test_a_directory_in_place_of_another_census_file_is_removed_and_not_uploaded(tmp_path, name):
    body = (
        f"printf '%s' '{OK_RECORD}' > \"$CENSUS_DIR/panel_status.json\"\n"
        f'rm -rf "$CENSUS_DIR/{name}"; mkdir "$CENSUS_DIR/{name}"; echo "$PLANT" > "$CENSUS_DIR/{name}/leak.txt"\n'
    )
    out = _exercise(tmp_path, "ok", python_shim=_shim(body), extra_env={"PLANT": PLANT})
    assert not (out["work"] / "census" / name).exists()
    assert not any(p.name == "leak.txt" for p in out["resolved"])
    _assert_upload_clean(out)


def test_the_panel_script_runs_without_the_runner_file_command_variables(tmp_path):
    keys = tmp_path / "keys.txt"
    body = (
        # the fake gh is a python3 script too, so only the first run (the panel's) is recorded
        f"[ -e '{keys}' ] || env | sed 's/=.*//' > '{keys}'\n"
        f"printf '%s' '{OK_RECORD}' > \"$CENSUS_DIR/panel_status.json\"\n"
    )
    out = _exercise(tmp_path / "w", "ok", python_shim=_shim(body))
    seen = set(keys.read_text(encoding="utf-8").split())
    assert "CENSUS_DIR" in seen and "PATH" in seen, "the stub must have run with the rest of the environment"
    runner_vars = {"GITHUB_STEP_SUMMARY", "GITHUB_ENV", "GITHUB_OUTPUT", "GITHUB_PATH", "GITHUB_STATE"}
    assert not runner_vars & seen, sorted(runner_vars & seen)
    assert out["panel"].returncode == 0


def test_a_process_that_rewrites_the_record_after_the_check_is_not_printed_or_uploaded(tmp_path):
    """A record swapped in after the checker ran is never read: each step
    checks the record itself first, and stages from the checker's output."""
    work_status = "$CENSUS_DIR/panel_status.json"
    body = (
        # the fake gh is this shim too: only the first run (the panel's) starts a racer, and it is bounded
        '[ -e "$CENSUS_DIR/../racer.pid" ] && exit 0\n'
        f"printf '%s' '{OK_RECORD}' > \"{work_status}\"\n"
        "( n=0; while [ $n -lt 3000 ]; do n=$((n+1)); printf '%s' '{\"state\":\"failed\",\"reason_code\":\"authentication\",\"reason\":\"'\"$PLANT\"'\"}' "
        f"> \"{work_status}.x\" && mv \"{work_status}.x\" \"{work_status}\"; done ) >/dev/null 2>&1 &\n"
        'echo $! > "$CENSUS_DIR/../racer.pid"\n'
    )
    try:
        out = _exercise(tmp_path, "ok", python_shim=_shim(body), extra_env={"PLANT": PLANT})
    finally:
        pid = (tmp_path / "work" / "racer.pid")
        if pid.exists():
            subprocess.run(["kill", pid.read_text().strip()], capture_output=True)
    readers = out["printed"] + out["summary"] + "\n".join(out["uploaded"]) + json.dumps(out["calls"])
    assert PLANT not in readers


def test_the_operator_line_carries_the_scripts_exit_status(tmp_path):
    out = _exercise(tmp_path, "exit_nonzero_after_ran")
    assert " exit=7." in out["health"].stdout, out["health"].stdout
    assert out["record"]["exit_status"] == 7
    out = _exercise(tmp_path / "again", "ok", python_shim=_shim("exit 3\n"))
    assert " exit=3." in out["health"].stdout, out["health"].stdout


def _check(tmp_path: Path, record: str, rc: str | None = None) -> subprocess.CompletedProcess:
    census = tmp_path / "census"
    census.mkdir(parents=True)
    (census / "panel_status.json").write_text(record, encoding="utf-8")
    cmd = ["bash", str(CHECKER), str(census)] + ([rc] if rc is not None else [])
    return subprocess.run(cmd, capture_output=True, text=True, timeout=60)


@pytest.mark.parametrize(
    "field,bad",
    [
        ("reason_code", "no_key partial_census"),
        ("reason_code", " no_key"),
        ("reason_code", "no_key "),
        ("reason_code", ""),
        ("reason_code", "no_key\n"),
        ("stage", "call parse"),
        ("stage", " call"),
        ("stage", "call "),
        ("stage", ""),
        ("stage", "call\n"),
        ("state", "ran\n"),
        ("state", "ran failed"),
        ("state", " ran"),
        ("state", ""),
    ],
)
def test_a_value_is_accepted_only_as_an_exact_listed_word(tmp_path, field, bad):
    record = {"state": "failed", "reason_code": "timeout", "stage": "call"}
    record[field] = bad
    out = json.loads(_check(tmp_path, json.dumps(record)).stdout)
    assert out["reason_code"] == "bad_record" and out["state"] == "failed", (field, bad, out)


def test_every_listed_state_code_and_stage_alone_is_accepted(tmp_path):
    for i, state in enumerate(("ran", "off", "held_back", "failed")):
        out = json.loads(_check(tmp_path / f"s{i}", json.dumps({"state": state})).stdout)
        assert out["state"] == state and out["reason_code"] is None, out
    for i, code in enumerate(sorted(_checker_list("CODES") - {"bad_record"})):
        out = json.loads(_check(tmp_path / f"c{i}", json.dumps({"state": "failed", "reason_code": code})).stdout)
        assert out["reason_code"] == code, (code, out)
    for i, stage in enumerate(sorted(_checker_list("STAGES"))):
        out = json.loads(_check(tmp_path / f"t{i}", json.dumps({"state": "ran", "stage": stage})).stdout)
        assert out["stage"] == stage, (stage, out)
