"""Shared fixtures for the `.github/scripts` test suite.

`validate_skills` lives in `.github/scripts/`, which is not a package and is
not importable by default -- put it on `sys.path` here rather than in every
test module.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = REPO_ROOT / ".github" / "scripts"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import skill_version  # noqa: E402  -- import needs the sys.path line above
import validate_skills  # noqa: E402  -- import needs the sys.path line above
import gen_skill_directory  # noqa: E402  -- same


# A SKILL.md that passes every rule. Tests break exactly one thing at a time
# off this baseline, so a failure names the rule that fired. Carries the
# house's five sections (in validate_skills.HOUSE_SECTIONS order) since
# house_structure_errors joined "every rule" -- a `tree.valid_skill()` paired
# with a placement map (most of the placement-map suite) must satisfy it
# regardless of which `family` that map assigns, or every one of those tests
# would need its own exemption wiring just to stay focused on what it
# actually tests.
VALID_SKILL = """---
name: {name}
description: What this skill does and when to use it.
---

# Title

Body.

## When to use

- When this applies.

## When NOT to use

- When it doesn't.

## Verification

- How to tell it worked.

## Cross-references

- Nothing to cross-reference in this fixture.

## Sources

- None.
"""


class SkillTree:
    """A throwaway repo-shaped tree: `skills/<name>/SKILL.md` plus an optional
    `docs/placement-map.json`. The fixture chdirs into it, because the gate
    resolves both paths relative to the cwd.
    """

    def __init__(self, base: Path) -> None:
        self.base = base

    def skill(self, name: str, text: str | None = None) -> Path:
        """Create `skills/<name>/`. `text=None` leaves the dir without a
        SKILL.md (the "missing SKILL.md" case).
        """
        d = self.base / "skills" / name
        d.mkdir(parents=True, exist_ok=True)
        if text is not None:
            (d / "SKILL.md").write_text(text, encoding="utf-8")
        return d

    def valid_skill(self, name: str = "alpha") -> Path:
        return self.skill(name, VALID_SKILL.format(name=name))

    def frontmatter(self, name: str = "alpha", extra: str = "", body: str = "\n# Title\n\nBody.\n") -> Path:
        """A valid skill with `extra` YAML lines spliced into the frontmatter."""
        fm = f"---\nname: {name}\ndescription: What this skill does.\n{extra}---\n"
        return self.skill(name, fm + body)

    def placement_map(self, obj: object = None, raw: str | None = None) -> Path:
        """Write `docs/placement-map.json` from an object (JSON-encoded) or
        from `raw` bytes-as-text (for the malformed-JSON case).
        """
        import json

        d = self.base / "docs"
        d.mkdir(parents=True, exist_ok=True)
        path = d / "placement-map.json"
        path.write_text(raw if raw is not None else json.dumps(obj), encoding="utf-8")
        return path

    def control_skill(self, name: str = "control") -> Path:
        """A skill whose DESCRIPTION carries the "deliberately not here"
        section's CONTROL term. The generator refuses to render without one --
        an uncontrolled zero is not a measurement -- so any tree holding the
        directory needs this. It is a fixture requirement that exists because
        the guard is real, not a workaround for it.

        In the description and not the body: the probe scan reads each skill's
        trigger surface (name + frontmatter), because that is what decides
        whether an agent ever finds a skill -- and because scanning bodies let
        one skill's cross-reference redden the whole gate.
        """
        return self.skill(
            name,
            VALID_SKILL.format(name=name).replace(
                "description: What this skill does",
                "description: What this skill does about "
                f"{gen_skill_directory.NOT_HERE_CONTROL},",
            ),
        )

    def directory(self, body: str | None = None) -> Path:
        """Create `skills/<DIRECTORY_SLUG>/SKILL.md`.

        `body=None` writes what the generator renders for the tree AS IT IS AT
        THIS MOMENT -- so a test that adds a skill afterwards has a stale
        directory, which is precisely the case the gate exists for. Order the
        calls accordingly.
        """
        # The directory dir has to exist BEFORE the render: the directory is a
        # skill like any other and lists itself, so rendering first and
        # creating second produces a body that is stale the instant it is
        # written. Same self-reference the real generator handles.
        self.skill(gen_skill_directory.DIRECTORY_SLUG)
        if body is None:
            body = gen_skill_directory.render(
                self.base / "skills", self.base / "docs" / "placement-map.json"
            )
        head = f"---\nname: {gen_skill_directory.DIRECTORY_SLUG}\ndescription: d\n---"
        return self.skill(gen_skill_directory.DIRECTORY_SLUG, head + body)

    _auto_index: str | None = None
    """The last index this scaffold wrote, or None. See validate()."""

    def validate(self) -> list[str]:
        """Run the gate over this tree and return its error annotations.

        `docs/skill-versions.json` absence is now an error to the gate
        itself (presence-with-defects is not the only failure any more --
        see `test_an_absent_index_is_rejected`), but most tests in this
        suite exercise a per-skill rule that has nothing to do with that
        gate. So: auto-provision a matching index, computed fresh at THIS
        call from whatever `skills/` currently holds -- a mutation made
        after the skill was created is reflected too, so this never trips a
        spurious currency error -- UNLESS a test already wrote its own (see
        `index_for()` in test_validate_skills_version.py, always called
        after every skill() call so it always wins). A test that wants to
        see the gate with no scaffolding at all calls `validate_skills.run()`
        directly instead of going through here.
        """
        import json

        versions_path = self.base / "docs" / "skill-versions.json"
        current = {
            md.parent.name: {
                "current": skill_version.digest(md.read_bytes()),
                "version": skill_version.stamped_version(md.read_bytes()),
                "history": [],
            }
            for md in sorted((self.base / "skills").glob("*/SKILL.md"))
        }
        payload = json.dumps({"version": 1, "skills": current}, sort_keys=True)

        # Refresh only what WE wrote. A test that writes its own index must keep
        # it -- that is how the currency gate gets exercised at all -- so
        # ownership is decided by content, not by a flag another helper would
        # have to remember to clear: if the file on disk is byte-identical to
        # the scaffold we last wrote, it is still ours.
        #
        # `if not exists` was not enough: a test that calls validate() twice
        # (once as a control, then again after adding a skill) got an index
        # frozen at the first call, so the second run failed the currency gate
        # on scaffolding rather than on the rule under test.
        if not versions_path.exists() or self._auto_index == versions_path.read_text(
            encoding="utf-8"
        ):
            versions_path.parent.mkdir(parents=True, exist_ok=True)
            versions_path.write_text(payload, encoding="utf-8")
            self._auto_index = payload
        return validate_skills.run(Path("skills"))


@pytest.fixture
def tree(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SkillTree:
    monkeypatch.chdir(tmp_path)
    return SkillTree(tmp_path)
