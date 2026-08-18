"""`.github/scripts/stamp_versions.py` -- the only thing that writes a stamp.

`restamp` re-checks, on every file, what `skill_version.stamp` promises: the
body comes out byte-identical, `name` and `description` survive, the result
re-parses, and the stamp is a fixed point. Those assertions exist to catch a
future regression in `stamp`, which means nothing about them fails today --
deleting every one of them leaves the suite green unless something reaches in
and breaks `stamp` too. So that is what these tests do.

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
    assert skill_version.stamped_value(out) == skill_version.digest(BASE)


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


def test_restamp_refuses_a_one_time_unquoting_sabotage(monkeypatch) -> None:
    """Drop the quotes on the FIRST call only and the YAML value is still the
    right digest, so the re-parse check above is satisfied. This is the shape
    the fixed-point assertion below was mutation-tested against before it was
    deleted: `new` itself is malformed (unquoted), so `stamped_value(new)`
    disagrees with `digest(new)` and the fixed-point assertion fires first --
    idempotence never gets a turn.

    A one-time sabotage is a narrower case than a real regression, though --
    see `test_restamp_refuses_a_persistent_unquoting_regression` below for
    the shape that was missed.
    """
    def unquote(out: bytes, raw: bytes) -> bytes:
        d = skill_version.digest(out).encode()
        return out.replace(b'version: "' + d + b'"', b"version: " + d)

    _sabotage(monkeypatch, unquote)
    with pytest.raises(AssertionError, match="not a fixed point"):
        stamp_versions.restamp(BASE)


def test_restamp_refuses_a_persistent_unquoting_regression(monkeypatch) -> None:
    """A regression inside `version_line` itself -- not at the `stamp` call
    site -- fires on EVERY call, including the idempotence self-check two
    lines below. Both sides of `stamp(new) == new` come out unquoted the same
    way and agree with each other while both are wrong, so idempotence is
    blind to it.

    Only the fixed-point assertion (`stamped_value(new) == digest(new)`)
    catches this: `stamped_value` reads the STRICT, quote-requiring
    `STAMP_RE` and comes back `None` for an unquoted line. This is the
    assertion `cbb3eff` deleted on the strength of a mutation that sabotaged
    `stamp` only once -- a one-time sabotage is exactly the shape idempotence
    *does* catch, so it proved nothing about a persistent one.
    """
    def unquoted_version_line(value: str) -> str:
        return f"version: {value}  {skill_version.COMMENT}"

    monkeypatch.setattr(skill_version, "version_line", unquoted_version_line)

    # Control: under the regression, idempotence alone does NOT notice --
    # both calls to `stamp` are corrupted the same persistent way.
    new = skill_version.stamp(BASE)
    assert skill_version.stamp(new) == new  # "idempotent" and still wrong
    assert skill_version.stamped_value(new) is None
    assert skill_version.digest(new) is not None

    with pytest.raises(AssertionError, match="not a fixed point"):
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
    assert "no `version:` line" in p.stdout


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
    (d / "SKILL.md").write_bytes(stamped.replace(line, line + b'\nversion: "deadbeefcafe"'))
    p = _run("--check", cwd=tmp_path)
    assert p.returncode == 1, p.stdout
    assert "2 `version:` lines" in p.stdout
