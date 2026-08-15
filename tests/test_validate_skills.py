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
    assert "There is no exception list." in error


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
ENTRY = {"authoring_home": "catalog", "distribution": "default-on", "subscribers": ["logmind"]}


def valid_map(**skills: dict) -> dict:
    return {"version": 1, "updated": "2026-08-14", "skills": skills or {"alpha": ENTRY}}


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
    tree.placement_map({"version": version, "updated": "2026-08-14", "skills": {"alpha": ENTRY}})
    assert only(tree.validate()) == PM + "`version` must be an int"


@pytest.mark.parametrize("updated", ["", "   ", 20260814, None])
def test_placement_map_updated_must_be_a_non_empty_string(tree: SkillTree, updated: object) -> None:
    tree.valid_skill()
    tree.placement_map({"version": 1, "updated": updated, "skills": {"alpha": ENTRY}})
    assert only(tree.validate()) == PM + "`updated` must be a non-empty string"


def test_placement_map_skills_must_be_an_object(tree: SkillTree) -> None:
    tree.valid_skill()
    tree.placement_map({"version": 1, "updated": "2026-08-14", "skills": []})
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
