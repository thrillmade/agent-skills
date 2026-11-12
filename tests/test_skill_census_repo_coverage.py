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

    def __init__(self, routes: dict):
        self.routes = routes
        self.seen: list[str] = []
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
                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

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


def _run(args: list[str], api: _FakeApi, env_extra: dict) -> dict:
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
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


def _count(routes: dict) -> dict:
    with _FakeApi(routes) as api:
        return _run([], api, {"STEWARD_TOKEN": "fake-token"})


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


def _resolve(routes: dict, *, self_name: str = SELF) -> dict:
    with _FakeApi(routes) as api:
        return _run(["--resolve"], api, {"LOOKUP_TOKEN": "fake-lookup", "GITHUB_REPOSITORY": self_name})


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
