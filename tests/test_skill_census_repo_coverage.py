"""#313: a census that could not read a repository must say so, by name.

Two halves of `census_counters.py`, both run as the workflow runs them -- the
real script in a subprocess, talking real HTTP (urllib, redirects and all) to
a fake GitHub API on localhost -- so every assertion is on what an operator
sees: the log lines, GITHUB_OUTPUT, digest.md, census.json and the exit code.

1. The counters (`main`). A repository the token cannot see answers 404, and
   so does a lock file a readable repository simply does not carry. The
   census used to read both as "no lock", so an unreadable consumer was
   counted as read with zero subscriptions. Now the repository itself is
   checked first: a 404, or an answer under a different name (a renamed
   repository behind a redirect), is NOT READ, and the run says it is partial.

2. `--resolve`. The App token is requested for a list of names, and one name
   GitHub cannot resolve fails the whole request (HTTP 422, four Mondays in a
   row). `--resolve` compares the wanted names with what the installation can
   see and writes only the visible ones. It must never write an empty list:
   create-github-app-token turns an empty `repositories` input plus `owner`
   into a token for every repository the App can see.

This repository is public, and so are its Actions logs, so the installation's
repository list and a redirect's target name must never reach the output.
Every name below that is not in CONSUMER_REPOS is invented.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / ".github" / "scripts" / "census_counters.py"

ORG = "thrillmade"
SELF = "thrillmade/thrill-skills"
CONSUMERS = [
    "clud-bug",
    "clud-bug-app",
    "logmind",
    "udts",
    "protocol",
    "reporulez",
    "rezgen",
    "skdd",
]

# Invented names: never a real repository.
REDIRECT_TARGET = "thrillmade/invented-renamed-target"
PRIVATE_EXTRA = "thrillmade/invented-private-neighbour"
RENAMED_SELF = "thrillmade/renamed-fixture"


# --- fake GitHub API -------------------------------------------------------


class _FakeApi:
    """Serves `routes` ({path: (status, payload)}; status 301 means payload
    is the Location). Anything unrouted is a 404, which is also what GitHub
    answers for a file a repository does not carry."""

    def __init__(self, routes: dict, delete_status: int | str = 204):
        self.routes = routes
        self.delete_status = delete_status  # an int, or "drop" to hang up unanswered
        self.seen: list[str] = []
        self.deleted: list[tuple[str, str]] = []  # (path, Authorization)
        api = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):  # noqa: N802 -- stdlib name
                path = self.path.split("?", 1)[0]
                query = self.path.split("?", 1)[1] if "?" in self.path else ""
                api.seen.append(self.path)
                key = path if path in api.routes else f"{path}?{query}"
                status, payload = api.routes.get(key, (404, {"message": "Not Found"}))
                if status == 301:
                    self.send_response(301)
                    self.send_header("Location", payload)
                    self.end_headers()
                    return
                # bytes = a raw body, for answers that are not JSON at all
                body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_DELETE(self):  # noqa: N802 -- stdlib name
                api.deleted.append((self.path, self.headers.get("Authorization", "")))
                if api.delete_status == "drop":
                    self.close_connection = True
                    return
                self.send_response(api.delete_status)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *args):  # silence the server
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def _readable(name: str) -> dict:
    return {f"/repos/{ORG}/{name}": (200, {"full_name": f"{ORG}/{name}", "name": name})}


def _counter_routes(*, unreadable=(), renamed=(), self_name=SELF) -> dict:
    routes: dict = {f"/repos/{self_name}/issues": (200, [])}
    for name in CONSUMERS:
        if name in unreadable:
            continue  # unrouted: the repository itself answers 404
        if name in renamed:
            routes[f"/repos/{ORG}/{name}"] = (301, "/repositories/4242")
            routes["/repositories/4242"] = (
                200,
                {"full_name": REDIRECT_TARGET, "name": REDIRECT_TARGET.split("/")[1]},
            )
            continue
        routes.update(_readable(name))
    return routes


def _run(args: list[str], api: _FakeApi, env_extra: dict, files: dict | None = None) -> dict:
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        for rel, content in (files or {}).items():
            (tdp / rel).parent.mkdir(parents=True, exist_ok=True)
            (tdp / rel).write_text(content, encoding="utf-8")
        out_dir = tdp / "out"
        gh_output = tdp / "github_output"
        gh_output.write_text("", encoding="utf-8")
        env = {
            k: v
            for k, v in os.environ.items()
            if k not in ("GITHUB_REPOSITORY", "STEWARD_TOKEN", "LOOKUP_TOKEN")
        }
        env.update(
            {
                "GITHUB_API_URL": api.url,
                "OUT_DIR": str(out_dir),
                "GITHUB_OUTPUT": str(gh_output),
                "GITHUB_REPOSITORY": SELF,
            }
        )
        env.update(env_extra)
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=tdp,  # no skills/ dir: an empty catalog, which is fine here
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
        census = digest = None
        if (out_dir / "census.json").exists():
            census = json.loads((out_dir / "census.json").read_text(encoding="utf-8"))
        if (out_dir / "digest.md").exists():
            digest = (out_dir / "digest.md").read_text(encoding="utf-8")
        return {
            "rc": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "log": proc.stdout + proc.stderr,
            "census": census,
            "digest": digest,
            "github_output": gh_output.read_text(encoding="utf-8"),
        }


def _count(routes: dict, files: dict | None = None) -> dict:
    with _FakeApi(routes) as api:
        return _run([], api, {"STEWARD_TOKEN": "fake-token"}, files)


def _summary_line(stdout: str) -> str:
    lines = [l for l in stdout.splitlines() if l.startswith(("ok ", "partial "))]
    assert len(lines) == 1, f"expected exactly one summary line:\n{stdout}"
    return lines[0]


# --- 1. the counters: what was read, and what was not ------------------------


def test_full_read_prints_ok_and_no_banner():
    """Control: every consumer answers under its own name."""
    out = _count(_counter_routes())
    assert out["rc"] == 0, out["log"]
    assert _summary_line(out["stdout"]).startswith("ok ")
    assert "repos_read=8/8" in _summary_line(out["stdout"])
    assert "::warning::" not in out["log"]
    assert "Partial census" not in out["digest"]
    assert out["census"]["coverage"] == {
        "consumers": 8,
        "read": 8,
        "complete": True,
        "not_read": {},
    }


def test_repo_without_lock_or_manifest_is_still_read():
    """A readable repository with no skills-lock.json, no manifest and no
    .claude/skills is read, with zero subscriptions -- the existing meaning of
    a contents 404, kept. Every contents path below is unrouted (404)."""
    out = _count(_counter_routes())
    assert out["census"]["repos"]["skdd"]["read"] is True
    assert out["census"]["repos"]["skdd"]["subscribed"] == []
    assert "| `skdd` | 0 |" in out["digest"]


def test_unreadable_repo_is_named_at_the_top_of_the_digest():
    out = _count(_counter_routes(unreadable=("rezgen",)))
    assert out["rc"] == 0, "a partial census is not a failure\n" + out["log"]

    summary = _summary_line(out["stdout"])
    assert summary.startswith("partial "), summary
    assert "repos_read=7/8" in summary
    assert "not_read=rezgen" in summary
    warnings = [l for l in out["log"].splitlines() if l.startswith("::warning::")]
    assert len(warnings) == 1, warnings
    assert "rezgen" in warnings[0] and "NOT READ" in warnings[0]

    # The digest opens with it: the line after the title.
    lines = out["digest"].splitlines()
    assert lines[0].startswith("# Skill census digest")
    banner = next(l for l in lines[1:] if l.strip())
    assert "Partial census" in banner and "read 7 of 8" in banner, banner
    assert "`rezgen`" in banner
    row = next(l for l in lines if l.startswith("| `rezgen` |"))
    assert "not read" in row, row

    assert out["census"]["coverage"]["read"] == 7
    assert out["census"]["coverage"]["complete"] is False
    assert list(out["census"]["coverage"]["not_read"]) == ["rezgen"]
    assert out["census"]["repos"]["rezgen"]["read"] is False
    # And it was never treated as a readable repo with no lock file.
    assert out["census"]["repos"]["rezgen"].get("subscribed") == []


def test_renamed_repo_is_not_read_and_its_new_name_is_never_printed():
    out = _count(_counter_routes(renamed=("protocol",)))
    assert out["rc"] == 0, out["log"]
    reason = out["census"]["coverage"]["not_read"]["protocol"]
    assert "CONSUMER_REPOS" in reason, reason
    row = next(l for l in out["digest"].splitlines() if l.startswith("| `protocol` |"))
    assert "not read" in row
    target = REDIRECT_TARGET.split("/")[1]
    for where in (out["log"], out["digest"], json.dumps(out["census"])):
        assert target not in where


def test_zero_repos_read_exits_1_with_examined_nothing():
    out = _count(_counter_routes(unreadable=tuple(CONSUMERS)))
    assert out["rc"] == 1, out["log"]
    errors = [l for l in out["log"].splitlines() if l.startswith("::error::")]
    assert len(errors) == 1, out["log"]
    assert "census examined nothing: 0 of 8" in errors[0]
    for name in CONSUMERS:
        assert name in errors[0]
    # The artifacts are still written, so the run can be inspected.
    assert out["census"]["coverage"]["read"] == 0
    assert "Partial census" in out["digest"] or "read 0 of 8" in out["digest"]
    assert not any(l.startswith("ok ") for l in out["stdout"].splitlines())


def test_partial_digest_keeps_the_title_the_closure_step_matches():
    """The workflow closes the previous digest by its exact title and single
    label; the partial banner must not move the title line."""
    out = _count(_counter_routes(unreadable=("rezgen",)))
    assert out["digest"].splitlines()[0] == f"# Skill census digest — {out['census']['cycle']}"


# --- 2. --resolve: which names the token is requested for --------------------


def _installation(*full_names: str, per_page_split: int | None = None) -> dict:
    repos = [{"full_name": n, "name": n.split("/")[1]} for n in full_names]
    if per_page_split is None:
        return {
            "/installation/repositories?per_page=100&page=1": (
                200,
                {"total_count": len(repos), "repositories": repos},
            )
        }
    first, rest = repos[:per_page_split], repos[per_page_split:]
    return {
        "/installation/repositories?per_page=100&page=1": (
            200,
            {"total_count": len(repos), "repositories": first},
        ),
        "/installation/repositories?per_page=100&page=2": (
            200,
            {"total_count": len(repos), "repositories": rest},
        ),
    }


LOOKUP_TOKEN = "fake-lookup-token-value"


def _resolve(routes: dict, *, self_name: str = SELF, delete_status: int | str = 204) -> dict:
    with _FakeApi(routes, delete_status) as api:
        out = _run(["--resolve"], api, {"LOOKUP_TOKEN": LOOKUP_TOKEN, "GITHUB_REPOSITORY": self_name})
        out["deleted"] = list(api.deleted)
        return out


def _repositories_output(github_output: str) -> list[str] | None:
    lines = [l for l in github_output.splitlines() if l.startswith("repositories=")]
    if not lines:
        return None
    assert len(lines) == 1, github_output
    return lines[0].split("=", 1)[1].split(",")


def test_resolve_full_visibility_lists_self_then_every_consumer():
    """Control."""
    out = _resolve(_installation(SELF, *(f"{ORG}/{c}" for c in CONSUMERS)))
    assert out["rc"] == 0, out["log"]
    assert _repositories_output(out["github_output"]) == [SELF] + [f"{ORG}/{c}" for c in CONSUMERS]
    assert "::warning::" not in out["log"]


def test_stale_name_is_dropped_with_a_warning_and_left_out_of_the_mint_list():
    visible = [f"{ORG}/{c}" for c in CONSUMERS if c != "udts"]
    out = _resolve(_installation(SELF, *visible))
    assert out["rc"] == 0, out["log"]
    warnings = [l for l in out["log"].splitlines() if l.startswith("::warning::")]
    assert len(warnings) == 1, warnings
    assert "udts" in warnings[0] and "NOT READ" in warnings[0]
    assert _repositories_output(out["github_output"]) == [SELF] + visible


def test_resolve_walks_every_page_of_the_installation():
    names = [SELF] + [f"{ORG}/{c}" for c in CONSUMERS]
    out = _resolve(_installation(*names, per_page_split=4))
    assert out["rc"] == 0, out["log"]
    assert _repositories_output(out["github_output"]) == names


def test_resolve_ignores_case():
    out = _resolve(_installation(SELF.upper(), *(f"{ORG}/{c}".upper() for c in CONSUMERS)))
    assert out["rc"] == 0, out["log"]
    assert _repositories_output(out["github_output"]) == [SELF] + [f"{ORG}/{c}" for c in CONSUMERS]


def test_installation_names_outside_the_list_never_reach_the_log():
    out = _resolve(_installation(PRIVATE_EXTRA, SELF, *(f"{ORG}/{c}" for c in CONSUMERS)))
    assert out["rc"] == 0
    extra = PRIVATE_EXTRA.split("/")[1]
    assert extra not in out["log"]
    assert extra not in out["github_output"]


def test_no_consumer_visible_fails_loudly_and_writes_no_output():
    """The guard that keeps the steward token narrow: an empty
    `repositories` input would widen it to every repository the App sees."""
    out = _resolve(_installation(SELF, PRIVATE_EXTRA))
    assert out["rc"] == 1, out["log"]
    assert any(l.startswith("::error::") and "examined nothing" in l for l in out["log"].splitlines()), out["log"]
    assert _repositories_output(out["github_output"]) is None
    assert out["github_output"] == ""


def test_this_repo_not_visible_fails_loudly():
    out = _resolve(_installation(*(f"{ORG}/{c}" for c in CONSUMERS)))
    assert out["rc"] == 1, out["log"]
    errors = [l for l in out["log"].splitlines() if l.startswith("::error::")]
    assert errors and SELF in errors[0] and "examined nothing" in errors[0], out["log"]
    assert out["github_output"] == ""


def test_lookup_failure_fails_loudly_and_writes_no_output():
    out = _resolve({})  # /installation/repositories unrouted: 404
    assert out["rc"] == 1, out["log"]
    assert any(l.startswith("::error::") for l in out["log"].splitlines()), out["log"]
    assert out["github_output"] == ""


def test_self_name_follows_GITHUB_REPOSITORY():
    out = _resolve(
        _installation(RENAMED_SELF, *(f"{ORG}/{c}" for c in CONSUMERS)),
        self_name=RENAMED_SELF,
    )
    assert out["rc"] == 0, out["log"]
    assert _repositories_output(out["github_output"])[0] == RENAMED_SELF


def test_counters_read_the_docket_of_the_repo_they_run_in():
    """Own name from the run context in the counters too: the docket read
    goes to GITHUB_REPOSITORY, not a literal."""
    with _FakeApi(_counter_routes(self_name=RENAMED_SELF)) as api:
        out = _run([], api, {"STEWARD_TOKEN": "t", "GITHUB_REPOSITORY": RENAMED_SELF})
        seen = list(api.seen)
    assert out["rc"] == 0, out["log"]
    assert any(p.startswith(f"/repos/{RENAMED_SELF}/issues") for p in seen), seen
    assert not any(p.startswith(f"/repos/{SELF}/") for p in seen), seen


# --- a failed lookup is a failed lookup, whatever shape it takes -------------


def _assert_failed_lookup(out: dict) -> None:
    """The documented ending of every failed lookup: one ::error::, exit 1,
    nothing written for the token step, no traceback, the token never shown."""
    assert out["rc"] == 1, out["log"]
    errors = [l for l in out["log"].splitlines() if l.startswith("::error::")]
    assert len(errors) == 1 and "examined nothing" in errors[0], out["log"]
    assert out["github_output"] == ""
    assert "Traceback" not in out["log"], out["log"]
    assert LOOKUP_TOKEN not in out["log"]


def test_truncated_installation_listing_is_a_failed_lookup():
    """The listing stopped (an empty page) before total_count names arrived.
    Reading that as "these consumers are gone" would drop live repositories
    with a stale-name warning; it is a lookup that failed."""
    names = [SELF] + [f"{ORG}/{c}" for c in CONSUMERS]
    routes = {
        "/installation/repositories?per_page=100&page=1": (
            200,
            {"total_count": len(names), "repositories": [{"full_name": n} for n in names[:4]]},
        ),
        "/installation/repositories?per_page=100&page=2": (
            200,
            {"total_count": len(names), "repositories": []},
        ),
    }
    out = _resolve(routes)
    _assert_failed_lookup(out)
    assert "::warning::" not in out["log"], "a truncated listing must not read as stale names"


def test_non_json_listing_is_a_failed_lookup():
    out = _resolve({"/installation/repositories?per_page=100&page=1": (200, b"<html>bad gateway</html>")})
    _assert_failed_lookup(out)


def test_undecodable_listing_is_a_failed_lookup():
    out = _resolve({"/installation/repositories?per_page=100&page=1": (200, b"\xff\xfe\xfa not utf-8")})
    _assert_failed_lookup(out)


def test_a_timeout_is_reported_as_a_lookup_failure(monkeypatch):
    """A read timeout surfaces from urlopen as TimeoutError, which is neither
    an HTTPError nor a URLError; it must still reach the caller as the
    token-free RuntimeError every failed request becomes."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("census_counters_timeout", SCRIPT)
    cc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cc)

    def timeout(*args, **kwargs):
        raise TimeoutError("The read operation timed out")

    monkeypatch.setattr(cc.urllib.request, "urlopen", timeout)
    try:
        cc._request("installation/repositories?per_page=100&page=1", "secret-token")
    except RuntimeError as exc:
        assert "secret-token" not in str(exc)
        assert "installation/repositories" in str(exc)
    else:
        raise AssertionError("a timeout was not raised as RuntimeError")


# --- the lookup token is revoked as soon as the listing is done -------------


def _revoked(out: dict) -> bool:
    return ("/installation/token", f"Bearer {LOOKUP_TOKEN}") in out["deleted"]


def test_lookup_token_is_revoked_after_a_successful_listing():
    out = _resolve(_installation(SELF, *(f"{ORG}/{c}" for c in CONSUMERS)))
    assert out["rc"] == 0, out["log"]
    assert _revoked(out), out["deleted"]


def test_lookup_token_is_revoked_after_a_failed_listing():
    out = _resolve({})
    assert out["rc"] == 1
    assert _revoked(out), out["deleted"]


def test_lookup_token_is_revoked_when_nothing_is_visible():
    out = _resolve(_installation(SELF))
    assert out["rc"] == 1
    assert _revoked(out), out["deleted"]


# --- a partial census makes no finding about what it did not read ------------

PLACEMENT = json.dumps(
    {"skills": {"invented-skill": {"subscribers": ["rezgen", "skdd"]}}}
)
CATALOG_FILES = {"skills/invented-skill/SKILL.md": "x", "docs/placement-map.json": PLACEMENT}


def _section(digest: str, heading: str) -> list[str]:
    lines = digest.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith(heading))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("#")), len(lines))
    return lines[start:end]


def test_placement_never_reports_an_unread_repo_as_missing():
    out = _count(_counter_routes(unreadable=("rezgen",)), CATALOG_FILES)
    assert out["rc"] == 0, out["log"]
    [div] = out["census"]["signals"]["placement_divergence"]["divergences"]
    assert div["missing"] == ["skdd"], div
    section = _section(out["digest"], "## Placement divergence")
    [finding] = [l for l in section if l.startswith("- `invented-skill`")]
    assert finding == "- `invented-skill` — declared-but-not-observed: `skdd`", finding
    # Named once, as NOT checked because not read — never as a finding.
    [not_checked] = [l for l in section if "rezgen" in l]
    assert "NOT checked" in not_checked and "not read" in not_checked, not_checked


def test_placement_control_lists_both_when_both_are_read():
    out = _count(_counter_routes(), CATALOG_FILES)
    [div] = out["census"]["signals"]["placement_divergence"]["divergences"]
    assert div["missing"] == ["rezgen", "skdd"]


def test_unsubscribed_section_says_it_is_partial_in_its_own_first_line():
    out = _count(_counter_routes(unreadable=("rezgen",)), CATALOG_FILES)
    section = [l for l in _section(out["digest"], "### Unsubscribed catalog skills") if l.strip()]
    assert "read 7 of 8" in section[1] and "partial" in section[1].lower(), section[:3]


def test_unsubscribed_section_has_no_partial_note_on_a_full_read():
    out = _count(_counter_routes(), CATALOG_FILES)
    section = "\n".join(_section(out["digest"], "### Unsubscribed catalog skills"))
    assert "partial" not in section.lower()


def test_unsubscribed_counts_come_only_from_read_repos():
    """An unread record is never a subscriber, even if it carries data."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("census_counters_signals", SCRIPT)
    cc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cc)
    repos = {
        "skdd": {"read": True, "subscribed": [], "local": ["shared"]},
        "rezgen": {"read": False, "subscribed": ["invented-skill"], "local": ["shared"]},
    }
    signals = cc.compute_signals(["invented-skill"], repos)
    assert [s["name"] for s in signals["unsubscribed_catalog_skills"]] == ["invented-skill"]
    assert signals["convergent_local"] == []


def test_a_non_json_body_is_reported_as_a_request_failure(monkeypatch):
    """The request layer on its own (resolve() also catches everything, so the
    end-to-end tests above hold if either layer does): a body that is not
    JSON becomes the same token-free RuntimeError, which the counters'
    per-repo collection reports as that repo's error."""
    import importlib.util
    import io

    spec = importlib.util.spec_from_file_location("census_counters_nonjson", SCRIPT)
    cc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cc)

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(cc.urllib.request, "urlopen", lambda *a, **k: _Resp(b"<html>bad gateway</html>"))
    try:
        cc._request("repos/thrillmade/invented-consumer", "secret-token")
    except RuntimeError as exc:
        assert "secret-token" not in str(exc) and "repos/thrillmade/invented-consumer" in str(exc)
    else:
        raise AssertionError("a non-JSON body was not raised as RuntimeError")


# --- a failed revoke costs one warning, never the run, never the token -------


def _assert_failed_revoke_is_harmless(out: dict) -> None:
    assert out["rc"] == 0, out["log"]
    assert _revoked(out), "the revoke was not attempted"
    assert _repositories_output(out["github_output"]) == [SELF] + [f"{ORG}/{c}" for c in CONSUMERS]
    warnings = [l for l in out["log"].splitlines() if l.startswith("::warning::")]
    assert len(warnings) == 1 and "revoke" in warnings[0], out["log"]
    assert "Traceback" not in out["log"]
    assert LOOKUP_TOKEN not in out["log"]


def test_a_revoke_answered_500_is_one_warning():
    out = _resolve(_installation(SELF, *(f"{ORG}/{c}" for c in CONSUMERS)), delete_status=500)
    _assert_failed_revoke_is_harmless(out)


def test_a_revoke_left_unanswered_is_one_warning():
    """The server hangs up without answering -- the cheap stand-in for a
    revoke that never completes (a real timeout would cost API_TIMEOUT)."""
    out = _resolve(_installation(SELF, *(f"{ORG}/{c}" for c in CONSUMERS)), delete_status="drop")
    _assert_failed_revoke_is_harmless(out)


def test_an_http_protocol_error_is_reported_as_a_request_failure(monkeypatch):
    """http.client errors (IncompleteRead, BadStatusLine) are neither OSError
    nor ValueError; they too must become the token-free RuntimeError."""
    import http.client
    import importlib.util

    spec = importlib.util.spec_from_file_location("census_counters_httpexc", SCRIPT)
    cc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cc)

    def incomplete(*args, **kwargs):
        raise http.client.IncompleteRead(b"partial")

    monkeypatch.setattr(cc.urllib.request, "urlopen", incomplete)
    try:
        cc._request("repos/thrillmade/invented-consumer", "secret-token")
    except RuntimeError as exc:
        assert "secret-token" not in str(exc) and "repos/thrillmade/invented-consumer" in str(exc)
    else:
        raise AssertionError("IncompleteRead escaped _request unwrapped")


# --- one definition of "read" ------------------------------------------------


def _module(tag: str):
    import importlib.util

    spec = importlib.util.spec_from_file_location(f"census_counters_{tag}", SCRIPT)
    cc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cc)
    return cc


def test_a_record_without_a_read_key_is_unread_everywhere():
    """Coverage and the signals use one definition, the conservative one: a
    record that does not say `read: True` was not read, so it is neither
    counted as covered nor as a subscriber, local skill or usage source."""
    cc = _module("readkey")
    repos = {
        "skdd": {
            "subscribed": ["invented-skill"],
            "local": ["shared"],
            "usage": {"invented-skill": {"loads": 3, "citations": 2, "last_cited": None}},
        },
        "rezgen": {"read": True, "subscribed": [], "local": ["shared"]},
    }
    assert "skdd" in cc.compute_coverage(repos)["not_read"]
    signals = cc.compute_signals(["invented-skill"], repos)
    assert [s["name"] for s in signals["unsubscribed_catalog_skills"]] == ["invented-skill"]
    assert signals["convergent_local"] == []
    assert cc.aggregate_usage(repos)["present"] is False


def _placement_digest(cc, repos: dict, placement: dict, coverage: dict) -> str:
    signals = cc.compute_signals([], repos)
    signals["placement_divergence"] = cc.compute_placement_divergence(placement, repos)
    census = {
        "cycle": "census-2026-W47",
        "generated_at": "2026-11-16T12:00:00+00:00",
        "coverage": coverage,
        "repos": repos,
        "signals": signals,
        "stale_docket": {"open_count": 0, "stale_count": 0, "stale": []},
    }
    return "\n".join(_section(cc.render_digest(census), "## Placement divergence"))


def test_an_unread_record_is_never_observed_as_a_subscriber():
    """An unread record carries no evidence even if it carries data: it must
    not turn up as observed-but-not-declared."""
    cc = _module("observed")
    repos = {
        "skdd": {"read": True, "subscribed": ["invented-skill"]},
        "rezgen": {"read": False, "not_read": "x", "subscribed": ["invented-skill"]},
    }
    placement = {"skills": {"invented-skill": {"subscribers": ["skdd"]}}}
    coverage = {"consumers": 2, "read": 1, "complete": False, "not_read": {"rezgen": "x"}}
    section = _placement_digest(cc, repos, placement, coverage)
    assert "observed-but-not-declared" not in section, section


# --- the placement section never gives a partial census an all-clear --------

ALL_CLEAR = "_Placement map agrees with live subscriptions — no divergence._"


def _consumers_read(read_names: set, subscribed: dict) -> dict:
    repos = {}
    for name in CONSUMERS:
        if name in read_names:
            repos[name] = {"read": True, "subscribed": subscribed.get(name, [])}
        else:
            repos[name] = {"read": False, "not_read": "x", "subscribed": []}
    return repos


def _coverage(repos: dict) -> dict:
    not_read = {n: "x" for n, r in repos.items() if not r["read"]}
    return {"consumers": len(repos), "read": len(repos) - len(not_read), "complete": not not_read, "not_read": not_read}


def test_partial_placement_with_no_divergence_is_qualified_and_names_what_was_not_checked():
    cc = _module("placement_partial")
    read = set(CONSUMERS) - {"rezgen"}
    repos = _consumers_read(read, {"skdd": ["invented-skill"]})
    placement = {"skills": {"invented-skill": {"subscribers": ["skdd", "rezgen"]}}}
    section = _placement_digest(cc, repos, placement, _coverage(repos))
    assert ALL_CLEAR not in section, section
    assert "_No divergence found among the 7 repositories read._" in section, section
    [not_checked] = [l for l in section.splitlines() if "NOT checked" in l]
    assert "`rezgen`" in not_checked
    assert "declared-but-not-observed" not in section


def test_full_placement_section_is_unchanged():
    """Byte-identical to the section as it was before partial coverage
    existed: the all-clear, and a finding line, exactly."""
    cc = _module("placement_full")
    repos = _consumers_read(set(CONSUMERS), {"skdd": ["invented-skill"]})
    agree = {"skills": {"invented-skill": {"subscribers": ["skdd"]}}}
    assert _placement_digest(cc, repos, agree, _coverage(repos)) == (
        "## Placement divergence\n\n" + ALL_CLEAR + "\n"
    )
    diverge = {"skills": {"invented-skill": {"subscribers": ["rezgen"]}}}
    assert _placement_digest(cc, repos, diverge, _coverage(repos)) == (
        "## Placement divergence\n\n"
        "- `invented-skill` — declared-but-not-observed: `rezgen`; observed-but-not-declared: `skdd`\n"
    )
