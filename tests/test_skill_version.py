"""Characterize `.github/scripts/skill_version.py` -- the content-identity rule.

The digest rule a subscriber has to be able to re-derive from their own
bytes, with no catalog access and no tooling beyond `sha256`:

    normalise CRLF -> LF, delete the `version:`, `digest:` and `origin:`
    lines from the frontmatter, sha256 the remaining bytes, take the first
    12 hex characters.

Everything below is about the two ways that rule can be silently wrong:
elision that is not invariant (so the same content digests differently
depending on what the three stamps already said), and a reader that
disagrees with the YAML parser about which line of a duplicated field is the
file's claim -- for any of the three fields, not just the one that used to
exist. A third section characterizes `stamp()`'s semver decision, the one
piece of this module that is not a pure function of the bytes alone.
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


# --- the digest rule itself --------------------------------------------------


def test_digest_is_twelve_lowercase_hex():
    d = skill_version.digest(BASE)
    assert re.fullmatch(r"[0-9a-f]{12}", d), d


def test_digest_is_the_documented_construction():
    """Retypable from memory, and this asserts the memory is right: the
    digest of a file with none of the three identity lines is just sha256 of
    its bytes, truncated.
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


# --- elision invariance ------------------------------------------------------
#
# Every shape of a `version:`/`digest:`/`origin:` line -- correct, unquoted,
# garbage, absent -- must yield the SAME digest for the rest of the file.
# Otherwise stamping (which rewrites all three) would change the very value
# it is supposed to hold stable, and the expected value an error message
# names would itself be wrong.

MALFORMED = [
    b'version: "1.4.2"\n',
    b"version: 1.4.2\n",
    b"version: banana\n",
    b'digest: "e606dd248a0a"\n',
    b"digest: e606dd248a0a\n",
    b"digest: banana\n",
    b'digest: "abc123"\n',
    b"digest:\n",
    b'digest:   "000000000000"   \n',
    b"origin: https://example.invalid\n",
    b"origin:\n",
]


@pytest.mark.parametrize("line", MALFORMED)
def test_every_identity_line_shape_elides_to_the_same_digest(line):
    assert skill_version.digest(_with(line)) == skill_version.digest(BASE)


def test_all_three_fields_together_elide_to_the_same_digest():
    block = b'version: "1.0.0"\ndigest: "aaaaaaaaaaaa"\norigin: https://x\n'
    assert skill_version.digest(_with(block)) == skill_version.digest(BASE)


def test_elision_is_frontmatter_only():
    """An indented `metadata.version` -- or a `version:` line in the BODY --
    is somebody else's field and must survive into the hash. Same for
    `digest:`/`origin:`.

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

    body_three = BASE + b"\nversion: 3\ndigest: x\norigin: y\n"
    body_four = BASE + b"\nversion: 4\ndigest: x\norigin: y\n"
    assert skill_version.digest(body_three) != skill_version.digest(body_four)
    assert skill_version.digest(body_three) != skill_version.digest(BASE)


def test_crlf_input_digests_the_same_as_lf():
    crlf = BASE.replace(b"\n", b"\r\n")
    assert b"\r\n" in crlf
    assert skill_version.digest(crlf) == skill_version.digest(BASE)


def test_no_frontmatter_still_digests():
    raw = b"# Title\n\nBody.\n"
    assert skill_version.digest(raw) == hashlib.sha256(raw).hexdigest()[:12]


# --- stamping: the fixed point ----------------------------------------------


def test_stamp_is_a_fixed_point():
    """The property hard part #1 asks for by name: stamping a file (which
    rewrites all three identity lines) must not move the digest they are
    computed against.
    """
    stamped = skill_version.stamp(BASE)
    assert skill_version.digest(stamped) == skill_version.digest(BASE)
    assert skill_version.stamped_digest(stamped) == skill_version.digest(BASE)


def test_stamp_is_a_fixed_point_across_restamping_an_already_stamped_file():
    once = skill_version.stamp(BASE)
    twice = skill_version.stamp(once + b"x")  # a body edit between stamps
    assert skill_version.digest(twice) == skill_version.digest(once + b"x")


def test_stamp_is_idempotent():
    once = skill_version.stamp(BASE)
    assert skill_version.stamp(once) == once


def test_stamp_replaces_an_existing_wrong_digest():
    wrong = _with(b'version: "1.0.0"\ndigest: "deadbeefcafe"\norigin: https://x\n')
    assert skill_version.stamped_digest(skill_version.stamp(wrong)) == skill_version.digest(BASE)


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


def test_the_block_is_version_then_digest_then_origin_in_that_order():
    stamped = skill_version.stamp(BASE)
    front = skill_version.FRONTMATTER_RE.match(stamped).group(1).decode()
    lines = front.splitlines()
    assert lines[0].startswith("version:")
    assert lines[1].startswith("digest:")
    assert lines[2].startswith("origin:")


# --- stamping: the semver decision ------------------------------------------


def test_a_never_stamped_file_seeds_one_zero_zero():
    stamped = skill_version.stamp(BASE)
    assert skill_version.stamped_version(stamped) == "1.0.0"


def test_the_old_single_field_scheme_seeds_one_zero_zero_too():
    """The migration, characterized directly: a file whose ONLY identity line
    is the old `version: "<12-hex-digest>"` reads as having no valid semver
    -- `SEMVER_RE` does not match twelve hex digits -- so it takes the exact
    same path as a file stamped for the first time ever. One rule, not a
    special case for the 56 skills that needed it the day this shipped.
    """
    old_style = _with(b'version: "c894961136c7"\n')
    assert skill_version.stamped_version(old_style) is None  # control: reads as absent
    assert skill_version.stamped_version(skill_version.stamp(old_style)) == "1.0.0"


def test_an_unchanged_file_keeps_its_version_exactly() -> None:
    """Nothing about the content moved -- restamping must not even bump
    PATCH. "Same guidance" means no ledger entry at all, not a silent 1.0.1.
    A value `_bump` would never itself produce ("9.9.9") makes a bump
    unambiguous if one happens anyway.
    """
    first = skill_version.stamp(BASE)
    weird = first.replace(skill_version.version_lines(first)[0].encode(), b'version: "9.9.9"')
    assert skill_version.stamped_version(skill_version.stamp(weird)) == "9.9.9"


def test_a_body_edit_after_stamping_bumps_patch_only() -> None:
    first = skill_version.stamp(BASE)
    edited = first.replace(b"Body.", b"Bodyx.")
    restamped = skill_version.stamp(edited)
    assert skill_version.stamped_version(restamped) == "1.0.1"


def test_major_and_minor_are_carried_through_not_invented() -> None:
    """`stamp()` never picks a MAJOR or MINOR -- it only ever bumps PATCH.
    An author who already typed "2.3.0" into the file (e.g. a deliberate
    MINOR bump, in the same edit that changed the body) keeps exactly that
    MAJOR.MINOR; only PATCH is this function's to decide.
    """
    stamped = skill_version.stamp(BASE)
    claimed_230 = stamped.replace(
        skill_version.version_lines(stamped)[0].encode(), b'version: "2.3.0"'
    )
    edited = claimed_230.replace(b"Body.", b"Bodyx.")  # content moved past that claim
    assert skill_version.stamped_version(skill_version.stamp(edited)) == "2.3.1"


def test_a_malformed_prior_digest_forces_a_bump_even_if_the_body_did_not_change() -> None:
    """`stamp` cannot trust a claim it cannot read. A digest field it cannot
    parse is treated exactly like "content changed" -- conservatively, never
    silently reusing a version number for a claim that could not be
    verified. Body untouched; only the digest line is corrupted.
    """
    stamped = skill_version.stamp(BASE)
    claimed_123 = stamped.replace(
        skill_version.version_lines(stamped)[0].encode(), b'version: "1.2.3"'
    )
    corrupted = claimed_123.replace(
        skill_version.digest_lines(claimed_123)[0].encode(), b"digest: banana"
    )
    assert skill_version.stamped_version(skill_version.stamp(corrupted)) == "1.2.4"


def test_a_duplicated_prior_version_line_is_read_as_absent_and_seeds() -> None:
    raw = _with(b'version: "1.2.3"\nversion: "9.9.9"\n')
    assert skill_version.stamped_version(skill_version.stamp(raw)) == "1.0.0"


def test_origin_is_always_the_one_constant_value() -> None:
    stamped = skill_version.stamp(BASE)
    assert skill_version.stamped_origin(stamped) == skill_version.ORIGIN
    assert skill_version.ORIGIN == "https://github.com/thrillmade/agent-skills"


# --- the quotes, and why they are not optional for digest and version ------


def test_unquoted_all_digit_digest_is_coerced_by_yaml():
    """The landmine the quotes exist for. `766941312459` is a REAL historical
    digest (arlyn-delivery's installed frontend-a11y), and unquoted it stops
    being a string; `000000123456` is read as octal and does not round-trip.
    """
    assert yaml.safe_load("digest: 766941312459") == {"digest": 766941312459}
    assert yaml.safe_load("digest: 000000123456") == {"digest": 42798}


def test_unquoted_digest_stamp_is_not_a_valid_stamp():
    assert skill_version.stamped_digest(_with(b"digest: e606dd248a0a\n")) is None


def test_unquoted_version_stamp_is_not_a_valid_stamp():
    assert skill_version.stamped_version(_with(b"version: 1.0.0\n")) is None


@pytest.mark.parametrize(
    "line",
    [
        b"digest: banana\n",
        b'digest: "abc123"\n',
        b'digest: "E606DD248A0A"\n',
        b"digest:\n",
        b"digest: 766941312459\n",
    ],
)
def test_malformed_digest_stamps_read_as_absent(line):
    assert skill_version.stamped_digest(_with(line)) is None


@pytest.mark.parametrize(
    "line",
    [
        b"version: banana\n",
        b'version: "1.2"\n',
        b'version: "01.2.3"\n',
        b'version: "1.2.3.4"\n',
        b"version:\n",
    ],
)
def test_malformed_version_stamps_read_as_absent(line):
    assert skill_version.stamped_version(_with(line)) is None


def test_the_generated_version_line_carries_no_leading_zeros_in_the_examples_above():
    """Control for the leading-zero case above: semver.org's own grammar
    forbids them, and this catalog's own generated values never produce one
    to be confused with.
    """
    assert skill_version.version_line("1.0.0") == 'version: "1.0.0"'


def test_the_generated_digest_line_carries_a_route_home():
    """The one thing a human holding a hand-copied file has no other way to
    learn about the digest specifically. If this string stops being a
    resolvable coordinate the line is decoration.
    """
    line = skill_version.digest_line("e606dd248a0a")
    assert "github.com/thrillmade/agent-skills" in line
    assert "skill-versions.json" in line
    assert line.startswith('digest: "e606dd248a0a"')
    assert "\n" not in line


def test_the_generated_origin_line_is_the_constant_url_unquoted():
    line = skill_version.origin_line()
    assert line == f"origin: {skill_version.ORIGIN}"
    assert '"' not in line


# --- the duplicate-key bypass (C2), for each of the three fields -----------
#
# Two lines for one field, one true and one false. A reader that takes the
# first and a YAML parser that takes the last disagree, and the gate must not
# pass on a file whose identity every downstream tool reads differently.


def test_two_digest_lines_read_as_absent_not_as_the_first():
    d = skill_version.digest(BASE)
    dupe = _with(f'digest: "{d}"\n'.encode() + b'digest: "deadbeefcafe"\n')
    # the trap: a `search`-based reader answers with the FIRST, which is
    # the correct digest, and the file sails through.
    assert skill_version.DIGEST_RE.search(dupe).group(1).decode() == d
    # and PyYAML -- i.e. every agent and every tool -- answers with the LAST.
    front = skill_version.FRONTMATTER_RE.match(dupe).group(1)
    assert yaml.safe_load(front)["digest"] == "deadbeefcafe"
    # so the reader must refuse to answer at all.
    assert skill_version.stamped_digest(dupe) is None
    assert skill_version.digest_line_count(dupe) == 2


def test_two_version_lines_read_as_absent_not_as_the_first():
    dupe = _with(b'version: "1.0.0"\n' + b'version: "9.9.9"\n')
    assert skill_version.SEMVER_RE.search(dupe).group(1).decode() == "1.0.0"
    front = skill_version.FRONTMATTER_RE.match(dupe).group(1)
    assert yaml.safe_load(front)["version"] == "9.9.9"
    assert skill_version.stamped_version(dupe) is None
    assert skill_version.version_line_count(dupe) == 2


def test_two_origin_lines_read_as_absent_not_as_the_first():
    dupe = _with(b"origin: https://a\n" + b"origin: https://b\n")
    assert skill_version.stamped_origin(dupe) is None
    assert skill_version.origin_line_count(dupe) == 2


def test_a_second_malformed_digest_line_also_reads_as_absent():
    """The strict count alone is not enough: one well-formed stamp plus one
    malformed line leaves `findall` at exactly one strict match while YAML
    still reads the other. The count that has to be one is the PERMISSIVE one.
    """
    d = skill_version.digest(BASE)
    dupe = _with(f'digest: "{d}"\n'.encode() + b"digest: banana\n")
    assert len(skill_version.DIGEST_RE.findall(dupe)) == 1
    front = skill_version.FRONTMATTER_RE.match(dupe).group(1)
    assert yaml.safe_load(front)["digest"] == "banana"
    assert skill_version.stamped_digest(dupe) is None


def test_duplicate_lines_do_not_change_the_digest():
    """Both are elided, so the expected value printed at a duplicate is the
    same one printed at a missing stamp -- the message cannot be wrong.
    """
    d = skill_version.digest(BASE)
    dupe = _with(f'digest: "{d}"\n'.encode() + b'digest: "deadbeefcafe"\n')
    assert skill_version.digest(dupe) == d


def test_an_identity_line_in_the_body_is_not_counted():
    assert skill_version.version_line_count(BASE + b"\nversion: 2\n") == 0
    assert skill_version.digest_line_count(BASE + b"\ndigest: x\n") == 0
    assert skill_version.origin_line_count(BASE + b"\norigin: x\n") == 0


# --- the real tree -----------------------------------------------------------


def _catalog_files():
    return sorted(SKILLS.glob("*/SKILL.md"))


def test_the_catalog_has_skills_to_check():
    """Control for every zero below."""
    assert len(_catalog_files()) >= 40


@pytest.mark.parametrize("path", _catalog_files(), ids=lambda p: p.parent.name)
def test_every_catalog_skill_is_stamped_with_its_own_digest(path):
    raw = path.read_bytes()
    assert skill_version.stamped_digest(raw) == skill_version.digest(raw)


@pytest.mark.parametrize("path", _catalog_files(), ids=lambda p: p.parent.name)
def test_every_catalog_skill_carries_a_well_formed_semver(path):
    raw = path.read_bytes()
    assert skill_version.stamped_version(raw) is not None


@pytest.mark.parametrize("path", _catalog_files(), ids=lambda p: p.parent.name)
def test_every_catalog_skill_carries_the_one_true_origin(path):
    raw = path.read_bytes()
    assert skill_version.stamped_origin(raw) == skill_version.ORIGIN


@pytest.mark.parametrize("path", _catalog_files(), ids=lambda p: p.parent.name)
def test_stamping_every_catalog_skill_is_a_no_op(path):
    raw = path.read_bytes()
    assert skill_version.stamp(raw) == raw


@pytest.mark.parametrize("path", _catalog_files(), ids=lambda p: p.parent.name)
def test_no_catalog_file_contains_a_carriage_return(path):
    assert b"\r" not in path.read_bytes()
