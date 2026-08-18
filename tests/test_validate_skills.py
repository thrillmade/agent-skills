"""Characterization tests for `.github/scripts/validate_skills.py`.

These pin TODAY'S behaviour of the `validate-skills` gate, message text
included -- they are the referent for "mutation-tested before it ships".
Every assertion here was captured by running the pre-extraction heredoc and
the extracted module over the same fixture tree and diffing; where a rule is
sloppier than it looks (a `#Title` without a space is not an H1; a numeric
`name:` reads as "missing"), the test records the sloppiness rather than the
intent. Change a message here only when you meant to change the gate.

Layout mirrors the module: per-skill rules first, then the placement map.
"""

from __future__ import annotations

import pytest

from conftest import SkillTree

# `alpha`'s annotation prefix -- every per-skill error is filed against the
# SKILL.md path, relative to the cwd, so GitHub can anchor the annotation.
ALPHA = "::error file=skills/alpha/SKILL.md::"

HEAD = "---\nname: alpha\ndescription: d\n---"


def only(errors: list[str]) -> str:
    """Assert the tree produced exactly one error and return it. Guards the
    common false pass where a fixture trips a second rule by accident.
    """
    assert len(errors) == 1, f"expected exactly one error, got {errors}"
    return errors[0]


def body_of(size: int) -> str:
    """A skill body of exactly `size` bytes, H1 included."""
    head = "\n\n# Title\n\n"
    body = head + "x" * (size - len(head.encode("utf-8")))
    assert len(body.encode("utf-8")) == size
    return body


# --- File and frontmatter presence -----------------------------------------


def test_clean_tree_produces_no_errors(tree: SkillTree) -> None:
    tree.valid_skill()
    assert tree.validate() == []


def test_missing_skill_md(tree: SkillTree) -> None:
    tree.skill("alpha")  # directory only
    assert only(tree.validate()) == ALPHA + "missing SKILL.md"


def test_missing_frontmatter(tree: SkillTree) -> None:
    tree.skill("alpha", "# Title\n\nNo frontmatter at all.\n")
    assert only(tree.validate()) == (
        ALPHA + "missing YAML frontmatter (must start with --- ... --- block)"
    )


def test_frontmatter_must_start_at_byte_zero(tree: SkillTree) -> None:
    # FRONTMATTER_RE uses .match(), not .search() -- a leading blank line
    # means the block is not frontmatter at all.
    tree.skill("alpha", "\n---\nname: alpha\ndescription: d\n---\n\n# Title\n")
    assert only(tree.validate()) == (
        ALPHA + "missing YAML frontmatter (must start with --- ... --- block)"
    )


def test_invalid_yaml_frontmatter(tree: SkillTree) -> None:
    tree.skill("alpha", "---\nname: alpha\n  bad: [unclosed\n---\n\n# Title\n")
    error = only(tree.validate())
    # PyYAML's own message tail varies by version, so pin only the prefix.
    assert error.startswith(ALPHA + "frontmatter is not valid YAML: ")


def test_frontmatter_must_be_a_mapping(tree: SkillTree) -> None:
    tree.skill("alpha", "---\n- one\n- two\n---\n\n# Title\n")
    assert only(tree.validate()) == ALPHA + "frontmatter must be a YAML mapping"


def test_empty_frontmatter_reports_name_and_description(tree: SkillTree) -> None:
    # `yaml.safe_load(...) or {}` turns an empty block into a mapping, so the
    # per-field rules fire rather than the "must be a mapping" one.
    tree.skill("alpha", "---\n\n---\n\n# Title\n")
    assert tree.validate() == [
        ALPHA + "frontmatter is missing a non-empty `name:` field",
        ALPHA + "frontmatter is missing a non-empty `description:` field",
    ]


# --- name ------------------------------------------------------------------


def test_missing_name(tree: SkillTree) -> None:
    tree.skill("alpha", "---\ndescription: d\n---\n\n# Title\n")
    assert only(tree.validate()) == ALPHA + "frontmatter is missing a non-empty `name:` field"


def test_whitespace_only_name(tree: SkillTree) -> None:
    tree.skill("alpha", '---\nname: "   "\ndescription: d\n---\n\n# Title\n')
    assert only(tree.validate()) == ALPHA + "frontmatter is missing a non-empty `name:` field"


def test_non_string_name_reads_as_missing(tree: SkillTree) -> None:
    # A YAML scalar that isn't a string never reaches the slug or the
    # directory check -- it is reported as absent.
    tree.skill("alpha", "---\nname: 42\ndescription: d\n---\n\n# Title\n")
    assert only(tree.validate()) == ALPHA + "frontmatter is missing a non-empty `name:` field"


def test_name_must_match_directory(tree: SkillTree) -> None:
    tree.skill("alpha", "---\nname: beta\ndescription: d\n---\n\n# Title\n")
    assert only(tree.validate()) == (
        ALPHA + "frontmatter name='beta' does not match directory name 'alpha'"
    )


def test_name_is_stripped_before_comparison(tree: SkillTree) -> None:
    tree.skill("alpha", '---\nname: "  alpha  "\ndescription: d\n---\n\n# Title\n')
    assert tree.validate() == []


@pytest.mark.parametrize(
    "name",
    [
        "9bad",  # must start with a letter
        "Alpha",  # no uppercase
        "under_score",  # no underscores
        "a" * 64,  # 63-char ceiling
    ],
)
def test_name_slug_regex(tree: SkillTree, name: str) -> None:
    tree.skill(name, f"---\nname: {name}\ndescription: d\n---\n\n# Title\n")
    assert only(tree.validate()) == (
        f"::error file=skills/{name}/SKILL.md::frontmatter name='{name}' does not "
        r"match the SPEC §1.10.1 slug regex ^[a-z][a-z0-9-]{0,62}$"
    )


def test_name_slug_accepts_the_63_char_ceiling(tree: SkillTree) -> None:
    name = "a" * 63
    tree.skill(name, f"---\nname: {name}\ndescription: d\n---\n\n# Title\n")
    assert tree.validate() == []


# --- description and body --------------------------------------------------


def test_missing_description(tree: SkillTree) -> None:
    tree.skill("alpha", "---\nname: alpha\n---\n\n# Title\n")
    assert only(tree.validate()) == (
        ALPHA + "frontmatter is missing a non-empty `description:` field"
    )


def test_whitespace_only_description(tree: SkillTree) -> None:
    tree.skill("alpha", '---\nname: alpha\ndescription: "  "\n---\n\n# Title\n')
    assert only(tree.validate()) == (
        ALPHA + "frontmatter is missing a non-empty `description:` field"
    )


def test_missing_h1(tree: SkillTree) -> None:
    tree.frontmatter(body="\n## Only a subheading\n")
    assert only(tree.validate()) == ALPHA + "body has no top-level `# Title` heading"


def test_h1_requires_a_space_after_the_hash(tree: SkillTree) -> None:
    # `^# .+` -- '#NoSpace' is not an H1 as far as this gate is concerned.
    tree.frontmatter(body="\n#NoSpace\n")
    assert only(tree.validate()) == ALPHA + "body has no top-level `# Title` heading"


def test_h1_may_appear_anywhere_in_the_body(tree: SkillTree) -> None:
    tree.frontmatter(body="\nIntro prose first.\n\n# Title\n")
    assert tree.validate() == []


# --- body size (SIZE_LIMIT) ------------------------------------------------


def test_body_at_the_size_limit_passes(tree: SkillTree) -> None:
    tree.skill("alpha", HEAD + body_of(8192))
    assert tree.validate() == []


def test_body_one_byte_over_the_size_limit_fails(tree: SkillTree) -> None:
    tree.skill("alpha", HEAD + body_of(8193))
    error = only(tree.validate())
    assert error.startswith(
        ALPHA + "body is 8193 bytes, over the 8192-byte limit by 1. "
    )
    # The remedy text is the point of the message -- a bare limit invites a
    # bypass PR, so the reason ships with the number.
    assert "truncates the body when building its prompt" in error
    assert "There is no exception list for the limit." in error
    # The prohibition is on relocating INSTRUCTIONS to duck the count, which is
    # a different act from shipping source material in references/. A skill in
    # this catalog does ship one, so a message that bans both makes the catalog
    # contradict itself and leaves the author to pick a sentence to believe.
    assert "Shipping source material" in error
    assert "there is fine and unaffected" in error


def test_size_is_measured_in_bytes_not_characters(tree: SkillTree) -> None:
    # 4100 multi-byte characters are under the character count but over the
    # byte limit (2 bytes each).
    body = "\n\n# Title\n\n" + "é" * 4100
    tree.skill("alpha", HEAD + body)
    assert "body is 8211 bytes" in only(tree.validate())


# --- SPEC §1.10.1 optional fields ------------------------------------------


def test_invalid_kind(tree: SkillTree) -> None:
    tree.frontmatter(extra="kind: policy\n")
    assert only(tree.validate()) == (
        ALPHA + "`kind: 'policy'` is not one of ['design', 'rule', 'writing'] (SPEC §1.10.1)"
    )


@pytest.mark.parametrize("kind", ["rule", "writing", "design"])
def test_valid_kinds(tree: SkillTree, kind: str) -> None:
    tree.frontmatter(extra=f"kind: {kind}\n")
    assert tree.validate() == []


def test_invalid_source(tree: SkillTree) -> None:
    tree.frontmatter(extra="source: hand-written\n")
    assert only(tree.validate()) == (
        ALPHA + "`source: 'hand-written'` is not one of "
        "['clud-bug-baseline', 'logmind-derived', 'manual', 'skills-sh'] (SPEC §1.10.1)"
    )


@pytest.mark.parametrize(
    "source", ["manual", "logmind-derived", "skills-sh", "clud-bug-baseline"]
)
def test_valid_sources(tree: SkillTree, source: str) -> None:
    tree.frontmatter(extra=f"source: {source}\n")
    assert tree.validate() == []


def test_unknown_frontmatter_keys_are_tolerated(tree: SkillTree) -> None:
    # SPEC §2.1: unrecognised keys round-trip untouched. `review_mode` was
    # removed from the schema and is deliberately ignored, not rejected.
    tree.frontmatter(extra="layer: L0\nstatus: active\nreview_mode: fast\nnonsense: 1\n")
    assert tree.validate() == []


# --- applies_to ------------------------------------------------------------


def test_applies_to_must_be_a_mapping(tree: SkillTree) -> None:
    tree.frontmatter(extra="applies_to: everything\n")
    assert only(tree.validate()) == ALPHA + "`applies_to` must be a YAML mapping"


@pytest.mark.parametrize(
    "paths",
    [
        "applies_to:\n  paths: 'src/**'\n",  # string, not a list
        "applies_to:\n  paths:\n    - ''\n",  # empty entry
        "applies_to:\n  paths:\n    - '  '\n",  # whitespace-only entry
        "applies_to:\n  paths:\n    - 7\n",  # non-string entry
    ],
)
def test_invalid_applies_to_paths(tree: SkillTree, paths: str) -> None:
    tree.frontmatter(extra=paths)
    assert only(tree.validate()) == (
        ALPHA + "`applies_to.paths` must be a list of non-empty glob strings (SPEC §1.10.1)"
    )


def test_valid_applies_to_paths(tree: SkillTree) -> None:
    tree.frontmatter(extra="applies_to:\n  paths:\n    - 'src/**'\n    - 'docs/*.md'\n")
    assert tree.validate() == []


@pytest.mark.parametrize(
    "extensions",
    [
        "applies_to:\n  extensions: '.tsx'\n",  # string, not a list
        "applies_to:\n  extensions:\n    - tsx\n",  # no dot
        "applies_to:\n  extensions:\n    - '.'\n",  # bare dot
        "applies_to:\n  extensions:\n    - ''\n",  # empty
        "applies_to:\n  extensions:\n    - '. tsx'\n",  # whitespace
    ],
)
def test_invalid_applies_to_extensions(tree: SkillTree, extensions: str) -> None:
    tree.frontmatter(extra=extensions)
    assert only(tree.validate()) == (
        ALPHA + "`applies_to.extensions` must be a list of extension/suffix strings "
        "(e.g. '.tsx', '_test.py') (SPEC §1.10.1)"
    )


def test_applies_to_extensions_accepts_suffixes_not_just_extensions(tree: SkillTree) -> None:
    # clud-bug suffix-matches, so '_test.py' (shipped by skills/test-discipline)
    # is as legitimate as '.tsx'.
    tree.frontmatter(extra="applies_to:\n  extensions:\n    - .tsx\n    - _test.py\n")
    assert tree.validate() == []


@pytest.mark.parametrize(
    "author",
    [
        "applies_to:\n  author:\n    - octocat\n",  # a list
        "applies_to:\n  author: '  '\n",  # whitespace only
        "applies_to:\n  author: 42\n",  # non-string
    ],
)
def test_invalid_applies_to_author(tree: SkillTree, author: str) -> None:
    tree.frontmatter(extra=author)
    assert only(tree.validate()) == (
        ALPHA + "`applies_to.author` must be a single non-empty GitHub handle string, "
        "not a list (SPEC §1.10.1)"
    )


def test_applies_to_author_rejects_a_leading_at(tree: SkillTree) -> None:
    tree.frontmatter(extra="applies_to:\n  author: '@octocat'\n")
    assert only(tree.validate()) == (
        ALPHA + "`applies_to.author` must not include a leading '@' (SPEC §1.10.1)"
    )


def test_valid_applies_to_author(tree: SkillTree) -> None:
    tree.frontmatter(extra="applies_to:\n  author: octocat\n")
    assert tree.validate() == []


# --- Several rules at once -------------------------------------------------


def test_errors_accumulate_across_rules_and_skills(tree: SkillTree) -> None:
    # One skill can trip several rules, and a broken skill never stops the
    # walk -- the gate reports the whole tree in directory order.
    tree.skill("alpha", "---\nname: beta\n---\n\nno title\n")
    tree.valid_skill("gamma")
    tree.skill("zeta")
    assert tree.validate() == [
        ALPHA + "frontmatter name='beta' does not match directory name 'alpha'",
        ALPHA + "frontmatter is missing a non-empty `description:` field",
        ALPHA + "body has no top-level `# Title` heading",
        "::error file=skills/zeta/SKILL.md::missing SKILL.md",
    ]


# --- docs/placement-map.json -----------------------------------------------

PM = "::error file=docs/placement-map.json::"

# `family` and `owns` joined ENTRY when the generated catalog directory landed
# (#229). They are REQUIRED, so a baseline without them is not a valid map --
# which is the point: a skill cannot be added without saying where it sits in
# the directory and what it owns.
ENTRY = {
    "authoring_home": "catalog",
    "distribution": "default-on",
    "subscribers": ["logmind"],
    "family": "fam",
    "owns": "a fragment",
}
FAMILIES = [{"id": "fam", "title": "A family", "routes": "What this family covers."}]


def valid_map(**skills: dict) -> dict:
    return {
        "version": 1,
        "updated": "2026-08-14",
        "families": FAMILIES,
        "skills": skills or {"alpha": ENTRY},
    }


def test_absent_placement_map_is_tolerated(tree: SkillTree) -> None:
    tree.valid_skill()
    assert tree.validate() == []


def test_valid_placement_map(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map(valid_map())
    assert tree.validate() == []


def test_placement_map_must_be_valid_json(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map(raw="{not json")
    assert only(tree.validate()).startswith(
        PM + "docs/placement-map.json is not valid JSON: "
    )


def test_placement_map_top_level_must_be_an_object(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map([1, 2, 3])
    assert only(tree.validate()) == (
        PM + "top level of docs/placement-map.json must be a JSON object with "
        "`version`, `updated`, `skills`"
    )


@pytest.mark.parametrize("version", ["1", 1.0, None, True])
def test_placement_map_version_must_be_an_int(tree: SkillTree, version: object) -> None:
    # `True` is an int to Python, so the rule excludes bools explicitly.
    tree.valid_skill()
    tree.placement_map(
        {"version": version, "updated": "2026-08-14", "families": FAMILIES,
         "skills": {"alpha": ENTRY}}
    )
    assert only(tree.validate()) == PM + "`version` must be an int"


@pytest.mark.parametrize("updated", ["", "   ", 20260814, None])
def test_placement_map_updated_must_be_a_non_empty_string(tree: SkillTree, updated: object) -> None:
    tree.valid_skill()
    tree.placement_map(
        {"version": 1, "updated": updated, "families": FAMILIES,
         "skills": {"alpha": ENTRY}}
    )
    assert only(tree.validate()) == PM + "`updated` must be a non-empty string"


def test_placement_map_skills_must_be_an_object(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map(
        {"version": 1, "updated": "2026-08-14", "families": FAMILIES, "skills": []}
    )
    assert only(tree.validate()) == (
        PM + "`skills` must be an object mapping skill name -> metadata"
    )


def test_placement_map_entry_must_be_an_object(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map(valid_map(alpha="catalog"))
    assert only(tree.validate()) == (
        PM + "skills.alpha must be an object (unknown per-skill keys are tolerated; "
        "the value itself must still be a mapping)"
    )


@pytest.mark.parametrize(
    "home", ["repo-mirrored:Bad_Name", "repo-mirrored:", "elsewhere", None, 7]
)
def test_placement_map_invalid_authoring_home(tree: SkillTree, home: object) -> None:
    tree.valid_skill()
    tree.placement_map(valid_map(alpha={**ENTRY, "authoring_home": home}))
    assert only(tree.validate()) == (
        PM + f"skills.alpha.authoring_home={home!r} must match "
        r"^(catalog|undecided|repo-mirrored:[a-z0-9-]+)$"
    )


@pytest.mark.parametrize("home", ["catalog", "undecided", "repo-mirrored:clud-bug"])
def test_placement_map_valid_authoring_home(tree: SkillTree, home: str) -> None:
    tree.valid_skill()
    tree.placement_map(valid_map(alpha={**ENTRY, "authoring_home": home}))
    assert tree.validate() == []


@pytest.mark.parametrize("distribution", ["everywhere", None, ""])
def test_placement_map_invalid_distribution(tree: SkillTree, distribution: object) -> None:
    tree.valid_skill()
    tree.placement_map(valid_map(alpha={**ENTRY, "distribution": distribution}))
    assert only(tree.validate()) == (
        PM + f"skills.alpha.distribution={distribution!r} is not one of "
        "['catalog-only', 'default-on', 'opt-in']"
    )


@pytest.mark.parametrize("distribution", ["default-on", "opt-in", "catalog-only"])
def test_placement_map_valid_distribution(tree: SkillTree, distribution: str) -> None:
    tree.valid_skill()
    tree.placement_map(valid_map(alpha={**ENTRY, "distribution": distribution}))
    assert tree.validate() == []


@pytest.mark.parametrize("subscribers", ["logmind", None, [1], [None]])
def test_placement_map_subscribers_must_be_a_list_of_strings(
    tree: SkillTree, subscribers: object
) -> None:
    tree.valid_skill()
    tree.placement_map(valid_map(alpha={**ENTRY, "subscribers": subscribers}))
    assert only(tree.validate()) == PM + "skills.alpha.subscribers must be a list of strings"


def test_placement_map_empty_subscribers_is_allowed(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map(valid_map(alpha={**ENTRY, "subscribers": []}))
    assert tree.validate() == []


def test_placement_map_keys_reconcile_against_skills_dirs(tree: SkillTree) -> None:
    # This is the rule that makes "the map is kept in sync" true rather than
    # aspirational: missing and extra are reported separately, by name.
    tree.valid_skill("alpha")
    tree.valid_skill("beta")
    tree.placement_map(valid_map(alpha=ENTRY, ghost=ENTRY))
    assert tree.validate() == [
        PM + "docs/placement-map.json is missing an entry for: beta",
        PM + "docs/placement-map.json has an entry for non-existent skills/ dir(s): ghost",
    ]


def test_placement_map_reconciliation_lists_every_name(tree: SkillTree) -> None:
    tree.valid_skill("alpha")
    tree.valid_skill("beta")
    tree.valid_skill("gamma")
    tree.placement_map(valid_map(ghost=ENTRY, phantom=ENTRY))
    assert tree.validate() == [
        PM + "docs/placement-map.json is missing an entry for: alpha, beta, gamma",
        PM + "docs/placement-map.json has an entry for non-existent skills/ dir(s): "
        "ghost, phantom",
    ]


def test_placement_map_reconciliation_counts_dirs_without_a_skill_md(tree: SkillTree) -> None:
    # Reconciliation is against DIRECTORY names, not SKILL.md files -- a dir
    # missing its SKILL.md is still expected in the map.
    tree.valid_skill("alpha")
    tree.skill("beta")
    tree.placement_map(valid_map(alpha=ENTRY, beta=ENTRY))
    assert only(tree.validate()) == "::error file=skills/beta/SKILL.md::missing SKILL.md"


def test_malformed_placement_map_json_skips_the_shape_rules(tree: SkillTree) -> None:
    # A parse failure yields exactly one error -- reconciliation cannot run
    # against an object that does not exist.
    tree.valid_skill("alpha")
    tree.valid_skill("beta")
    tree.placement_map(raw="{not json")
    assert len(tree.validate()) == 1


# --- the generated catalog directory (#229) ---------------------------------
#
# Two gates, and they catch different halves. The `families`/`family`/`owns`
# rules stop a skill from being ADDED without a directory line; the staleness
# rule stops the directory from being left behind once one is. Either alone
# leaves the drift representable.

import gen_skill_directory  # noqa: E402  -- conftest put .github/scripts on the path

DIR_MD = f"::error file=skills/{gen_skill_directory.DIRECTORY_SLUG}/SKILL.md::"


def test_families_must_be_a_non_empty_list(tree: SkillTree) -> None:
    tree.valid_skill()
    m = valid_map()
    del m["families"]
    tree.placement_map(m)
    # The skill's own `family` becomes unresolvable, so two errors is correct:
    # the missing list, and the entry that now names nothing.
    assert tree.validate() == [
        PM + "`families` must be a non-empty list of {id, title, routes} objects. "
        "It is the directory's grouping; without it every skill's `family` is "
        "unresolvable and the generated directory is a flat list of names.",
        PM + "skills.alpha.family='fam' is not a declared family. Declared: (none)",
    ]


@pytest.mark.parametrize("families", [[], {}, "fam", None])
def test_families_rejects_non_lists_and_empties(tree: SkillTree, families: object) -> None:
    tree.valid_skill()
    tree.placement_map({**valid_map(), "families": families})
    assert tree.validate()[0].startswith(PM + "`families` must be a non-empty list")


def test_family_entry_must_be_an_object(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map({**valid_map(), "families": ["fam"]})
    assert tree.validate() == [
        PM + "families[0] must be an object with `id`, `title` and `routes`",
        PM + "skills.alpha.family='fam' is not a declared family. Declared: (none)",
    ]


@pytest.mark.parametrize("fid", ["Fam", "1fam", "fam_ily", "", None, 7])
def test_family_id_must_match_the_slug_regex(tree: SkillTree, fid: object) -> None:
    tree.valid_skill()
    tree.placement_map(
        {**valid_map(), "families": [{"id": fid, "title": "T", "routes": "R"}]}
    )
    assert tree.validate()[0] == (
        PM + f"families[0].id={fid!r} must match ^[a-z][a-z0-9-]{{0,62}}$"
    )


def test_a_family_id_declared_twice_is_rejected(tree: SkillTree) -> None:
    # Two entries with one id would list every skill in it twice.
    tree.valid_skill()
    tree.placement_map(
        {
            **valid_map(),
            "families": [
                {"id": "fam", "title": "T", "routes": "R"},
                {"id": "fam", "title": "T2", "routes": "R2"},
            ],
        }
    )
    assert only(tree.validate()) == (
        PM + "families[1].id='fam' is declared twice; a skill naming it would be "
        "listed twice"
    )


@pytest.mark.parametrize("key", ["title", "routes"])
@pytest.mark.parametrize("val", ["", "   ", None, 7])
def test_family_title_and_routes_must_be_non_empty_strings(
    tree: SkillTree, key: str, val: object
) -> None:
    tree.valid_skill()
    fam = {"id": "fam", "title": "T", "routes": "R", key: val}
    tree.placement_map({**valid_map(), "families": [fam]})
    assert only(tree.validate()) == (
        PM + f"families[0].{key} must be a non-empty string"
    )


def test_no_family_may_be_declared_without_a_skill(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map(
        {
            **valid_map(),
            "families": [
                {"id": "fam", "title": "T", "routes": "R"},
                {"id": "ghost", "title": "T", "routes": "R"},
                {"id": "phantom", "title": "T", "routes": "R"},
            ],
        }
    )
    assert only(tree.validate()) == (
        PM + "`families` declares ghost, phantom but no skill lists them. Delete "
        "the family or give a skill that `family`."
    )


def test_a_malformed_entry_suppresses_the_dead_family_report(tree: SkillTree) -> None:
    # That entry's `family` is unknowable, so "no skill lists it" would be a
    # second annotation derived from the first defect rather than a finding.
    tree.valid_skill()
    tree.placement_map(valid_map(alpha="catalog"))
    assert only(tree.validate()) == (
        PM + "skills.alpha must be an object (unknown per-skill keys are "
        "tolerated; the value itself must still be a mapping)"
    )


@pytest.mark.parametrize("family", ["", "   ", None, 7, []])
def test_family_is_required_on_every_entry(tree: SkillTree, family: object) -> None:
    tree.valid_skill()
    tree.valid_skill("beta")  # keeps `fam` alive, so only the one rule fires
    tree.placement_map(valid_map(alpha={**ENTRY, "family": family}, beta=ENTRY))
    assert only(tree.validate()).startswith(
        PM + "skills.alpha.family must be a non-empty string"
    )


def test_family_must_name_a_declared_family(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.valid_skill("beta")
    tree.placement_map(valid_map(alpha={**ENTRY, "family": "nowhere"}, beta=ENTRY))
    assert only(tree.validate()) == (
        PM + "skills.alpha.family='nowhere' is not a declared family. Declared: fam"
    )


@pytest.mark.parametrize("owns", ["", "   ", None, 7, []])
def test_owns_is_required_on_every_entry(tree: SkillTree, owns: object) -> None:
    tree.valid_skill()
    tree.placement_map(valid_map(alpha={**ENTRY, "owns": owns}))
    assert only(tree.validate()).startswith(
        PM + "skills.alpha.owns must be a non-empty string"
    )


def test_owns_at_exactly_the_cap_is_allowed(tree: SkillTree) -> None:
    # The boundary either side, in one pair -- a cap tested only from the far
    # side does not pin where it is.
    tree.valid_skill()
    tree.placement_map(
        valid_map(alpha={**ENTRY, "owns": "x" * gen_skill_directory.OWNS_MAX_BYTES})
    )
    assert tree.validate() == []


def test_owns_one_byte_over_the_cap_is_rejected(tree: SkillTree) -> None:
    tree.valid_skill()
    over = "x" * (gen_skill_directory.OWNS_MAX_BYTES + 1)
    tree.placement_map(valid_map(alpha={**ENTRY, "owns": over}))
    assert only(tree.validate()).startswith(
        PM + f"skills.alpha.owns is {gen_skill_directory.OWNS_MAX_BYTES + 1} bytes, "
        f"over the {gen_skill_directory.OWNS_MAX_BYTES}-byte cap by 1"
    )


def test_owns_is_measured_in_bytes_not_characters(tree: SkillTree) -> None:
    # The cap exists to bound the RENDERED body, which is bytes. An em dash is
    # three of them, so a character count would let a line through 2x over.
    tree.valid_skill()
    owns = "—" * gen_skill_directory.OWNS_MAX_BYTES  # 32 chars, 96 bytes
    tree.placement_map(valid_map(alpha={**ENTRY, "owns": owns}))
    assert only(tree.validate()).startswith(
        PM + f"skills.alpha.owns is {3 * gen_skill_directory.OWNS_MAX_BYTES} bytes"
    )


# --- staleness -------------------------------------------------------------


def test_absent_directory_skill_is_tolerated(tree: SkillTree) -> None:
    # A tree that publishes no directory is not in breach of anything.
    tree.valid_skill()
    tree.placement_map(valid_map())
    assert tree.validate() == []


def test_a_current_directory_passes(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.control_skill()
    tree.placement_map(
        valid_map(
            alpha=ENTRY,
            control=ENTRY,
            **{gen_skill_directory.DIRECTORY_SLUG: ENTRY},
        )
    )
    tree.directory()
    assert tree.validate() == []


def test_a_skill_added_without_regenerating_fails(tree: SkillTree) -> None:
    """The case the gate exists for, and the one the README table never had."""
    tree.valid_skill()
    tree.control_skill()
    tree.placement_map(
        valid_map(
            alpha=ENTRY,
            control=ENTRY,
            **{gen_skill_directory.DIRECTORY_SLUG: ENTRY},
        )
    )
    tree.directory()
    assert tree.validate() == []  # control: current before the skill lands

    tree.valid_skill("beta")
    tree.placement_map(
        valid_map(
            alpha=ENTRY,
            beta=ENTRY,
            control=ENTRY,
            **{gen_skill_directory.DIRECTORY_SLUG: ENTRY},
        )
    )
    assert only(tree.validate()).startswith(
        DIR_MD + "this body is GENERATED and no longer matches"
    )


def test_a_hand_edited_directory_fails(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.control_skill()
    tree.placement_map(
        valid_map(
            alpha=ENTRY,
            control=ENTRY,
            **{gen_skill_directory.DIRECTORY_SLUG: ENTRY},
        )
    )
    body = gen_skill_directory.render(
        tree.base / "skills", tree.base / "docs" / "placement-map.json"
    )
    tree.directory(body=body.replace("- `alpha`", "- `alpha-renamed-by-hand`"))
    assert only(tree.validate()).startswith(
        DIR_MD + "this body is GENERATED and no longer matches"
    )


def test_a_directory_with_no_source_cannot_be_verified(tree: SkillTree) -> None:
    # Presence without a usable source is the worst state: an unverifiable
    # directory reads exactly like a verified one.
    tree.valid_skill()
    tree.control_skill()
    tree.directory(body="\n# Directory\n\nHand-written.\n")
    assert only(tree.validate()).startswith(
        DIR_MD + "the directory cannot be rendered, so it cannot be verified"
    )


def test_a_directory_without_frontmatter_is_reported_once(tree: SkillTree) -> None:
    # The per-skill loop already files "missing YAML frontmatter"; a second
    # annotation for the same defect would only make the count lie.
    tree.valid_skill()
    tree.control_skill()
    tree.placement_map(
        valid_map(
            alpha=ENTRY,
            control=ENTRY,
            **{gen_skill_directory.DIRECTORY_SLUG: ENTRY},
        )
    )
    tree.skill(gen_skill_directory.DIRECTORY_SLUG, "# Directory\n\nNo frontmatter.\n")
    assert only(tree.validate()) == (
        DIR_MD + "missing YAML frontmatter (must start with --- ... --- block)"
    )


def test_an_oversized_directory_is_reported_by_the_gate(
    tree: SkillTree, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The gate carries the size refusal too, not only the generator.

    Without it the only thing between the catalog and a truncated directory is
    somebody remembering to run the generator by hand -- and the failure the
    truncation causes is skills that look like they do not exist, which is the
    failure this skill exists to prevent.
    """
    tree.valid_skill()
    tree.control_skill()
    tree.placement_map(
        valid_map(
            alpha=ENTRY,
            control=ENTRY,
            **{gen_skill_directory.DIRECTORY_SLUG: ENTRY},
        )
    )
    tree.directory()
    assert tree.validate() == []  # control: fine at the real reserve

    monkeypatch.setattr(gen_skill_directory, "MAX_BODY_BYTES", 10)
    assert only(tree.validate()).startswith(DIR_MD + "the rendered directory is")


# --- retirement: the one meaning-level rule ---------------------------------
#
# The byte comparison above cannot see this class at all. `family` and `owns`
# are editorial text, so the directory and the map agree with each other by
# construction and a skill filed as live after it was retired passes every
# rule. It shipped that way: `skillforge` sat under "The catalog itself"
# reading "scaffolding a new skill" for the whole migration window, routing
# agents INTO guidance its own frontmatter told them to stop following.

SUPERSEDED_DESC = "SUPERSEDED by `beta` — kept for the migration window."


def superseded_skill(tree: SkillTree, name: str = "alpha", desc: str = SUPERSEDED_DESC) -> None:
    tree.skill(name, f"---\nname: {name}\ndescription: {desc}\n---\n\n# T\n\nBody.\n")


def test_a_superseded_skill_filed_as_live_is_reported(tree: SkillTree) -> None:
    superseded_skill(tree)
    tree.placement_map(valid_map(alpha=ENTRY))
    assert only(tree.validate()) == (
        PM + "skills.alpha.family='fam', but skills/alpha/SKILL.md announces itself "
        "as SUPERSEDED. A retired skill listed among live ones is a directory "
        "routing agents to guidance its own author told them to stop following. "
        "File it under 'deprecated' and point `owns` at the successors."
    )


def test_a_superseded_skill_in_the_deprecated_family_passes(tree: SkillTree) -> None:
    """Control for the rule above: the fix the message names actually clears it."""
    superseded_skill(tree)
    tree.placement_map(
        {
            **valid_map(alpha={**ENTRY, "family": "deprecated"}),
            "families": [{"id": "deprecated", "title": "D", "routes": "R"}],
        }
    )
    assert tree.validate() == []


def test_a_live_skill_is_not_mistaken_for_a_retired_one(tree: SkillTree) -> None:
    """The other control. A detector that fired on everything would 'prove'
    the rule works while telling you nothing.
    """
    tree.valid_skill()
    tree.placement_map(valid_map(alpha=ENTRY))
    assert tree.validate() == []


@pytest.mark.parametrize(
    "desc",
    [
        "SUPERSEDED by `beta`.",
        "SUPERSEDED — see beta, which owns this now.",
        "SUPERSEDED (see beta).",
    ],
)
def test_the_superseded_marker_is_read_at_the_start_of_the_description(
    tree: SkillTree, desc: str
) -> None:
    superseded_skill(tree, desc=desc)
    tree.placement_map(valid_map(alpha=ENTRY))
    assert "announces itself as SUPERSEDED" in only(tree.validate())


@pytest.mark.parametrize(
    "desc",
    [
        "Use when a rule was SUPERSEDED by another one.",
        "Judging whether guidance is superseded.",
    ],
)
def test_the_word_superseded_mid_sentence_is_not_a_retirement(
    tree: SkillTree, desc: str
) -> None:
    """A skill ABOUT retirement is not a retired skill. The marker is a
    headline, so it is matched as one.
    """
    superseded_skill(tree, desc=desc)
    tree.placement_map(valid_map(alpha=ENTRY))
    assert tree.validate() == []


@pytest.mark.parametrize("extra", ["superseded_by: beta\n", "status: superseded\n"])
def test_the_reserved_retirement_keys_count_too(tree: SkillTree, extra: str) -> None:
    """`superseded_by` and `status` are RESERVED-and-tolerated (SPEC §1.10.1).
    A detector that knew only the description would go quiet the first time
    somebody used the field the spec actually provides.
    """
    tree.frontmatter("alpha", extra=extra)
    tree.placement_map(valid_map(alpha=ENTRY))
    assert "announces itself as SUPERSEDED" in only(tree.validate())


# --- README membership (#229's first problem) -------------------------------
#
# The table is complete by diligence and nothing keeps it that way, in the file
# most readers meet first. MEMBERSHIP only: the purpose column is prose with
# room for sentences the byte-capped directory cannot afford, and generating it
# from a 32-byte fragment would make the README worse to make it derived.


def readme(tree: SkillTree, *names: str) -> None:
    rows = "\n".join(f"| [`{n}`](skills/{n}/SKILL.md) | Purpose. |" for n in names)
    (tree.base / "README.md").write_text(f"# Catalog\n\n{rows}\n", encoding="utf-8")


def test_absent_readme_is_tolerated(tree: SkillTree) -> None:
    tree.valid_skill()
    assert tree.validate() == []


def test_a_readme_naming_every_skill_passes(tree: SkillTree) -> None:
    tree.valid_skill("alpha")
    tree.valid_skill("beta")
    readme(tree, "alpha", "beta")
    assert tree.validate() == []


def test_a_skill_missing_from_the_readme_is_reported(tree: SkillTree) -> None:
    tree.valid_skill("alpha")
    tree.valid_skill("beta")
    readme(tree, "alpha")
    assert only(tree.validate()) == (
        "::error file=README.md::the README does not link skills/<name>/SKILL.md "
        "for: beta. It is the first listing most readers meet, and a skill missing "
        "from it reads as a skill that does not exist -- which is what somebody "
        "then writes again. Add a row to the table."
    )


def test_a_readme_row_outliving_its_skill_is_reported(tree: SkillTree) -> None:
    tree.valid_skill("alpha")
    readme(tree, "alpha", "retired")
    assert only(tree.validate()).startswith(
        "::error file=README.md::the README links skills/<name>/SKILL.md for dir(s) "
        "that do not exist: retired"
    )


def test_a_mention_without_a_link_does_not_count(tree: SkillTree) -> None:
    """The probe is the link, not the name: prose can mention a skill it does
    not route to, and a listing that cannot be clicked is not a listing.
    """
    tree.valid_skill("alpha")
    (tree.base / "README.md").write_text("# Catalog\n\nWe have alpha.\n", encoding="utf-8")
    assert "does not link" in only(tree.validate())
