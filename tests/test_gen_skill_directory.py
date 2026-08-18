"""Characterization tests for `.github/scripts/gen_skill_directory.py`.

The generator's job is narrow and its refusals are the interesting part. A
directory rendered from a source that failed to load is a SHORT directory, and
a short directory reads exactly like a complete one to the agent holding it --
so every degrade-to-partial path here is a `SystemExit` instead, and each one
has a test.

Assertion text is matched on the phrase unique to the guard under test. Several
refusals share the words "Refusing to build a directory", so asserting on that
would pass with the guard deleted -- green on the next guard's message, which
is not a pass about this one.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import gen_skill_directory as gen
from conftest import SkillTree

REPO_ROOT = Path(__file__).resolve().parents[1]

FAM = [{"id": "fam", "title": "A family", "routes": "What this family covers."}]


def entry(family: str = "fam", owns: str = "a fragment") -> dict:
    return {
        "authoring_home": "catalog",
        "distribution": "opt-in",
        "subscribers": [],
        "family": family,
        "owns": owns,
    }


def a_tree(tree: SkillTree, *names: str, families: list | None = None, **owns) -> None:
    """`names` skills plus a control skill, and a map covering all of them."""
    tree.control_skill()
    for n in names:
        tree.valid_skill(n)
    skills = {n: entry(owns=owns.get(n, "a fragment")) for n in names}
    skills["control"] = entry()
    tree.placement_map(
        {
            "version": 1,
            "updated": "2026-08-18",
            "families": families if families is not None else FAM,
            "skills": skills,
        }
    )


def render(tree: SkillTree) -> str:
    return gen.render(tree.base / "skills", tree.base / "docs" / "placement-map.json")


# --- what it renders -------------------------------------------------------


def test_every_skill_on_disk_is_listed(tree: SkillTree) -> None:
    a_tree(tree, "alpha", "beta")
    body = render(tree)
    assert "- `alpha` — a fragment" in body
    assert "- `beta` — a fragment" in body
    assert "- `control` — a fragment" in body
    # control: the probe would notice a name that is NOT there
    assert "- `gamma`" not in body


def test_skills_are_sorted_within_a_family(tree: SkillTree) -> None:
    """Order is the tree's, not the JSON's. A map whose keys were reordered
    would otherwise rewrite the whole document and hide the real change.
    """
    a_tree(tree, "zeta", "alpha")
    body = render(tree)
    assert body.index("`alpha`") < body.index("`control`") < body.index("`zeta`")


def test_families_render_in_declared_order(tree: SkillTree) -> None:
    fams = [
        {"id": "second", "title": "Second", "routes": "R2"},
        {"id": "fam", "title": "A family", "routes": "R1"},
    ]
    tree.control_skill()
    tree.valid_skill("alpha")
    tree.placement_map(
        {
            "version": 1,
            "updated": "2026-08-18",
            "families": fams,
            "skills": {"control": entry("second"), "alpha": entry("fam")},
        }
    )
    body = render(tree)
    assert body.index("## Second") < body.index("## A family")


def test_an_empty_family_renders_nothing(tree: SkillTree) -> None:
    # It is a gate failure, reported by validate_skills by name. Rendering a
    # heading with no skills under it would make the two disagree about the
    # same defect.
    a_tree(tree, "alpha", families=FAM + [{"id": "ghost", "title": "Ghost", "routes": "R"}])
    body = render(tree)
    assert "## Ghost" not in body
    assert "## A family" in body  # control: headings do render


# --- what it refuses to render ---------------------------------------------


def test_zero_skills_is_fatal(tree: SkillTree) -> None:
    (tree.base / "skills").mkdir()
    with pytest.raises(SystemExit, match="from zero skills"):
        render(tree)


def test_a_missing_placement_map_is_fatal(tree: SkillTree) -> None:
    tree.valid_skill()
    with pytest.raises(SystemExit, match="Refusing to build a directory without .*placement-map.json"):
        render(tree)


def test_a_malformed_placement_map_is_fatal(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map(raw="{not json")
    with pytest.raises(SystemExit, match="is not valid JSON"):
        render(tree)


def test_a_map_without_families_is_fatal(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map({"version": 1, "updated": "d", "skills": {"alpha": entry()}})
    with pytest.raises(SystemExit, match="no non-empty `families` list"):
        render(tree)


def test_a_map_without_skills_is_fatal(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map({"version": 1, "updated": "d", "families": FAM, "skills": {}})
    with pytest.raises(SystemExit, match="no non-empty `skills` object"):
        render(tree)


def test_a_skill_in_no_family_is_fatal(tree: SkillTree) -> None:
    """The one that matters most: silently dropping it produces a directory
    that is complete-looking and wrong, which is #229's failure exactly.
    """
    a_tree(tree, "alpha")
    m = json.loads((tree.base / "docs" / "placement-map.json").read_text())
    m["skills"]["alpha"]["family"] = "nowhere"
    tree.placement_map(m)
    with pytest.raises(SystemExit, match="omits skills on disk: alpha"):
        render(tree)


def test_a_skill_missing_from_the_map_entirely_is_fatal(tree: SkillTree) -> None:
    a_tree(tree, "alpha")
    tree.valid_skill("beta")  # on disk, never added to the map
    with pytest.raises(SystemExit, match="omits skills on disk: beta"):
        render(tree)


# --- the "deliberately not here" section -----------------------------------


def test_the_not_here_section_refuses_when_a_gap_has_been_filled(tree: SkillTree) -> None:
    a_tree(tree, "alpha")
    phrase = gen.NOT_HERE_PROBES[0][0]
    tree.skill(
        "alpha",
        f"---\nname: alpha\ndescription: Use when you need {phrase}.\n---\n\n# T\n\nBody.\n",
    )
    with pytest.raises(SystemExit, match="out of date"):
        render(tree)


def test_a_probe_phrase_in_a_body_is_not_coverage(tree: SkillTree) -> None:
    """The scan reads the trigger surface, not bodies, and both directions of
    that matter.

    Outward: scanning bodies meant one cross-reference -- "`superpowers:
    test-driven-development` owns that" -- reddened the whole gate, with the
    error filed against a file the PR never touched. Nine of these skills are
    repo-mirrored, so that was a foreign release-sync PR going red over this
    catalog's editorial gap list.

    Inward: a body mention is a pointer. A skill covers a topic when its
    trigger surface says so, because that is what decides whether an agent
    ever loads it. The test above is the control: the same phrase in
    `description` still refuses.
    """
    a_tree(tree, "alpha")
    phrase = gen.NOT_HERE_PROBES[1][0]
    tree.skill(
        "alpha",
        "---\nname: alpha\ndescription: Unrelated.\n---\n\n# T\n\n"
        f"Routing: `superpowers:{phrase}-development` owns that.\n",
    )
    assert f"`{phrase}` matches **0** skills" in render(tree)


def test_the_not_here_section_refuses_when_its_control_matches_nothing(
    tree: SkillTree,
) -> None:
    """An uncontrolled zero is not a measurement. Without this, a matcher that
    matched nothing at all would 'prove' every gap the section claims.
    """
    tree.valid_skill("alpha")  # no control skill: nothing mentions the control term
    tree.placement_map(
        {
            "version": 1,
            "updated": "2026-08-18",
            "families": FAM,
            "skills": {"alpha": entry()},
        }
    )
    with pytest.raises(SystemExit, match="control probe"):
        render(tree)


def test_the_directory_does_not_probe_itself(tree: SkillTree) -> None:
    """Regression. The section NAMES the phrases it says nothing covers, so
    scanning the directory's own body made every probe match on the second run
    and the file could never be regenerated.
    """
    a_tree(tree, "alpha", gen.DIRECTORY_SLUG)
    tree.skill(
        gen.DIRECTORY_SLUG,
        "---\nname: x\ndescription: covers none of "
        + ", ".join(p for p, _ in gen.NOT_HERE_PROBES)
        + "\n---\n\n# T\n\nBody.\n",
    )
    body = render(tree)  # would raise "out of date" if the directory were scanned
    assert "matches **0** skills" in body


def test_the_control_count_is_rendered(tree: SkillTree) -> None:
    a_tree(tree, "alpha")
    assert f"(Control: `{gen.NOT_HERE_CONTROL}` matches 1," in render(tree)


# --- the size reserve ------------------------------------------------------


def test_the_reserve_sits_under_the_skill_cap() -> None:
    """The reserve is only a reserve if it is under the real cap and has room
    in it. Raising `MAX_BODY_BYTES` past `SIZE_LIMIT` is the one-line change
    that turns this whole guard off while every relative assertion below stays
    green -- the same shape as the `limitBytes` escape validate_skills.py:74-89
    already refused.
    """
    import validate_skills

    assert gen.SIZE_LIMIT == validate_skills.SIZE_LIMIT, (
        "the cap has two owners and they disagree"
    )
    assert gen.MAX_BODY_BYTES < gen.SIZE_LIMIT
    # Room for several more rows, so the next skill added is not the one that
    # discovers the ceiling in CI. A row is name + markup + owns, ~60 bytes.
    assert gen.SIZE_LIMIT - gen.MAX_BODY_BYTES >= 4 * 60


def test_size_error_is_none_at_exactly_the_reserve() -> None:
    assert gen.size_error("x" * gen.MAX_BODY_BYTES) is None


def test_size_error_fires_one_byte_over_the_reserve() -> None:
    msg = gen.size_error("x" * (gen.MAX_BODY_BYTES + 1))
    assert msg is not None
    assert f"{gen.MAX_BODY_BYTES + 1} bytes" in msg
    assert "by 1" in msg


def test_size_error_names_the_ladder() -> None:
    """The message carries the remedy on purpose: a maintainer told only a
    number files a bypass; one told which lever is next spends it.
    """
    msg = gen.size_error("x" * (gen.MAX_BODY_BYTES + 1))
    assert "retire skills" in msg
    assert "Splitting the directory in two is NOT a lever" in msg


def test_size_error_recites_no_measured_number() -> None:
    """Every integer in the refusal must be derivable from the body and the
    two limits.

    The rungs used to carry measured worths typed into the string ("74 to 81",
    "a ceiling of 87", "roughly 155"), and not one of them reproduced -- a
    hand-kept number with no owner, inside the change whose thesis is that
    hand-kept numbers with no owner are the defect. `levers()` measures them
    now, on the tree in front of you, at the moment you ask.
    """
    import re as _re

    n = gen.MAX_BODY_BYTES + 1
    msg = gen.size_error("x" * n)
    # 1-4 number the levers and 229 is the issue this exists for. Neither is
    # a measurement, and nothing else is allowed to appear.
    allowed = {n, gen.MAX_BODY_BYTES, gen.SIZE_LIMIT, n - gen.MAX_BODY_BYTES, 1, 2, 3, 4, 229}
    found = {int(x) for x in _re.findall(r"\d+", msg)}
    assert found <= allowed, sorted(found - allowed)


# --- growth, measured rather than recited ----------------------------------


def test_the_ceiling_is_where_the_reserve_actually_binds(tree: SkillTree) -> None:
    """Self-consistency, and the property the whole function claims: render at
    the ceiling and it fits; render at one more and it does not.
    """
    a_tree(tree, "alpha", "beta")
    dirs, families, skills, nh = gen._inputs(
        tree.base / "skills", tree.base / "docs" / "placement-map.json"
    )
    top = gen.ceiling(dirs, families, skills, nh, limit=3000)
    extra = top - len(dirs)

    at = gen._body(*gen._grown(dirs, families, skills, extra), nh)
    over = gen._body(*gen._grown(dirs, families, skills, extra + 1), nh)
    assert len(at.encode("utf-8")) <= 3000 < len(over.encode("utf-8"))


def test_the_ceiling_pays_for_the_families_growth_needs(tree: SkillTree) -> None:
    """New skills arrive in new families at the catalog's own density, and a
    family costs a heading and a routing line. A ceiling that assumed families
    were free would overstate the headroom -- which is how the docstring's
    original table came out too generous.
    """
    a_tree(tree, "alpha", "beta")
    dirs, families, skills, nh = gen._inputs(
        tree.base / "skills", tree.base / "docs" / "placement-map.json"
    )
    grown_dirs, grown_fams, _ = gen._grown(dirs, families, skills, 12)
    assert len(grown_fams) > len(families)
    assert len(grown_dirs) == len(dirs) + 12


def test_a_cheaper_owns_raises_the_ceiling_and_bare_names_raise_it_further(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The ladder's ORDER is the claim `size_error()` makes. Its rungs are
    measured, so the ordering is checkable rather than asserted in prose.
    """
    monkeypatch.chdir(REPO_ROOT)
    args = gen._inputs()
    base = gen.ceiling(*args)
    cheaper = gen.ceiling(*args, owns_max=24)
    shorter = gen.ceiling(*args, owns_max=24, route_scale=0.5)
    bare = gen.ceiling(*args, bare=True)
    assert base < cheaper <= shorter < bare


def test_the_ceiling_matches_an_independent_arithmetic_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A computed number is only better than a recited one if something checks
    the computation. This re-derives the ceiling from row and family
    arithmetic written out here, rather than from the generator's code path.
    """
    monkeypatch.chdir(REPO_ROOT)
    dirs, families, skills, nh = gen._inputs()
    n = len(gen._body(dirs, families, skills, nh).encode("utf-8"))

    shown = [
        f for f in families if any(skills.get(s, {}).get("family") == f["id"] for s in dirs)
    ]
    per_family = round(len(dirs) / len(shown))
    name_len = round(sum(len(d.encode("utf-8")) for d in dirs) / len(dirs))
    title_len = round(sum(len(f["title"].encode("utf-8")) for f in shown) / len(shown))
    routes_len = round(sum(len(f["routes"].encode("utf-8")) for f in shown) / len(shown))

    # A row is "- `" + name + "` — " + owns + "\n": 10 bytes of markup (the em
    # dash is three) plus the name plus the fragment.
    row = 10 + name_len + gen.OWNS_MAX_BYTES
    # A family is "## " + title + "\n" + routes + "\n" + a blank line, plus the
    # blank line that closes its list.
    family = 3 + title_len + 1 + routes_len + 1 + 1 + 1
    per_skill = row + family / per_family
    predicted = len(dirs) + int((gen.MAX_BODY_BYTES - n) // per_skill)

    measured = gen.ceiling(dirs, families, skills, nh)
    assert abs(measured - predicted) <= 1, f"measured {measured}, predicted {predicted}"


def test_levers_measures_every_rung_and_says_nothing_when_it_cannot(
    tree: SkillTree, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(REPO_ROOT)
    text = gen.levers()
    assert "skills today" in text
    # Four measurements: today's format and the three rungs under it.
    assert len([c for c in text if c == ";"]) == 3

    monkeypatch.chdir(tree.base)  # no skills/ at all
    assert gen.levers() == ""  # a refusal must not become a traceback


def test_size_error_measures_bytes_not_characters() -> None:
    # An em dash is three bytes. A character count would pass a body twice the
    # size of the cap it claims to enforce.
    assert gen.size_error("—" * (gen.MAX_BODY_BYTES // 3 + 1)) is not None


# --- the CLI ---------------------------------------------------------------


def test_check_passes_on_a_current_directory(tree: SkillTree) -> None:
    a_tree(tree, "alpha", gen.DIRECTORY_SLUG)
    tree.directory()
    assert gen.main(["--check"]) == 0


def test_check_fails_on_a_stale_directory(tree: SkillTree, capsys) -> None:
    a_tree(tree, "alpha", gen.DIRECTORY_SLUG)
    tree.directory()
    assert gen.main(["--check"]) == 0  # control: current before the edit
    path = tree.base / "skills" / gen.DIRECTORY_SLUG / "SKILL.md"
    path.write_text(path.read_text().replace("`alpha`", "`alpha-by-hand`"))
    assert gen.main(["--check"]) == 1
    assert "run `python3 .github/scripts/gen_skill_directory.py --write`" in (
        capsys.readouterr().out.lower()
    )


def test_write_makes_check_pass(tree: SkillTree) -> None:
    a_tree(tree, "alpha", gen.DIRECTORY_SLUG)
    tree.directory()
    path = tree.base / "skills" / gen.DIRECTORY_SLUG / "SKILL.md"
    path.write_text(path.read_text().replace("`alpha`", "`alpha-by-hand`"))
    assert gen.main(["--check"]) == 1  # control: stale first
    assert gen.main(["--write"]) == 0
    assert gen.main(["--check"]) == 0


def test_write_preserves_the_frontmatter(tree: SkillTree) -> None:
    """`description` is a trigger surface, hand-authored. A generator that
    rewrote it would silently undo the one field that makes the skill load.
    """
    a_tree(tree, "alpha", gen.DIRECTORY_SLUG)
    tree.directory()
    path = tree.base / "skills" / gen.DIRECTORY_SLUG / "SKILL.md"
    path.write_text(
        path.read_text().replace("description: d", "description: a real trigger")
    )
    assert gen.main(["--write"]) == 0
    assert "description: a real trigger" in path.read_text()


def test_the_default_mode_writes_nothing(tree: SkillTree) -> None:
    a_tree(tree, "alpha", gen.DIRECTORY_SLUG)
    tree.directory()
    path = tree.base / "skills" / gen.DIRECTORY_SLUG / "SKILL.md"
    before = path.read_text()
    path.write_text(before.replace("`alpha`", "`alpha-by-hand`"))
    stale = path.read_text()
    assert gen.main([]) == 1
    assert path.read_text() == stale


# --- against the real catalog ----------------------------------------------


def test_this_catalog_publishes_a_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    """The one owner of "this repo has a directory".

    `validate_skills.directory_errors` deliberately tolerates a tree without
    one -- its rules have to hold for any tree, and the suite drives it over
    tmp trees that publish nothing. That left the real hole one level up:
    deleting `skills/finding-a-catalog-skill/` AND its placement-map entry was
    green in the gate, so the catalog's own map of itself was removable in two
    lines with nothing reporting it. Retiring it is allowed; doing it by
    accident is not, and this is what makes the difference visible.
    """
    monkeypatch.chdir(REPO_ROOT)
    path = gen.target()
    assert path.exists(), (
        f"{path} is gone. If that is deliberate, delete this test in the same "
        "change and say why; if it is not, run "
        "`python3 .github/scripts/gen_skill_directory.py --write`."
    )
    pm = json.loads(Path("docs/placement-map.json").read_text(encoding="utf-8"))
    assert gen.DIRECTORY_SLUG in pm["skills"]
    assert "zzz-not-a-skill" not in pm["skills"]  # control: absence is detectable


def test_the_shipped_directory_is_current(monkeypatch: pytest.MonkeyPatch) -> None:
    """Belt to `validate_skills`' braces: if this file's own SKILL.md is ever
    committed stale, this fails in the fast suite as well as in the gate.
    """
    monkeypatch.chdir(REPO_ROOT)
    assert gen.main(["--check"]) == 0


def test_the_shipped_directory_is_inside_the_reserve(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(REPO_ROOT)
    body = gen.render()
    n = len(body.encode("utf-8"))
    assert gen.size_error(body) is None, f"{n} bytes"
    # Not just "under the cap" -- under it with room, so the next skill added
    # is not the one that discovers the ceiling in CI.
    assert n <= gen.MAX_BODY_BYTES, n


def test_the_shipped_directory_names_every_skill(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(REPO_ROOT)
    body = gen.render()
    names = sorted(p.name for p in Path("skills").iterdir() if p.is_dir())
    assert names, "control: the catalog is not empty"
    missing = [n for n in names if f"`{n}`" not in body]
    assert missing == []
    assert "`zzz-not-a-skill`" not in body  # control: absence is detectable
