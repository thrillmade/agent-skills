#!/usr/bin/env python3
"""Validate every role at `.claude/agents/<name>.md` (the SPEC §2.4 roster).

Called by `.github/workflows/validate-skills.yml` on PR + push to main, as a
second step alongside `validate_skills.py`. Catches a malformed role
(missing `name`/`description`, a `name` that does not match its filename, a
`trigger` outside the enum, unparseable frontmatter) before it ships to a
subscriber, the same failure class `validate_skills.py` already catches for
`skills/*/SKILL.md`.

A role is "shaped like a skill" (SPEC §2.4): YAML frontmatter plus a body the
agent reads as its instructions. It is NOT a skill, though, and the two
gates stay separate rather than merged into one:

  - Only `name` and `description` are REQUIRED (SPEC §2.4's own table) --
    skills additionally require `version` and `digest` (SPEC §2.1). A role
    that named neither would still be valid; running it through
    `validate_skills.py`'s per-skill rules would reject it for fields the
    roster contract never asked for.
  - A role's identity is checked against its FILENAME (`.claude/agents/
    <name>.md`), not a directory name -- there is no `skills/<name>/`
    equivalent to walk.
  - `docs/placement-map.json` carries both namespaces in one file (SPEC
    §5.1: "there is one distribution system"), but `family` and `owns` are
    generated-DIRECTORY concepts (`skills/finding-a-catalog-skill/SKILL.md`)
    that do not apply to a role -- SPEC §5.1's own `"agents/simplifier"`
    example carries neither. `validate_skills.py` skips any `agents/`-
    prefixed key for exactly this reason (see its `AGENTS_PREFIX`); this
    file owns that key's shape and its 1:1 reconcile against the roster
    directory, the agent-roster half of the split.

Stdlib + PyYAML only, matching `validate_skills.py`.

Inputs:
  cwd  ROOT (`.claude/agents`) and the placement map are BOTH cwd-relative.
       Run from the repo root. `main()`'s coverage guard is what stops a run
       from the wrong directory passing vacuously -- see `coverage_errors`.

Outputs (stdout):
  One `::error file=<path>::<msg>` GitHub annotation per validation error,
  then a `::error::<N> agent role validation errors` summary -- or a single
  `OK: <N> agent roles validated cleanly.` line.

Exit codes:
  0  Every role file (and its docs/placement-map.json entry, if present)
     validated cleanly AND the coverage guard agrees the run actually saw
     the roster.
  1  Any validation error, either infra-fatal condition (no .claude/agents/
     dir, no role files), or a coverage-guard failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(".claude/agents")
PLACEMENT_MAP_PATH = Path("docs/placement-map.json")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---(?=\n|\Z)", re.DOTALL)

# SPEC §2.4's own placeholder is `<kebab-case-slug>`, the identical shape
# skills use (SPEC §2.1) -- reused rather than re-derived, since nothing
# in §2.4 says a role's slug rules differ from a skill's.
NAME_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")

# SPEC §2.4: `trigger: on-demand | on-merge | scheduled | on-release`.
TRIGGER_VALUES = {"on-demand", "on-merge", "scheduled", "on-release"}

# See validate_skills.py's own AGENTS_PREFIX -- the two files agree on this
# constant's value by convention, not by import, because each validates only
# ITS OWN namespace of the shared placement map and neither needs the other's
# rules to do it. A future refactor sharing a single `catalog_shared.py`
# module is fine; duplicating one string today is not the drift that module
# would exist to prevent.
AGENTS_PREFIX = "agents/"

AUTHORING_HOME_RE = re.compile(r"^(catalog|undecided|repo-mirrored:[a-z0-9-]+)$")
DISTRIBUTION_VALUES = {"default-on", "opt-in", "catalog-only"}


def _role_files(root: Path) -> list[Path]:
    """Every `.md` file directly under `root`, sorted. The set of things this
    gate considers a role -- SPEC §2.4: "Discovery is reading that
    directory," and nothing in §2.4 describes a nested layout the way a
    skill's own `skills/<name>/SKILL.md` does.
    """
    return sorted(root.glob("*.md"))


def run(root: Path) -> list[str]:
    """Validate every role under `root`, returning the `::error ...::` lines.

    An empty list means clean. The caller prints the lines and the summary
    -- see `main()`, which also applies `coverage_errors()` to the clean
    path so a run that validated nothing cannot pass.

    Two INFRA-FATAL conditions print and `sys.exit(1)` from here rather than
    returning: a missing `.claude/agents/` dir and one with no role files.
    They are not validation errors and carry no `::error::<N> agent role
    validation errors` summary line -- the same posture `validate_skills.py`
    takes for its own two infra-fatal conditions, preserved deliberately so
    the two gates read the same way in a CI log.
    """
    errors: list[str] = []

    if not root.exists() or not root.is_dir():
        print(f"::error::{root} directory not found at repo root")
        sys.exit(1)

    role_files = _role_files(root)
    if not role_files:
        print(f"::error::no role files under {root}")
        sys.exit(1)

    # filename (no extension) -> whether THIS run saw a validly-named role
    # there. Filled in below as each file is read; the placement-map
    # reconcile compares against this set rather than re-globbing, so it
    # can never disagree with what the per-file loop actually validated.
    role_names: set[str] = set()

    for role_path in role_files:
        prefix = str(role_path)
        stem = role_path.stem

        # `_role_files` globs `*.md` without a type filter, so a directory
        # NAMED `<name>.md` (nothing stops one existing under `.claude/agents/`)
        # reaches here too. `read_bytes()` on a directory raises
        # `IsADirectoryError` uncaught, taking the whole run down instead of
        # reporting it -- identical to the pre-existing `skill_md.read_bytes()`
        # bug at validate_skills.py:712 (same root cause: `.exists()`/glob is
        # true for a directory too), confirmed there and left alone as a
        # wider change than this file should carry. Reported and skipped
        # here, matching the UnicodeDecodeError case just below rather than
        # added to `role_names` as SPEC-valid.
        if not role_path.is_file():
            errors.append(f"::error file={prefix}::{role_path} is not a file")
            continue

        raw = role_path.read_bytes()
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError as e:
            errors.append(f"::error file={prefix}::could not read {role_path}: {e}")
            continue

        m = FRONTMATTER_RE.match(content)
        if not m:
            errors.append(
                f"::error file={prefix}::missing YAML frontmatter "
                "(must start with --- ... --- block)"
            )
            continue

        try:
            meta = yaml.safe_load(m.group(1)) or {}
        except yaml.YAMLError as e:
            errors.append(f"::error file={prefix}::frontmatter is not valid YAML: {e}")
            continue

        if not isinstance(meta, dict):
            errors.append(f"::error file={prefix}::frontmatter must be a YAML mapping")
            continue

        name = meta.get("name")
        valid_name = False
        if not name or not isinstance(name, str) or not name.strip():
            errors.append(
                f"::error file={prefix}::frontmatter is missing a non-empty `name:` field"
            )
        else:
            name = name.strip()
            if name != stem:
                errors.append(
                    f"::error file={prefix}::frontmatter name='{name}' "
                    f"does not match filename '{stem}'"
                )
            if not NAME_SLUG_RE.match(name):
                errors.append(
                    f"::error file={prefix}::frontmatter name='{name}' does not match "
                    r"the SPEC §2.4 slug regex ^[a-z][a-z0-9-]{0,62}$"
                )
            else:
                valid_name = True

        description = meta.get("description")
        if not description or not isinstance(description, str) or not description.strip():
            errors.append(
                f"::error file={prefix}::frontmatter is missing a non-empty `description:` field"
            )

        # SPEC §2.4: `trigger` is OPTIONAL, defaulting to `on-demand` --
        # enforced only when present, the same posture `kind`/`source` have
        # in validate_skills.py.
        trigger = meta.get("trigger")
        if trigger is not None and trigger not in TRIGGER_VALUES:
            errors.append(
                f"::error file={prefix}::`trigger: {trigger!r}` is not one of "
                f"{sorted(TRIGGER_VALUES)} (SPEC §2.4)"
            )

        # A role with no top-level H1 is tolerated -- unlike a skill, SPEC
        # §2.4 makes no body-shape claim beyond "a body the agent reads as
        # its instructions," so there is no rule here to enforce.

        if valid_name:
            role_names.add(name)

    errors.extend(placement_map_errors(role_names))
    return errors


def placement_map_errors(role_names: set[str]) -> list[str]:
    """Validate the `agents/*` slice of `docs/placement-map.json` and
    reconcile it 1:1 against `role_names` (the roles THIS run actually
    validated -- see `run`).

    Mirrors `validate_skills.py`'s own placement-map posture exactly:
    absence is tolerated (the file may not exist yet, or may be authored by
    a parallel agent); a JSON parse failure is reported once and nothing
    further is checked, because there is no object left to reconcile
    against.

    Every other key in the file (a bare skill slug, or anything not
    prefixed `agents/`) is `validate_skills.py`'s to validate -- this
    function reads the same file but only ever looks at its own slice.
    """
    if not PLACEMENT_MAP_PATH.exists():
        return []

    prefix = str(PLACEMENT_MAP_PATH)
    try:
        text = PLACEMENT_MAP_PATH.read_text(encoding="utf-8")
    except OSError as e:
        return [f"::error file={prefix}::could not read {PLACEMENT_MAP_PATH}: {e}"]

    try:
        pm = json.loads(text)
    except json.JSONDecodeError as e:
        return [f"::error file={prefix}::{PLACEMENT_MAP_PATH} is not valid JSON: {e}"]

    if not isinstance(pm, dict):
        # Malformed at the top level -- validate_skills.py already reports
        # this defect in full; nothing here duplicates it.
        return []

    skills_map = pm.get("skills")
    if not isinstance(skills_map, dict):
        # Same reasoning: validate_skills.py already reports "`skills` must
        # be an object...".
        return []

    errors: list[str] = []
    map_role_names: set[str] = set()

    for slug, meta in skills_map.items():
        if not slug.startswith(AGENTS_PREFIX):
            continue

        role_name = slug[len(AGENTS_PREFIX):]
        map_role_names.add(role_name)

        if not isinstance(meta, dict):
            errors.append(
                f"::error file={prefix}::skills.{slug} must be an object "
                "(unknown per-entry keys are tolerated; the value itself "
                "must still be a mapping)"
            )
            continue

        authoring_home = meta.get("authoring_home")
        if not isinstance(authoring_home, str) or not AUTHORING_HOME_RE.match(authoring_home):
            errors.append(
                f"::error file={prefix}::skills.{slug}.authoring_home="
                f"{authoring_home!r} must match "
                r"^(catalog|undecided|repo-mirrored:[a-z0-9-]+)$"
            )

        distribution = meta.get("distribution")
        if distribution not in DISTRIBUTION_VALUES:
            errors.append(
                f"::error file={prefix}::skills.{slug}.distribution="
                f"{distribution!r} is not one of {sorted(DISTRIBUTION_VALUES)}"
            )

        subscribers = meta.get("subscribers")
        if not isinstance(subscribers, list) or not all(
            isinstance(s, str) for s in subscribers
        ):
            errors.append(
                f"::error file={prefix}::skills.{slug}.subscribers must be "
                "a list of strings"
            )

    # Map keys must EXACTLY equal the .claude/agents/ role names -- the same
    # 1:1 reconcile validate_skills.py runs for skills/, one namespace over.
    missing_from_map = sorted(role_names - map_role_names)
    extra_in_map = sorted(map_role_names - role_names)
    if missing_from_map:
        errors.append(
            f"::error file={prefix}::{PLACEMENT_MAP_PATH} is missing an "
            f"`{AGENTS_PREFIX}` entry for: "
            f"{', '.join(AGENTS_PREFIX + n for n in missing_from_map)}"
        )
    if extra_in_map:
        errors.append(
            f"::error file={prefix}::{PLACEMENT_MAP_PATH} has an "
            f"`{AGENTS_PREFIX}` entry for non-existent {ROOT}/ role(s): "
            f"{', '.join(AGENTS_PREFIX + n for n in extra_in_map)}"
        )

    return errors


def coverage_errors(root: Path, validated: int) -> list[str]:
    """Assert the run actually saw the roster it claims to have validated.

    Mirrors `validate_skills.py::coverage_errors` exactly, one directory
    over: a clean list of errors is only evidence if it was produced
    against real roles -- a run that walked an empty or wrong tree reports
    zero errors just as loudly as one that walked every real role. **If
    this gate discovers zero roles, that is a FAILURE, not a pass** -- the
    guard this whole function exists to be, not a nice-to-have alongside
    the per-role rules above.

    Returns the `::error::` lines (empty list == the pass is evidence).
    """
    on_disk = len(list(root.glob("*.md")))
    errors: list[str] = []

    if validated == 0:
        errors.append(
            f"::error::coverage guard: 0 agent roles validated under '{root}'. This "
            "gate is cwd-relative, so a run from the wrong directory validates "
            "nothing and would otherwise report success -- green CI over zero "
            "coverage. Run it from the repo root."
        )

    if validated != on_disk:
        errors.append(
            f"::error::coverage guard: validated {validated} role file(s) but "
            f"'{root}' holds {on_disk} .md file(s). The counts must agree or the "
            "pass is not evidence about the roles on disk."
        )

    return errors


def main() -> int:
    errors = run(ROOT)

    if errors:
        for e in errors:
            print(e)
        print(f"::error::{len(errors)} agent role validation errors")
        return 1

    validated = len(_role_files(ROOT))
    guard = coverage_errors(ROOT, validated)
    if guard:
        for e in guard:
            print(e)
        return 1

    print(f"OK: {validated} agent roles validated cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
