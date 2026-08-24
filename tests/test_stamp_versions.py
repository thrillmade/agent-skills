"""`.github/scripts/stamp_versions.py` -- the only thing that writes a stamp.

`restamp` re-checks, on every file, what `skill_version.stamp` promises: the
body comes out byte-identical, `name` and `description` survive, all three
identity lines re-parse, and each is its own fixed point. Those assertions
exist to catch a future regression in `stamp`, which means nothing about them
fails today -- deleting every one of them leaves the suite green unless
something reaches in and breaks `stamp` too. So that is what these tests do.

Without them the assertions are decoration: a mutation run flipped
`assert new_body == old_body` to `pass` and 814 tests still passed.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import skill_version
import stamp_versions

from conftest import SCRIPTS

REPO = SCRIPTS.parents[1]

BASE = b"""---
name: alpha
description: What this skill does.
---

# Title

Body.
"""


def test_restamp_stamps_a_clean_file() -> None:
    out = stamp_versions.restamp(BASE)
    assert skill_version.stamped_digest(out) == skill_version.digest(BASE)
    assert skill_version.stamped_version(out) == "1.0.0"
    assert skill_version.stamped_origin(out) == skill_version.ORIGIN


def _sabotage(monkeypatch, corrupt) -> None:
    """Replace `stamp` with one that corrupts its output -- ONCE.

    Two things bite here. `stamp_versions.skill_version` and `skill_version`
    are the same module object, so the replacement has to close over the
    ORIGINAL function or it recurses forever. And `restamp` calls `stamp`
    twice -- once to produce the file, once to check idempotence -- so a
    sabotage that fires on every call corrupts both sides of that comparison
    and they agree again. The idempotence test passed for that reason before
    the counter was added.
    """
    real = skill_version.stamp
    calls = {"n": 0}

    def patched(raw: bytes) -> bytes:
        calls["n"] += 1
        out = real(raw)
        return corrupt(out, raw) if calls["n"] == 1 else out

    monkeypatch.setattr(stamp_versions.skill_version, "stamp", patched)


def test_restamp_refuses_a_stamp_that_changed_the_body(monkeypatch) -> None:
    _sabotage(monkeypatch, lambda out, raw: out.replace(b"Body.", b"Bodyx"))
    with pytest.raises(AssertionError, match="stamping changed the body"):
        stamp_versions.restamp(BASE)


def test_restamp_refuses_a_stamp_that_changed_the_description(monkeypatch) -> None:
    _sabotage(monkeypatch, lambda out, raw: out.replace(
        b"description: What this skill does.", b"description: Something else."
    ))
    with pytest.raises(AssertionError, match="stamping changed `description`"):
        stamp_versions.restamp(BASE)


def test_restamp_refuses_a_stamp_that_changed_the_name(monkeypatch) -> None:
    _sabotage(monkeypatch, lambda out, raw: out.replace(b"name: alpha", b"name: beta"))
    with pytest.raises(AssertionError, match="stamping changed `name`"):
        stamp_versions.restamp(BASE)


def test_restamp_refuses_a_stamp_that_drops_origin(monkeypatch) -> None:
    _sabotage(monkeypatch, lambda out, raw: out.replace(
        f"origin: {skill_version.ORIGIN}".encode(), b"origin: https://example.invalid"
    ))
    with pytest.raises(AssertionError, match="origin does not re-parse"):
        stamp_versions.restamp(BASE)


def test_restamp_refuses_a_one_time_unquoting_sabotage_on_digest(monkeypatch) -> None:
    """Drop the quotes on the digest line on the FIRST call only and the YAML
    value is still the right hash, so the re-parse check above is satisfied.
    This is the shape the fixed-point assertion below was mutation-tested
    against before it was deleted: `new` itself is malformed (unquoted), so
    `stamped_digest(new)` disagrees with `digest(new)` and the fixed-point
    assertion fires first -- idempotence never gets a turn.

    A one-time sabotage is a narrower case than a real regression, though --
    see `test_restamp_refuses_a_persistent_unquoting_regression` below for
    the shape that was missed.
    """
    def unquote(out: bytes, raw: bytes) -> bytes:
        d = skill_version.digest(out).encode()
        return out.replace(b'digest: "' + d + b'"', b"digest: " + d)

    _sabotage(monkeypatch, unquote)
    with pytest.raises(AssertionError, match="digest is not a fixed point"):
        stamp_versions.restamp(BASE)


def test_restamp_refuses_a_persistent_unquoting_regression(monkeypatch) -> None:
    """A regression inside `version_line` itself -- not at the `stamp` call
    site -- fires on EVERY call, including the idempotence self-check two
    lines below. `stamped_version` reads the unquoted line as no claim at
    all, and "no claim" is exactly the case `stamp()` seeds at the constant
    "1.0.0" -- so a persistently unquoted generator converges on repeated
    calls (unlike a persistently unquoted `digest_line`, which would instead
    bump PATCH forever and so trips idempotence on its own; this is the
    quieter shape, the one idempotence is blind to).

    The re-parse assertion (`new_meta.get("version") == stamped_version(new)`)
    catches this first: YAML reads the unquoted `version: 1.0.0` as the
    string `"1.0.0"`, but `stamped_version` reads the STRICT, quote-requiring
    `SEMVER_RE` and comes back `None` for the same line -- the two disagree,
    so `restamp` refuses. This is the shape a mutation once deleted a
    fixed-point-style assertion on the strength of testing only a one-time
    sabotage -- a one-time sabotage is exactly the shape idempotence *does*
    catch, so it proved nothing about a persistent one.
    """
    def unquoted_version_line(value: str) -> str:
        return f"version: {value}"

    monkeypatch.setattr(skill_version, "version_line", unquoted_version_line)

    # Control: under the regression, idempotence alone does NOT notice --
    # both calls to `stamp` converge on the same wrong, unquoted "1.0.0".
    new = skill_version.stamp(BASE)
    assert skill_version.stamp(new) == new  # "idempotent" and still wrong
    assert skill_version.stamped_version(new) is None
    assert skill_version.stamped_digest(new) == skill_version.digest(new)

    with pytest.raises(AssertionError, match="version does not re-parse"):
        stamp_versions.restamp(BASE)


def test_restamp_refuses_a_version_line_that_reparses_as_none(monkeypatch) -> None:
    """The shape the re-parse assertion, by itself, is BLIND to: `version:`
    with no value at all. YAML reads that as Python `None`, and
    `stamped_version` -- which requires `SEMVER_RE` to match -- ALSO reads it
    as `None`, so `new_meta.get("version") == stamped_version(new)` passes
    (`None == None`) even though nothing was actually stamped. Only the
    fixed-point assertion, which insists on `is not None`, catches it -- this
    is the case that justifies it being a SEPARATE assertion rather than
    folded into the re-parse check above.
    """
    monkeypatch.setattr(skill_version, "version_line", lambda value: "version:")
    with pytest.raises(AssertionError, match="version is not a fixed point"):
        stamp_versions.restamp(BASE)


# --- the CLI ---------------------------------------------------------------


def _run(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    """No pipe -- the exit code comes from the process."""
    return subprocess.run(
        [sys.executable, str(SCRIPTS / "stamp_versions.py"), *args],
        cwd=cwd, capture_output=True, text=True,
    )


def test_check_passes_on_the_shipped_catalog() -> None:
    p = _run("--check", cwd=REPO)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "stamps match their file's content digest" in p.stdout


def test_check_fails_on_an_unstamped_tree(tmp_path: Path) -> None:
    d = tmp_path / "skills" / "alpha"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_bytes(BASE)
    p = _run("--check", cwd=tmp_path)
    assert p.returncode == 1, p.stdout
    assert "0 `version:` line(s), 0 `digest:` line(s), 0 `origin:` line(s)" in p.stdout


def test_write_then_check_is_clean(tmp_path: Path) -> None:
    d = tmp_path / "skills" / "alpha"
    d.mkdir(parents=True)
    (d / "SKILL.md").write_bytes(BASE)
    assert _run("--write", cwd=tmp_path).returncode == 0
    assert (d / "SKILL.md").read_bytes() != BASE  # the mutation landed
    assert _run("--check", cwd=tmp_path).returncode == 0


def test_a_run_that_found_no_skills_fails_rather_than_reporting_success(
    tmp_path: Path,
) -> None:
    """The walk is cwd-relative. A run from the wrong directory stamps nothing
    and would otherwise print a clean bill of health over zero files.
    """
    p = _run("--check", cwd=tmp_path)
    assert p.returncode == 1, p.stdout
    assert "no SKILL.md files under" in p.stdout


def test_check_reports_a_duplicate_version_line(tmp_path: Path) -> None:
    d = tmp_path / "skills" / "alpha"
    d.mkdir(parents=True)
    stamped = skill_version.stamp(BASE)
    line = skill_version.version_lines(stamped)[0].encode()
    (d / "SKILL.md").write_bytes(stamped.replace(line, line + b'\nversion: "9.9.9"'))
    p = _run("--check", cwd=tmp_path)
    assert p.returncode == 1, p.stdout
    assert "2 `version:` line(s)" in p.stdout


def test_check_reports_a_stale_digest_by_name(tmp_path: Path) -> None:
    d = tmp_path / "skills" / "alpha"
    d.mkdir(parents=True)
    stamped = skill_version.stamp(BASE)
    edited = stamped.replace(b"Body.", b"Bodyx.")  # digest now stale
    (d / "SKILL.md").write_bytes(edited)
    p = _run("--check", cwd=tmp_path)
    assert p.returncode == 1, p.stdout
    assert "`digest` claims" in p.stdout
    assert "`version` claims" in p.stdout  # PATCH is stale too -- same edit
