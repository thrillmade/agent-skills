"""`validate_skills.py`'s placement-map gate must never look at an
`agents/`-prefixed key.

SPEC §5.1's own example (`"agents/simplifier": {...}`) names one placement
map for both skills and agent roster entries -- but `family`/`owns` are
generated-DIRECTORY concepts (`skills/finding-a-catalog-skill/SKILL.md`)
that do not apply to a role, and the 1:1 reconcile below is against
`skills/` directory names, which an `agents/<name>` key was never meant to
equal. Before this file's `AGENTS_PREFIX` carve-out landed, adding the
first `agents/` entry to `docs/placement-map.json` failed CI on both counts
-- exactly the blocker agent-skills#180 names. These tests pin the fix:
`validate_agents.py` (see `tests/test_validate_agents.py`) owns that
namespace's shape and its own 1:1 reconcile against `.claude/agents/`; this
file only proves `validate_skills.py` gets out of its way.
"""

from __future__ import annotations

from conftest import SkillTree

# Reuses test_validate_skills.py's own fixture shape (`family`/`owns`
# REQUIRED for a skills/-namespaced entry) rather than redefining it, so a
# change to that baseline cannot drift silently between the two files.
FAMILIES = [{"id": "fam", "title": "A family", "routes": "What this family covers."}]
SKILL_ENTRY = {
    "authoring_home": "catalog",
    "distribution": "default-on",
    "subscribers": ["logmind"],
    "family": "fam",
    "owns": "a fragment",
}

# The minimal shape SPEC §5.1's own example uses for an agent entry -- no
# `family`, no `owns`.
AGENT_ENTRY = {"authoring_home": "catalog", "distribution": "catalog-only", "subscribers": []}


def valid_map(**skills: dict) -> dict:
    return {"version": 1, "updated": "2026-09-15", "families": FAMILIES, "skills": skills}


def test_an_agent_entry_with_no_family_or_owns_is_not_an_error(tree: SkillTree) -> None:
    tree.valid_skill("alpha")
    tree.placement_map(valid_map(alpha=SKILL_ENTRY, **{"agents/builder": AGENT_ENTRY}))
    assert tree.validate() == []


def test_an_agent_entry_is_never_extra_against_skills_dirs(tree: SkillTree) -> None:
    # Before the carve-out, `agents/builder` read as "an entry for a
    # non-existent skills/ dir" -- the exact defect agent-skills#180 names.
    tree.valid_skill("alpha")
    tree.placement_map(valid_map(alpha=SKILL_ENTRY, **{"agents/builder": AGENT_ENTRY}))
    errors = tree.validate()
    assert not any("agents/builder" in e for e in errors), errors


def test_a_malformed_agent_entry_produces_no_error_here(tree: SkillTree) -> None:
    # Not this gate's business either way -- validate_agents.py owns
    # validating the SHAPE of an `agents/`-namespaced value.
    tree.valid_skill("alpha")
    tree.placement_map(valid_map(alpha=SKILL_ENTRY, **{"agents/builder": "not an object"}))
    assert tree.validate() == []


def test_a_bare_skill_entry_still_requires_family_and_owns(tree: SkillTree) -> None:
    # Regression check: the carve-out must not have loosened the rule for
    # keys that are NOT agents/-prefixed.
    tree.valid_skill("alpha")
    tree.placement_map(
        valid_map(
            alpha={
                "authoring_home": "catalog",
                "distribution": "default-on",
                "subscribers": [],
            },
            **{"agents/builder": AGENT_ENTRY},
        )
    )
    errors = tree.validate()
    assert any(e.endswith("skills.alpha.family must be a non-empty string naming one of the "
                          "`families` ids. It is what puts this skill in the generated "
                          "directory (skills/finding-a-catalog-skill/SKILL.md); without it "
                          "the skill exists and the catalog's own map does not show it.")
               for e in errors), errors
    assert any("skills.alpha.owns must be a non-empty string" in e for e in errors), errors


def test_multiple_agent_entries_are_all_exempted(tree: SkillTree) -> None:
    tree.valid_skill("alpha")
    tree.placement_map(
        valid_map(
            alpha=SKILL_ENTRY,
            **{
                "agents/builder": AGENT_ENTRY,
                "agents/scout": AGENT_ENTRY,
                "agents/skill-smith": AGENT_ENTRY,
            },
        )
    )
    assert tree.validate() == []


def test_families_dead_check_is_unaffected_by_agent_entries(tree: SkillTree) -> None:
    # An agents/ entry never carries `family`, so it can never accidentally
    # satisfy the "every declared family has a skill" check either.
    tree.valid_skill("alpha")
    tree.placement_map(
        {
            "version": 1,
            "updated": "2026-09-15",
            "families": FAMILIES + [{"id": "orphan", "title": "t", "routes": "r"}],
            "skills": {"alpha": SKILL_ENTRY, "agents/builder": AGENT_ENTRY},
        }
    )
    errors = tree.validate()
    assert any(
        "`families` declares orphan but no skill lists it" in e for e in errors
    ), errors


# The test above proves nothing about the actual escape: `AGENT_ENTRY` never
# carries `family` in the first place, so it can't demonstrate that the
# dead-family check ignores one when it IS present. Nothing in this gate
# shape-checks the `agents/` namespace (see the `continue` at the top of the
# skills_map loop), so a `family` key on an `agents/` entry is not itself an
# error -- it is simply data the dead-family check must not read. Before the
# fix, `used` was built from `skills_map.values()` with no `agents/` filter
# while `map_names` (the 1:1 reconcile below it) DID filter them -- one rule
# applied in two places, and only one of them updated. An `agents/` entry
# carrying a `family` that named an otherwise-unused id counted as "live
# use" and the dead family passed silently, defeated by a key this check was
# never meant to read.
def test_an_agent_entrys_family_field_does_not_keep_a_dead_family_alive(
    tree: SkillTree,
) -> None:
    tree.valid_skill("alpha")
    tree.placement_map(
        {
            "version": 1,
            "updated": "2026-09-15",
            "families": FAMILIES + [{"id": "orphan", "title": "t", "routes": "r"}],
            "skills": {
                "alpha": SKILL_ENTRY,
                "agents/builder": {**AGENT_ENTRY, "family": "orphan"},
            },
        }
    )
    errors = tree.validate()
    assert any(
        "`families` declares orphan but no skill lists it" in e for e in errors
    ), errors


def test_a_family_used_by_a_real_skill_is_not_reported_dead(tree: SkillTree) -> None:
    # Guards against over-correcting the fix above: filtering `agents/` keys
    # out of `used` must not stop a family from counting as used when a REAL
    # skills/ entry is the one using it -- even with an agents/ entry also
    # present in the same map.
    tree.valid_skill("alpha")
    tree.placement_map(valid_map(alpha=SKILL_ENTRY, **{"agents/builder": AGENT_ENTRY}))
    errors = tree.validate()
    assert not any("`families` declares" in e for e in errors), errors
