"""Prove the catalog-directory guards can fail.

A guard that has never failed on demand is not proven. This file breaks each
one on purpose, one entry per MUTATIONS row, and asserts the suites that claim
to constrain it go red -- committed, so the proof re-runs on every PR instead
of living in somebody's recollection of a terminal session.

How it works: build a scratch repo (`.github/scripts/` + `tests/` + the real
`skills/` and `docs/placement-map.json`), apply one textual mutation to one
script, and run the real suites there in a subprocess. Red means they noticed.
Every mutation also asserts it LANDED -- a find-and-replace that silently
matched nothing would otherwise "prove" the guards work by testing an
unmodified file, which is the same mistake as a control-free grep.

`test_control_the_unmutated_tree_is_green` is the other half. Without it, "the
suite went red" is equally explained by a scratch harness that would report red
for any input at all.

Two scripts are under test and the split matters. `gen_skill_directory.py`
decides what the directory SAYS; `validate_skills.py` decides whether the
committed one still matches. Deleting either leaves the drift #229 filed
representable, so both have rows here.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GEN = REPO_ROOT / ".github" / "scripts" / "gen_skill_directory.py"
VALIDATOR = REPO_ROOT / ".github" / "scripts" / "validate_skills.py"
# Added when the per-skill versioning gate (#238) landed: both the validator
# and tests/conftest.py import `skill_version`, so a scratch tree without it
# dies at conftest import and every mutation below goes red for the wrong
# reason -- which the control caught rather than the mutations.
SKILL_VERSION = REPO_ROOT / ".github" / "scripts" / "skill_version.py"
VERSIONS_INDEX = REPO_ROOT / "docs" / "skill-versions.json"
CONFTEST = Path(__file__).parent / "conftest.py"
SUITES = [
    Path(__file__).parent / "test_gen_skill_directory.py",
    Path(__file__).parent / "test_validate_skills.py",
]
SKILLS = REPO_ROOT / "skills"
PLACEMENT_MAP = REPO_ROOT / "docs" / "placement-map.json"

# Each entry: (script, name, exact source text, replacement). The comment on
# each says what defect it reintroduces -- a mutation nobody can name the
# damage for is not worth committing.
MUTATIONS = [
    # --- gen_skill_directory.py: what the directory says -------------------
    (
        GEN,
        # The directory scans its own body for the phrases it says nothing
        # covers, so every probe matches itself on the second run and the file
        # can never be regenerated. Found by running the generator twice; the
        # first write poisoned the second.
        "the_directory_probes_itself",
        "        if d.name == DIRECTORY_SLUG:\n            continue",
        "        if False:\n            continue",
    ),
    (
        GEN,
        # The control deleted. A matcher that matches nothing then "proves"
        # every gap the section claims -- an uncontrolled zero, which is the
        # specific mistake this project has been burned by repeatedly.
        "the_not_here_control_is_dropped",
        "    if not control:\n        raise SystemExit(",
        "    if False:\n        raise SystemExit(",
    ),
    (
        GEN,
        # A gap that has since been filled keeps being advertised as a gap, so
        # the directory routes an agent OUT of the catalog for something the
        # catalog now owns -- causing the duplication it exists to prevent.
        "a_filled_gap_is_still_advertised",
        "    if filled:\n        raise SystemExit(",
        "    if False:\n        raise SystemExit(",
    ),
    (
        GEN,
        # A skill on disk with no family is silently dropped. The directory
        # then looks complete and is not, which is #229's failure exactly --
        # reintroduced one level down, inside the fix.
        "a_skill_in_no_family_is_dropped_silently",
        "    if orphans:\n        raise SystemExit(",
        "    if False:\n        raise SystemExit(",
    ),
    (
        GEN,
        # A run from the wrong directory renders an empty list, and nothing
        # about an empty directory looks wrong to the agent reading it.
        "an_empty_tree_renders_an_empty_directory",
        "    if not dirs:\n        raise SystemExit(",
        "    if False:\n        raise SystemExit(",
    ),
    (
        GEN,
        # Without the map there is no `owns` text at all, so every line
        # degrades to a bare name. A directory that silently says less is
        # indistinguishable from one that says everything.
        "a_missing_source_degrades_instead_of_refusing",
        "    if not map_path.exists():\n        raise SystemExit(",
        "    if False:\n        raise SystemExit(",
    ),
    (
        GEN,
        # The size reserve stops applying, so the directory grows past the cap
        # and the consuming reviewer truncates its tail -- and the tail of a
        # directory is skills that then look like they do not exist.
        "the_size_reserve_is_disabled",
        "MAX_BODY_BYTES = 7900",
        "MAX_BODY_BYTES = 100000000",
    ),
    (
        GEN,
        # Off by one at the reserve. The boundary pair is what catches this,
        # not the large cases.
        "the_size_reserve_is_off_by_one",
        "    if n <= MAX_BODY_BYTES:\n        return None",
        "    if n <= MAX_BODY_BYTES + 1:\n        return None",
    ),
    (
        GEN,
        # The body is measured in characters. Every em dash in it is three
        # bytes, so a body well past the cap passes a count that says it fits.
        "the_body_is_measured_in_characters",
        '    n = len(body.encode("utf-8"))\n    if n <= MAX_BODY_BYTES:',
        "    n = len(body)\n    if n <= MAX_BODY_BYTES:",
    ),
    (
        GEN,
        # `--check` stops reporting drift, so the CI wiring is decorative: a
        # stale directory passes the one command whose whole job is to notice.
        "check_passes_on_a_stale_directory",
        '    if args.check:\n        print(\n            f"::error file={path}::the committed directory body differs from what "',
        '    if False:\n        print(\n            f"::error file={path}::the committed directory body differs from what "',
    ),
    (
        GEN,
        # `--write` drops the hand-authored frontmatter. `description` is the
        # trigger surface -- the one field that decides whether an agent loads
        # the skill at all -- so regenerating would silently unpublish it.
        "write_discards_the_frontmatter",
        "        path.write_text(front + body, encoding=\"utf-8\")",
        "        path.write_text(body, encoding=\"utf-8\")",
    ),
    # --- validate_skills.py: whether the committed one still matches --------
    (
        VALIDATOR,
        # The staleness comparison deleted. A skill can be added, or the
        # directory hand-edited, and the gate says nothing -- which is the
        # README table's defect, recreated in the artifact meant to replace it.
        "the_staleness_comparison_is_deleted",
        "    if content[m.end():] != rendered:",
        "    if False:",
    ),
    (
        VALIDATOR,
        # The whole directory gate skipped. Same defect, reached without
        # touching the comparison.
        "the_directory_gate_never_runs",
        "    path = root / gen_skill_directory.DIRECTORY_SLUG / \"SKILL.md\"\n    if not path.exists():\n        return []",
        "    path = root / gen_skill_directory.DIRECTORY_SLUG / \"SKILL.md\"\n    return []",
    ),
    (
        VALIDATOR,
        # A directory that cannot be rendered is treated as fine. Presence
        # without a usable source is the worst state of the three: an
        # unverifiable directory reads exactly like a verified one.
        "an_unverifiable_directory_passes",
        "    except SystemExit as e:\n        return [",
        "    except SystemExit as e:\n        return []\n        return [",
    ),
    (
        VALIDATOR,
        # The rendered size stops being gated at the repo level, so the only
        # thing standing between the catalog and a truncated directory is
        # somebody remembering to run the generator by hand.
        "the_rendered_size_is_not_gated",
        "    size = gen_skill_directory.size_error(rendered)\n    if size:",
        "    size = gen_skill_directory.size_error(rendered)\n    if False:",
    ),
    (
        VALIDATOR,
        # `family` becomes optional, so a skill can be added that the
        # directory has nowhere to put -- and the generator, not the gate,
        # discovers it. The point of requiring it here is that the failure
        # lands on the PR that adds the skill.
        "family_is_no_longer_required",
        "                        if not isinstance(family, str) or not family.strip():",
        "                        if False:",
    ),
    (
        VALIDATOR,
        # A typo'd family id is accepted. The skill then belongs to a family
        # that does not exist and vanishes from its own directory.
        "a_family_id_need_not_exist",
        "                        elif family not in family_ids:",
        "                        elif False:",
    ),
    (
        VALIDATOR,
        # `owns` becomes optional: the skill is listed with no text saying what
        # it owns, which is the column that does the work.
        "owns_is_no_longer_required",
        "                        if not isinstance(owns, str) or not owns.strip():",
        "                        if False:",
    ),
    (
        VALIDATOR,
        # The per-skill byte cap stops applying. It is what keeps the whole
        # directory under the skill body limit as the catalog grows; without
        # it, one long line per skill is paid fifty times over.
        "the_owns_cap_is_disabled",
        '                        elif len(owns.encode("utf-8")) > gen_skill_directory.OWNS_MAX_BYTES:',
        "                        elif False:",
    ),
    (
        VALIDATOR,
        # Off by one at the cap.
        "the_owns_cap_is_off_by_one",
        '                        elif len(owns.encode("utf-8")) > gen_skill_directory.OWNS_MAX_BYTES:',
        '                        elif len(owns.encode("utf-8")) > gen_skill_directory.OWNS_MAX_BYTES + 1:',
    ),
    (
        VALIDATOR,
        # The cap is counted in characters. The budget it protects is bytes,
        # so a line of em dashes passes at three times the size it claims.
        "the_owns_cap_counts_characters",
        '                        elif len(owns.encode("utf-8")) > gen_skill_directory.OWNS_MAX_BYTES:',
        "                        elif len(owns) > gen_skill_directory.OWNS_MAX_BYTES:",
    ),
    (
        VALIDATOR,
        # A family with no skills survives. The map then claims a grouping the
        # directory does not show -- the divergence the 1:1 reconcile exists to
        # stop, in the one direction it does not cover.
        "a_dead_family_survives",
        "                    dead = [] if malformed_entry else sorted(family_ids - used)",
        "                    dead = []",
    ),
    (
        VALIDATOR,
        # `families` becomes optional, so every skill's `family` is
        # unresolvable and the directory is a flat list of names.
        "families_is_no_longer_required",
        "                if not isinstance(families, list) or not families:",
        "                if False:",
    ),
    (
        VALIDATOR,
        # One id declared twice, so every skill in it is listed twice and the
        # directory's own counts stop being trustworthy.
        "a_family_id_may_be_declared_twice",
        "                        elif fid in family_ids:",
        "                        elif False:",
    ),
    (
        VALIDATOR,
        # A family id that is not a slug. It reaches the rendered body as a
        # heading anchor nothing can link to.
        "a_family_id_need_not_be_a_slug",
        "                        if not isinstance(fid, str) or not NAME_SLUG_RE.match(fid):",
        "                        if not isinstance(fid, str):",
    ),
    (
        VALIDATOR,
        # An unhashable `family` (a JSON list) crashes the whole gate with a
        # TypeError instead of being reported by it. This one shipped, briefly,
        # and a boundary parametrization caught it.
        "an_unhashable_family_crashes_the_gate",
        '                        if isinstance(m, dict) and isinstance(m.get("family"), str)',
        "                        if isinstance(m, dict)",
    ),
    # --- gen_skill_directory.py: the probe surface and the growth numbers ---
    (
        GEN,
        # The gap probes read whole bodies again. One cross-reference in one
        # skill ("`superpowers:test-driven-development` owns that") then
        # reddens the WHOLE gate, filing the error against this directory on a
        # PR that never touched it -- including a foreign release-sync PR for
        # one of the nine repo-mirrored skills.
        "the_probe_scan_reads_whole_bodies",
        '    return f"{name}\\n{front}"',
        '    return f"{name}\\n{text}"',
    ),
    (
        GEN,
        # Growth stops paying for the families it needs. The ceiling then
        # overstates the headroom -- which is how the original hand-typed
        # growth table came out generous under every model it stated.
        "the_ceiling_gets_new_families_for_free",
        "        if k % per_family == 0:",
        "        if False:",
    ),
    (
        GEN,
        # Off by one at the ceiling: the reported headroom includes one skill
        # that does not fit.
        "the_ceiling_is_off_by_one",
        "    return len(dirs) + extra",
        "    return len(dirs) + extra + 1",
    ),
    (
        GEN,
        # Growth prices `owns` at half the cap instead of at it. A ceiling is
        # a promise, and a promise priced at the typical case breaks on the
        # worst one.
        "growth_prices_owns_below_the_cap",
        '    owns = "x" * owns_max',
        '    owns = "x" * (owns_max // 2)',
    ),
    (
        GEN,
        # A measured rung typed back into the refusal text. Every number of
        # that kind this file used to carry was wrong when it was checked; the
        # refusal names levers and the tool measures their worth on demand.
        "the_size_refusal_recites_a_measured_number",
        '        "(4) retire skills. At this size the cap is information about the "',
        '        "(4) retire skills, expected at roughly 74. At this size the cap is '
        'information about the "',
    ),
    # --- validate_skills.py: retirement and the README ---------------------
    (
        VALIDATOR,
        # A retired skill may be filed among the live ones. The directory then
        # routes agents INTO guidance its own author told them to stop
        # following -- which shipped, as `skillforge`.
        "a_retired_skill_may_be_filed_as_live",
        "                        if (\n                            slug in superseded",
        "                        if (\n                            False",
    ),
    (
        VALIDATOR,
        # The retirement marker stops being anchored to the start of the
        # description, so a skill ABOUT retirement is reported as retired. A
        # rule that fires on the innocent case is a rule somebody switches off.
        "the_retirement_marker_is_matched_anywhere",
        "    if isinstance(description, str) and SUPERSEDED_RE.match(description):",
        "    if isinstance(description, str) and SUPERSEDED_RE.search(description):",
    ),
    (
        VALIDATOR,
        # The RESERVED `superseded_by` key stops counting, so the detector
        # goes quiet the first time somebody uses the field the SPEC actually
        # provides for this.
        "the_reserved_retirement_key_is_ignored",
        '    if isinstance(meta.get("superseded_by"), str) and meta["superseded_by"].strip():',
        "    if False:",
    ),
    (
        VALIDATOR,
        # A skill can be added without a README row: #229's first problem,
        # left exactly as it was found.
        "a_skill_may_be_missing_from_the_readme",
        "    missing = sorted(on_disk - linked)",
        "    missing = []",
    ),
    (
        VALIDATOR,
        # A README row outlives its skill, sending a reader to a 404 while
        # counting toward a completeness nobody has.
        "a_readme_row_may_outlive_its_skill",
        "    stale = sorted(linked - on_disk)",
        "    stale = []",
    ),
    (
        VALIDATOR,
        # The README reconcile never runs at all. Same defect, reached without
        # touching either direction of it.
        "the_readme_gate_never_runs",
        "    errors.extend(readme_errors(root, skill_dirs))",
        "    errors.extend([])",
    ),
    # --- validate_skills.py: house section structure -----------------------
    (
        VALIDATOR,
        # The whole gate never runs. Every skill missing a house section, or
        # carrying them out of order, ships silently -- the drift #266's CEO
        # ruling exists to close, reopened at the call site rather than
        # inside either check.
        "the_house_structure_gate_never_runs",
        "    if isinstance(skills_map, dict):\n"
        "        errors.extend(\n"
        "            house_structure_errors(root, skill_dirs, skill_meta, superseded, skills_map)\n"
        "        )",
        "    if False:\n"
        "        pass",
    ),
    (
        VALIDATOR,
        # A skill missing one or more of the five sections is not reported --
        # the presence half of the rule, the one that actually names the
        # shape.
        "a_missing_house_section_is_not_reported",
        "        missing = [h for h in HOUSE_SECTIONS if h not in present]\n"
        "        if missing:",
        "        missing = [h for h in HOUSE_SECTIONS if h not in present]\n"
        "        if False:",
    ),
    (
        VALIDATOR,
        # All five sections present but in the wrong order stops being an
        # error -- the SWAP/third-order drift this gate reordered 14 real
        # files to close reopens silently.
        "house_sections_out_of_order_are_not_reported",
        "        if present != list(HOUSE_SECTIONS):",
        "        if False:",
    ),
    (
        VALIDATOR,
        # The opt-out itself: every exemption (SUPERSEDED, [L2 stub],
        # repo-mirrored, the exempt families, the named exceptions) stops
        # applying, so every legitimately-exempt skill in the real catalog --
        # the udts-* stubs, the review-discipline family, logmind, the L1
        # dispatchers, and more -- starts failing a rule it was never meant
        # to carry. Proves the opt-out is load-bearing, not decorative: this
        # file's own `test_an_exempt_family_is_not_required_to_conform` /
        # `test_a_named_exemption_is_not_required_to_conform` /
        # `test_a_superseded_skill_is_exempt` / `test_an_l2_stub_is_exempt` /
        # `test_a_repo_mirrored_skill_is_exempt` go red.
        "the_house_structure_exemptions_are_ignored",
        "    if dir_name == gen_skill_directory.DIRECTORY_SLUG:",
        "    return None\n    if dir_name == gen_skill_directory.DIRECTORY_SLUG:",
    ),
]


def _scratch(tmp_path: Path, script: Path, source: str) -> Path:
    """A runnable copy of the repo with `script` replaced by `source`.

    Mirrors the real layout rather than inventing a minimal one, because the
    suites import through `tests/conftest.py`, which resolves
    `.github/scripts` relative to itself -- and because two of the tests chdir
    to the repo root and assert against the REAL catalog, so `skills/` and the
    placement map have to be there too.
    """
    scripts = tmp_path / ".github" / "scripts"
    scripts.mkdir(parents=True)
    for real in (GEN, VALIDATOR, SKILL_VERSION):
        shutil.copy(real, scripts / real.name)
    (scripts / script.name).write_text(source, encoding="utf-8")

    shutil.copytree(SKILLS, tmp_path / "skills")
    (tmp_path / "docs").mkdir()
    shutil.copy(PLACEMENT_MAP, tmp_path / "docs" / "placement-map.json")
    # The validator refuses a missing index rather than passing over it (#238),
    # so the scratch tree needs one or every run fails on absence, not mutation.
    shutil.copy(VERSIONS_INDEX, tmp_path / "docs" / "skill-versions.json")

    tests = tmp_path / "tests"
    tests.mkdir()
    shutil.copy(CONFTEST, tests / "conftest.py")
    for suite in SUITES:
        shutil.copy(suite, tests / suite.name)
    return tests


def _run_suites(tests: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "pytest", str(tests), "-q", "-p", "no:cacheprovider", *extra],
        capture_output=True,
        text=True,
        check=False,
        cwd=tests.parent,
    )


def test_control_the_unmutated_tree_is_green(tmp_path: Path) -> None:
    """The scratch harness can report success. Without this, every red below
    is equally explained by a broken harness.
    """
    tests = _scratch(tmp_path, GEN, GEN.read_text(encoding="utf-8"))
    result = _run_suites(tests)
    assert result.returncode == 0, (
        "the unmutated suites are not green in the scratch tree, so nothing "
        f"below is evidence:\n{result.stdout}\n{result.stderr}"
    )


def test_every_mutation_is_named_once() -> None:
    """Two rows under one name would report as one parametrized case and
    quietly halve the evidence.
    """
    names = [m[1] for m in MUTATIONS]
    assert len(names) == len(set(names)), sorted(n for n in names if names.count(n) > 1)


@pytest.mark.parametrize(
    "script,name,old,new", MUTATIONS, ids=[m[1] for m in MUTATIONS]
)
def test_mutation_turns_the_suites_red(
    tmp_path: Path, script: Path, name: str, old: str, new: str
) -> None:
    source = script.read_text(encoding="utf-8")
    assert source.count(old) == 1, (
        f"mutation {name!r} does not match {script.name} exactly once "
        f"({source.count(old)} matches). The script changed shape; update the "
        "mutation so it keeps testing what it claims to."
    )
    mutated = source.replace(old, new)
    assert mutated != source, f"mutation {name!r} did not land"

    tests = _scratch(tmp_path, script, mutated)
    result = _run_suites(tests, "-x")
    assert result.returncode != 0, (
        f"mutation {name!r} was applied and the suites still passed, so nothing "
        f"in them constrains that behaviour:\n{result.stdout}"
    )
