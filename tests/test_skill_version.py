"""Characterize `.github/scripts/skill_version.py` -- the content-identity rule.

The rule a subscriber has to be able to re-derive from their own bytes, with
no catalog access and no tooling beyond `sha256`:

    normalise CRLF -> LF, delete the `version:` line from the frontmatter,
    sha256 the remaining bytes, take the first 12 hex characters.

Everything below is about the two ways that rule can be silently wrong:
elision that is not invariant (so the same content digests differently
depending on what the stamp already said), and a reader that disagrees with
the YAML parser about which `version:` is the file's version.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
import yaml

import skill_version

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILLS = REPO_ROOT / "skills"

BASE = b"""---
name: alpha
description: What this skill does.
---

# Title

Body.
"""


def _with(front_extra: bytes = b"", body: bytes = b"") -> bytes:
    out = BASE.replace(b"description: What this skill does.\n",
                       b"description: What this skill does.\n" + front_extra)
    return out + body


# --- the rule itself -------------------------------------------------------


def test_digest_is_twelve_lowercase_hex():
    d = skill_version.digest(BASE)
    assert re.fullmatch(r"[0-9a-f]{12}", d), d


def test_digest_is_the_documented_construction():
    """Retypable from memory, and this asserts the memory is right: the
    digest of an unstamped file is just sha256 of its bytes, truncated.
    """
    assert skill_version.digest(BASE) == hashlib.sha256(BASE).hexdigest()[:12]


def test_digest_changes_when_the_body_changes():
    assert skill_version.digest(BASE) != skill_version.digest(BASE + b"x")


def test_digest_changes_when_the_description_changes():
    """`description` is the trigger surface -- a body-only digest would call
    a file with a rewritten description "current". It is not.
    """
    other = BASE.replace(b"What this skill does.", b"What this skill does!")
    assert len(other) == len(BASE)
    assert skill_version.digest(other) != skill_version.digest(BASE)


def test_digest_changes_when_a_frontmatter_key_is_added():
    assert skill_version.digest(_with(b"kind: rule\n")) != skill_version.digest(BASE)


# --- elision invariance ----------------------------------------------------
#
# Every shape of `version:` line -- correct, unquoted, garbage, absent --
# must yield the SAME digest. Otherwise the error message printed on a
# malformed stamp names a value that is itself wrong.

MALFORMED = [
    b'version: "e606dd248a0a"\n',
    b"version: e606dd248a0a\n",
    b"version: banana\n",
    b'version: "abc123"\n',
    b"version:\n",
    b'version:   "000000000000"   \n',
]


@pytest.mark.parametrize("line", MALFORMED)
def test_every_version_line_shape_elides_to_the_same_digest(line):
    assert skill_version.digest(_with(line)) == skill_version.digest(BASE)


def test_elision_is_frontmatter_only():
    """An indented `metadata.version` -- or a `version:` line in the BODY --
    is somebody else's field and must survive into the hash.

    The assertion is that CHANGING the nested value changes the digest, not
    merely that adding the block does. Anchoring elision to column 0 is what
    makes that true, and a version of this test that only compared against
    `BASE` passed with the anchor relaxed to `^[ \\t]*version:` -- the nested
    line was being eaten and the surviving `metadata:` line still made the
    two files differ.
    """
    three = _with(b"metadata:\n  version: 3\n")
    four = _with(b"metadata:\n  version: 4\n")
    assert skill_version.digest(three) != skill_version.digest(four)
    assert skill_version.digest(three) != skill_version.digest(BASE)

    body_three = BASE + b"\nversion: 3\n"
    body_four = BASE + b"\nversion: 4\n"
    assert skill_version.digest(body_three) != skill_version.digest(body_four)
    assert skill_version.digest(body_three) != skill_version.digest(BASE)


def test_crlf_input_digests_the_same_as_lf():
    crlf = BASE.replace(b"\n", b"\r\n")
    assert b"\r\n" in crlf
    assert skill_version.digest(crlf) == skill_version.digest(BASE)


def test_no_frontmatter_still_digests():
    raw = b"# Title\n\nBody.\n"
    assert skill_version.digest(raw) == hashlib.sha256(raw).hexdigest()[:12]


# --- stamping --------------------------------------------------------------


def test_stamp_is_a_fixed_point():
    stamped = skill_version.stamp(BASE)
    assert skill_version.digest(stamped) == skill_version.digest(BASE)
    assert skill_version.stamped_value(stamped) == skill_version.digest(BASE)


def test_stamp_is_idempotent():
    once = skill_version.stamp(BASE)
    assert skill_version.stamp(once) == once


def test_stamp_replaces_an_existing_wrong_stamp():
    wrong = _with(b'version: "deadbeefcafe"\n')
    assert skill_version.stamped_value(skill_version.stamp(wrong)) == skill_version.digest(BASE)


def test_stamp_leaves_the_body_byte_identical():
    stamped = skill_version.stamp(BASE)
    assert stamped.split(b"\n---\n", 1)[1] == BASE.split(b"\n---\n", 1)[1]


def test_stamp_refuses_a_file_with_no_frontmatter():
    with pytest.raises(ValueError):
        skill_version.stamp(b"# Title\n")


def test_stamped_file_still_parses_as_yaml_with_name_and_description():
    stamped = skill_version.stamp(BASE)
    front = skill_version.FRONTMATTER_RE.match(stamped).group(1)
    meta = yaml.safe_load(front)
    assert meta["name"] == "alpha"
    assert meta["description"] == "What this skill does."


# --- the quotes, and why they are not optional -----------------------------


def test_unquoted_all_digit_digest_is_coerced_by_yaml():
    """The landmine the quotes exist for. `766941312459` is a REAL historical
    digest (arlyn-delivery's installed frontend-a11y), and unquoted it stops
    being a string; `000000123456` is read as octal and does not round-trip.
    """
    assert yaml.safe_load("version: 766941312459") == {"version": 766941312459}
    assert yaml.safe_load("version: 000000123456") == {"version": 42798}


def test_unquoted_stamp_is_not_a_valid_stamp():
    assert skill_version.stamped_value(_with(b"version: e606dd248a0a\n")) is None


@pytest.mark.parametrize(
    "line",
    [
        b"version: banana\n",
        b'version: "abc123"\n',
        b'version: "E606DD248A0A"\n',
        b"version:\n",
        b"version: 766941312459\n",
    ],
)
def test_malformed_stamps_read_as_absent(line):
    assert skill_version.stamped_value(_with(line)) is None


def test_the_generated_line_is_what_stamp_writes():
    d = skill_version.digest(BASE)
    stamped = skill_version.stamp(BASE)
    assert skill_version.version_line(d).encode() + b"\n" in stamped


def test_the_generated_line_carries_a_route_home():
    """The one thing a human holding a hand-copied file has no other way to
    learn. If this string stops being a resolvable coordinate the line is
    decoration.
    """
    line = skill_version.version_line("e606dd248a0a")
    assert "github.com/thrillmade/agent-skills" in line
    assert "skill-versions.json" in line
    assert line.startswith('version: "e606dd248a0a"')
    assert "\n" not in line


# --- the duplicate-key bypass (C2) -----------------------------------------
#
# Two `version:` lines, one true and one false. A reader that takes the
# first and a YAML parser that takes the last disagree, and the gate passes
# on a file whose identity every downstream tool reads differently.


def test_two_version_lines_read_as_absent_not_as_the_first():
    d = skill_version.digest(BASE)
    dupe = _with(f'version: "{d}"\n'.encode() + b'version: "deadbeefcafe"\n')
    # the trap: a `search`-based reader answers with the FIRST, which is
    # the correct digest, and the file sails through.
    assert skill_version.STAMP_RE.search(dupe).group(1).decode() == d
    # and PyYAML -- i.e. every agent and every tool -- answers with the LAST.
    front = skill_version.FRONTMATTER_RE.match(dupe).group(1)
    assert yaml.safe_load(front)["version"] == "deadbeefcafe"
    # so the reader must refuse to answer at all.
    assert skill_version.stamped_value(dupe) is None
    assert skill_version.version_line_count(dupe) == 2


def test_a_second_malformed_version_line_also_reads_as_absent():
    """The strict count alone is not enough: one well-formed stamp plus one
    malformed line leaves `findall` at exactly one strict match while YAML
    still reads the other. The count that has to be one is the PERMISSIVE one.
    """
    d = skill_version.digest(BASE)
    dupe = _with(f'version: "{d}"\n'.encode() + b"version: banana\n")
    assert len(skill_version.STAMP_RE.findall(dupe)) == 1
    front = skill_version.FRONTMATTER_RE.match(dupe).group(1)
    assert yaml.safe_load(front)["version"] == "banana"
    assert skill_version.stamped_value(dupe) is None


def test_duplicate_lines_do_not_change_the_digest():
    """Both are elided, so the expected value printed at a duplicate is the
    same one printed at a missing stamp -- the message cannot be wrong.
    """
    d = skill_version.digest(BASE)
    dupe = _with(f'version: "{d}"\n'.encode() + b'version: "deadbeefcafe"\n')
    assert skill_version.digest(dupe) == d


def test_a_version_line_in_the_body_is_not_counted():
    assert skill_version.version_line_count(BASE + b"\nversion: 2\n") == 0


# --- the real tree ---------------------------------------------------------


def _catalog_files():
    return sorted(SKILLS.glob("*/SKILL.md"))


def test_the_catalog_has_skills_to_check():
    """Control for every zero below."""
    assert len(_catalog_files()) >= 40


@pytest.mark.parametrize("path", _catalog_files(), ids=lambda p: p.parent.name)
def test_every_catalog_skill_is_stamped_with_its_own_digest(path):
    raw = path.read_bytes()
    assert skill_version.stamped_value(raw) == skill_version.digest(raw)


@pytest.mark.parametrize("path", _catalog_files(), ids=lambda p: p.parent.name)
def test_stamping_every_catalog_skill_is_a_no_op(path):
    raw = path.read_bytes()
    assert skill_version.stamp(raw) == raw


@pytest.mark.parametrize("path", _catalog_files(), ids=lambda p: p.parent.name)
def test_no_catalog_file_contains_a_carriage_return(path):
    assert b"\r" not in path.read_bytes()
