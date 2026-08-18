#!/usr/bin/env python3
"""Validate every SKILL.md under skills/<name>/ (the `validate-skills` gate).

Called by `.github/workflows/validate-skills.yml` on PR + push to main.
Catches malformed frontmatter (missing name, missing description, name
mismatch with directory) before it ships to skills.sh, where downstream
consumers (clud-bug, agent runtimes via skills CLI) would silently get
broken skills.

Also gates docs/placement-map.json (when present): valid JSON/shape, and its
`skills` keys reconciled 1:1 against skills/ directory names. This is what
makes the placement-map guide's claim ("the map is kept in sync") actually
true instead of aspirational.

Three listings of the catalog have to agree with the tree, and each is
reconciled here (#229): the placement map 1:1 by key; the generated directory
skill by byte-identical re-render, plus the cross-check that a SUPERSEDED
skill is filed under `deprecated`; and README.md by membership only, since its
purpose column is prose no generator should flatten.

This file was a `python <<'PY'` heredoc inside the workflow until it was
extracted verbatim so it could be imported and characterized by
`tests/test_validate_skills.py`. Every rule, message string and exit code
below is the heredoc's, unchanged -- the gate's behaviour is now pinned by
tests rather than by re-reading YAML.

Stdlib + PyYAML only (the workflow pip-installs pyyaml; nothing else).

Inputs:
  cwd  ROOT and the placement map are BOTH cwd-relative, exactly as the
       heredoc had them. Run from the repo root. `main()`'s coverage guard
       is what stops a run from the wrong directory passing vacuously.

Outputs (stdout):
  One `::error file=<path>::<msg>` GitHub annotation per validation error,
  then a `::error::<N> skill validation errors` summary -- or a single
  `OK: <N> skills validated cleanly.` line.

Exit codes:
  0  Every SKILL.md (and the placement map, if present) validated cleanly
     AND the coverage guard agrees the run actually saw the tree.
  1  Any validation error, either infra-fatal condition (no skills/ dir, no
     skill subdirectories), or a coverage-guard failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import yaml

# The directory generator. Imported rather than shelled out to so the gate
# renders in-process and compares the WHOLE body: the directory is a pure
# function of this checkout and reads no git history, so nothing weaker than
# byte identity is needed and nothing weaker is used.
#
# `.github/scripts` is sys.path[0] when this file is run as a script, and
# tests/conftest.py puts it there for the import path.
#
# The try/except is not defensive. Without it, deleting the generator takes
# the whole gate down with an uncaught ModuleNotFoundError traceback and no
# `::error file=` annotation -- so the one failure that means "the directory
# can no longer be verified at all" is the one CI renders least legibly.
try:
    import gen_skill_directory  # noqa: E402
except ImportError as _import_error:
    print(
        "::error file=.github/scripts/gen_skill_directory.py::the catalog directory "
        f"generator could not be imported ({_import_error}), so the committed "
        "directory cannot be re-rendered and compared. Every other rule below would "
        "still pass, and an unverifiable directory reads exactly like a verified one."
    )
    sys.exit(1)

ROOT = Path("skills")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)

# protocol SPEC.md §1.10.1 "Frontmatter (NORMATIVE)" -- enums and
# shapes enforced below. Every key here is OPTIONAL in the
# frontmatter; unknown keys (and the RESERVED, definition-deferred
# `layer` / `status` / `superseded_by` keys) are always tolerated
# and never validated -- only the fields below are checked, and
# only when present.
NAME_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{0,62}$")
# SPEC §1.10.1: `source: manual | logmind-derived | skills-sh | clud-bug-baseline`
SOURCE_VALUES = {"manual", "logmind-derived", "skills-sh", "clud-bug-baseline"}
# SPEC: `kind: rule | writing | design`
KIND_VALUES = {"rule", "writing", "design"}

# Skill body size. No exceptions, and the number lives HERE on
# purpose -- in code, changeable only by a reviewed edit to this file.
#
# It was briefly a JSON file carrying a `limitBytes` key plus a
# grandfather list. That is the worse design: a grandfather row
# exempts one skill visibly in review, but `limitBytes` is one line
# and exempts all 46 at once, silently. Closing the small door while
# leaving the large one open relocates the escape rather than
# shutting it.
#
# There is no exception path because there is nothing to except.
# Past this size a consuming reviewer truncates the body when
# building its prompt, so the tail never reaches the model while the
# author sees a complete file and a green build. An oversized skill
# is already broken for its reader; blessing it does not make it
# work, it only makes the breakage approved.
#
# 8192 is clud-bug's own DEFAULT_MAX_SKILL_BYTES
# (src/core/prompt-builder.ts), whose comment ties it to SPEC 1.10.
# Its shipped workflow templates override this DOWN to 4000, so a
# repo on an unmodified template truncates earlier -- clud-bug#301.
SIZE_LIMIT = 8192

# --- docs/placement-map.json gate ------------------------------------------
#
# The steward's placement map (docs/integrating-with-agent-skills.md
# "The placement map") claims it is the per-skill ground truth kept
# in sync with skills/. Make that claim real: validate shape + enums
# when the file is present, and reconcile its `skills` keys 1:1
# against the skills/ directory names (report missing/extra by
# name). Absence is tolerated (it may not exist yet / may be
# authored by a parallel agent) -- only presence-with-defects fails.

AUTHORING_HOME_RE = re.compile(r"^(catalog|undecided|repo-mirrored:[a-z0-9-]+)$")
DISTRIBUTION_VALUES = {"default-on", "opt-in", "catalog-only"}

# How the catalog announces a retirement. All three retired skills open their
# `description` with it, and no live skill does -- it is the first thing an
# agent reads, so it is the thing the directory has to agree with. Anchored by
# `.match()` (which starts at position 0) rather than by a `^` in the pattern:
# with both, neither can be tested, because removing either one leaves the
# other still anchoring. One owner for the anchoring, and a mutation proves it.
SUPERSEDED_RE = re.compile(r"SUPERSEDED\b")

# A README link to a skill, which is how the README names one. The table is
# still hand-written prose; this reconciles its MEMBERSHIP only -- see
# `readme_errors`.
README_SKILL_LINK_RE = re.compile(r"\(skills/([a-z0-9-]+)/SKILL\.md\)")


def _is_superseded(meta: dict) -> bool:
    """Whether this skill announces itself as retired.

    Three signals, because the catalog has used them at different times and a
    detector that only knows one is a detector that goes quiet the first time
    somebody uses another: a `description` opening `SUPERSEDED`, the RESERVED
    `superseded_by` key, and `status: superseded`.
    """
    description = meta.get("description")
    if isinstance(description, str) and SUPERSEDED_RE.match(description):
        return True
    if isinstance(meta.get("superseded_by"), str) and meta["superseded_by"].strip():
        return True
    status = meta.get("status")
    return isinstance(status, str) and status.strip().lower() == "superseded"


def _valid_extension_entry(e: object) -> bool:
    """An `applies_to.extensions` entry is a suffix-matched string —
    clud-bug does suffix matching, not strict dotfile-extension
    matching, so both '.tsx' and '_test.py' (skills/test-discipline
    ships the latter) are legitimate. Require: non-empty string, no
    whitespace, at least one '.', and not the bare string '.'.
    """
    return (
        isinstance(e, str)
        and e != ""
        and not re.search(r"\s", e)
        and "." in e
        and e != "."
    )


def _skill_dirs(root: Path) -> list[Path]:
    """Every immediate subdirectory of `root`, sorted. The set of things the
    gate considers a skill -- one SKILL.md is expected in each.
    """
    return sorted(p for p in root.iterdir() if p.is_dir())


def run(root: Path) -> list[str]:
    """Validate every skill under `root`, returning the `::error ...::` lines.

    An empty list means clean. The caller prints the lines and the summary --
    see `main()`, which also applies `coverage_errors()` to the clean path so
    a run that validated nothing cannot pass.

    Two INFRA-FATAL conditions print and `sys.exit(1)` from here rather than
    returning: a missing skills/ dir and a skills/ dir with no subdirectories.
    They are not validation errors, they carry no `::error::<N> skill
    validation errors` summary line, and that is the workflow's shipped
    behaviour -- preserved deliberately.
    """
    errors: list[str] = []
    # Slugs whose own frontmatter says they are retired. Collected here rather
    # than re-read in the placement-map block below, so the two can never
    # disagree about which skills those are.
    superseded: set[str] = set()

    if not root.exists() or not root.is_dir():
        print("::error::skills/ directory not found at repo root")
        sys.exit(1)

    skill_dirs = _skill_dirs(root)
    if not skill_dirs:
        print("::error::no skill subdirectories under skills/")
        sys.exit(1)

    for skill_dir in skill_dirs:
        dir_name = skill_dir.name
        skill_md = skill_dir / "SKILL.md"
        prefix = f"{skill_md}"

        if not skill_md.exists():
            errors.append(f"::error file={prefix}::missing SKILL.md")
            continue

        content = skill_md.read_text(encoding="utf-8")
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
            errors.append(
                f"::error file={prefix}::frontmatter is not valid YAML: {e}"
            )
            continue

        if not isinstance(meta, dict):
            errors.append(
                f"::error file={prefix}::frontmatter must be a YAML mapping"
            )
            continue

        if _is_superseded(meta):
            superseded.add(dir_name)

        name = meta.get("name")
        if not name or not isinstance(name, str) or not name.strip():
            errors.append(
                f"::error file={prefix}::frontmatter is missing a non-empty `name:` field"
            )
        else:
            name = name.strip()
            if name != dir_name:
                errors.append(
                    f"::error file={prefix}::frontmatter name='{name}' "
                    f"does not match directory name '{dir_name}'"
                )
            if not NAME_SLUG_RE.match(name):
                errors.append(
                    f"::error file={prefix}::frontmatter name='{name}' does not match "
                    r"the SPEC §1.10.1 slug regex ^[a-z][a-z0-9-]{0,62}$"
                )

        description = meta.get("description")
        if not description or not isinstance(description, str) or not description.strip():
            errors.append(
                f"::error file={prefix}::frontmatter is missing a non-empty `description:` field"
            )

        # Require an H1 (Markdown title) somewhere in the body after the frontmatter
        body = content[m.end():]
        if not re.search(r"^# .+", body, flags=re.MULTILINE):
            errors.append(
                f"::error file={prefix}::body has no top-level `# Title` heading"
            )

        # --- Body size (see SIZE_LIMIT above) ---
        # The error carries the REASON deliberately. A maintainer who
        # hits a bare limit files a bypass PR; one who is told the tail
        # silently never reaches the reader fixes the skill instead.
        body_bytes = len(body.encode("utf-8"))
        if body_bytes > SIZE_LIMIT:
            errors.append(
                f"::error file={prefix}::body is {body_bytes} bytes, over the "
                f"{SIZE_LIMIT}-byte limit by {body_bytes - SIZE_LIMIT}. Past this, a "
                f"consuming reviewer truncates the body when building its prompt -- your "
                f"reader silently does not receive the rest, and nothing reports it. "
                f"Fixes, in order: cut narration and duplication; replace anything a "
                f"neighbouring skill already owns with a relative markdown link to it; "
                f"split ONLY if this is genuinely two topics, never to hit the number. "
                f"Do NOT move prose into references/ -- that consumer reads SKILL.md and "
                f"nothing else, so the move deletes it. There is no exception list."
            )

        # --- SPEC §1.10.1 OPTIONAL-field validation ---

        kind = meta.get("kind")
        if kind is not None and kind not in KIND_VALUES:
            errors.append(
                f"::error file={prefix}::`kind: {kind!r}` is not one of "
                f"{sorted(KIND_VALUES)} (SPEC §1.10.1)"
            )

        # `review_mode` was removed from the skill schema: how a repo
        # groups skills into passes is `review.passes` in its own review
        # config (SPEC §2.2), not a field on a skill it may not edit.
        # Unrecognised keys round-trip untouched (SPEC §2.1), so a stale
        # one is ignored rather than rejected.

        source = meta.get("source")
        if source is not None and source not in SOURCE_VALUES:
            errors.append(
                f"::error file={prefix}::`source: {source!r}` is not one of "
                f"{sorted(SOURCE_VALUES)} (SPEC §1.10.1)"
            )

        applies_to = meta.get("applies_to")
        if applies_to is not None:
            if not isinstance(applies_to, dict):
                errors.append(
                    f"::error file={prefix}::`applies_to` must be a YAML mapping"
                )
            else:
                paths = applies_to.get("paths")
                if paths is not None and (
                    not isinstance(paths, list)
                    or not all(isinstance(p, str) and p.strip() for p in paths)
                ):
                    errors.append(
                        f"::error file={prefix}::`applies_to.paths` must be a list "
                        "of non-empty glob strings (SPEC §1.10.1)"
                    )

                extensions = applies_to.get("extensions")
                if extensions is not None and (
                    not isinstance(extensions, list)
                    or not all(_valid_extension_entry(e) for e in extensions)
                ):
                    errors.append(
                        f"::error file={prefix}::`applies_to.extensions` must be a "
                        "list of extension/suffix strings (e.g. '.tsx', "
                        "'_test.py') (SPEC §1.10.1)"
                    )

                author = applies_to.get("author")
                if author is not None:
                    if not isinstance(author, str) or not author.strip():
                        errors.append(
                            f"::error file={prefix}::`applies_to.author` must be a "
                            "single non-empty GitHub handle string, not a list "
                            "(SPEC §1.10.1)"
                        )
                    elif author.strip().startswith("@"):
                        errors.append(
                            f"::error file={prefix}::`applies_to.author` must not "
                            "include a leading '@' (SPEC §1.10.1)"
                        )

    # --- docs/placement-map.json gate (see the constants above) --------

    placement_map_path = root.parent / "docs" / "placement-map.json"

    if placement_map_path.exists():
        pm_prefix = str(placement_map_path)

        try:
            pm_text = placement_map_path.read_text(encoding="utf-8")
        except OSError as e:
            errors.append(
                f"::error file={pm_prefix}::could not read {placement_map_path}: {e}"
            )
            pm_text = None

        pm = None
        if pm_text is not None:
            try:
                pm = json.loads(pm_text)
            except json.JSONDecodeError as e:
                errors.append(
                    f"::error file={pm_prefix}::{placement_map_path} is not valid JSON: {e}"
                )

        if pm is not None:
            if not isinstance(pm, dict):
                errors.append(
                    f"::error file={pm_prefix}::top level of {placement_map_path} "
                    "must be a JSON object with `version`, `updated`, `skills`"
                )
            else:
                version = pm.get("version")
                if not isinstance(version, int) or isinstance(version, bool):
                    errors.append(
                        f"::error file={pm_prefix}::`version` must be an int"
                    )

                updated = pm.get("updated")
                if not isinstance(updated, str) or not updated.strip():
                    errors.append(
                        f"::error file={pm_prefix}::`updated` must be a non-empty string"
                    )

                # --- `families`: the directory's grouping, ordered ---
                #
                # An ordered list rather than an object because the order IS
                # the document order of the generated directory, and a JSON
                # object's key order is not a thing a reviewer should have to
                # trust.
                families = pm.get("families")
                family_ids: set[str] = set()
                if not isinstance(families, list) or not families:
                    errors.append(
                        f"::error file={pm_prefix}::`families` must be a non-empty list "
                        "of {id, title, routes} objects. It is the directory's grouping; "
                        "without it every skill's `family` is unresolvable and the "
                        "generated directory is a flat list of names."
                    )
                else:
                    for i, fam in enumerate(families):
                        if not isinstance(fam, dict):
                            errors.append(
                                f"::error file={pm_prefix}::families[{i}] must be an "
                                "object with `id`, `title` and `routes`"
                            )
                            continue
                        fid = fam.get("id")
                        if not isinstance(fid, str) or not NAME_SLUG_RE.match(fid):
                            errors.append(
                                f"::error file={pm_prefix}::families[{i}].id={fid!r} must "
                                r"match ^[a-z][a-z0-9-]{0,62}$"
                            )
                        elif fid in family_ids:
                            errors.append(
                                f"::error file={pm_prefix}::families[{i}].id={fid!r} is "
                                "declared twice; a skill naming it would be listed twice"
                            )
                        else:
                            family_ids.add(fid)
                        for key in ("title", "routes"):
                            val = fam.get(key)
                            if not isinstance(val, str) or not val.strip():
                                errors.append(
                                    f"::error file={pm_prefix}::families[{i}].{key} must "
                                    "be a non-empty string"
                                )

                skills_map = pm.get("skills")
                if not isinstance(skills_map, dict):
                    errors.append(
                        f"::error file={pm_prefix}::`skills` must be an object "
                        "mapping skill name -> metadata"
                    )
                else:
                    malformed_entry = False
                    for slug, meta in skills_map.items():
                        if not isinstance(meta, dict):
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug} must be "
                                "an object (unknown per-skill keys are tolerated; "
                                "the value itself must still be a mapping)"
                            )
                            malformed_entry = True
                            continue

                        authoring_home = meta.get("authoring_home")
                        if not isinstance(authoring_home, str) or not AUTHORING_HOME_RE.match(
                            authoring_home
                        ):
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.authoring_home="
                                f"{authoring_home!r} must match "
                                r"^(catalog|undecided|repo-mirrored:[a-z0-9-]+)$"
                            )

                        distribution = meta.get("distribution")
                        if distribution not in DISTRIBUTION_VALUES:
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.distribution="
                                f"{distribution!r} is not one of "
                                f"{sorted(DISTRIBUTION_VALUES)}"
                            )

                        subscribers = meta.get("subscribers")
                        if not isinstance(subscribers, list) or not all(
                            isinstance(s, str) for s in subscribers
                        ):
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.subscribers "
                                "must be a list of strings"
                            )

                        # --- the directory's two editorial keys ---
                        #
                        # These are REQUIRED, and that is the whole point: the
                        # map is already reconciled 1:1 against skills/ below,
                        # so requiring them here means a skill cannot be added
                        # without saying which family it belongs to and what it
                        # owns. The README table has never had that property --
                        # it is complete by diligence, and the next skill added
                        # is the one that breaks it silently (#229).
                        family = meta.get("family")
                        if not isinstance(family, str) or not family.strip():
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.family must be "
                                "a non-empty string naming one of the `families` ids. It "
                                "is what puts this skill in the generated directory "
                                f"(skills/{gen_skill_directory.DIRECTORY_SLUG}/SKILL.md); "
                                "without it the skill exists and the catalog's own map "
                                "does not show it."
                            )
                        elif family not in family_ids:
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.family="
                                f"{family!r} is not a declared family. Declared: "
                                f"{', '.join(sorted(family_ids)) or '(none)'}"
                            )

                        # The one meaning-level check the byte comparison
                        # cannot make. `owns` and `family` are editorial text;
                        # the directory and the map agree with each other by
                        # construction, so a skill filed as live after it was
                        # retired is invisible to every gate above -- and it
                        # shipped that way: `skillforge` sat under "The
                        # catalog itself" reading "scaffolding a new skill"
                        # for the whole migration window, which routes an
                        # agent INTO the retired guidance. That is #229's
                        # failure inverted, inside the artifact built to
                        # prevent it, so the class is closed rather than the
                        # instance.
                        if (
                            slug in superseded
                            and isinstance(family, str)
                            and family != gen_skill_directory.DEPRECATED_FAMILY
                        ):
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.family="
                                f"{family!r}, but skills/{slug}/SKILL.md announces "
                                "itself as SUPERSEDED. A retired skill listed among "
                                "live ones is a directory routing agents to guidance "
                                "its own author told them to stop following. File it "
                                f"under '{gen_skill_directory.DEPRECATED_FAMILY}' and "
                                "point `owns` at the successors."
                            )

                        owns = meta.get("owns")
                        if not isinstance(owns, str) or not owns.strip():
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.owns must be a "
                                "non-empty string -- the fragment naming what this skill "
                                "OWNS, not what it is about, as it appears in the "
                                "directory."
                            )
                        elif len(owns.encode("utf-8")) > gen_skill_directory.OWNS_MAX_BYTES:
                            errors.append(
                                f"::error file={pm_prefix}::skills.{slug}.owns is "
                                f"{len(owns.encode('utf-8'))} bytes, over the "
                                f"{gen_skill_directory.OWNS_MAX_BYTES}-byte cap by "
                                f"{len(owns.encode('utf-8')) - gen_skill_directory.OWNS_MAX_BYTES}"
                                ". The cap is what keeps the directory itself under the "
                                "skill body limit as the catalog grows -- every byte here "
                                "is paid once per skill. Cut it to a fragment; the "
                                "family's routing line carries the context."
                            )

                    # Every declared family must have at least one skill. A
                    # family with none renders as nothing, so the map would
                    # claim a grouping the directory does not show -- the same
                    # divergence the 1:1 reconcile below exists to stop, in the
                    # one direction it does not cover.
                    #
                    # Suppressed when an entry was not even a mapping: that
                    # skill's `family` is unknowable, so "no skill lists it"
                    # would be a second annotation derived from the first
                    # defect rather than a finding of its own.
                    # `isinstance(..., str)` is load-bearing, not defensive:
                    # a `family: []` in the JSON is unhashable, and building
                    # this set without the guard raised TypeError out of the
                    # whole gate -- a malformed map taking the validator down
                    # instead of being reported by it.
                    used = {
                        m.get("family")
                        for m in skills_map.values()
                        if isinstance(m, dict) and isinstance(m.get("family"), str)
                    }
                    dead = [] if malformed_entry else sorted(family_ids - used)
                    if dead:
                        errors.append(
                            f"::error file={pm_prefix}::`families` declares "
                            f"{', '.join(dead)} but no skill lists "
                            f"{'them' if len(dead) > 1 else 'it'}. Delete the family or "
                            "give a skill that `family`."
                        )

                    # Map keys must EXACTLY equal the skills/ directory names.
                    map_names = set(skills_map.keys())
                    dir_names = {d.name for d in skill_dirs}
                    missing_from_map = sorted(dir_names - map_names)
                    extra_in_map = sorted(map_names - dir_names)
                    if missing_from_map:
                        errors.append(
                            f"::error file={pm_prefix}::{placement_map_path} is missing "
                            f"an entry for: {', '.join(missing_from_map)}"
                        )
                    if extra_in_map:
                        errors.append(
                            f"::error file={pm_prefix}::{placement_map_path} has an entry "
                            f"for non-existent skills/ dir(s): {', '.join(extra_in_map)}"
                        )

    errors.extend(directory_errors(root, placement_map_path))
    errors.extend(readme_errors(root, skill_dirs))
    return errors


def readme_errors(root: Path, skill_dirs: list[Path]) -> list[str]:
    """Reconcile the README's skill links 1:1 against `skills/`.

    #229's first problem, and the smaller half of it: the README table names
    every skill and nothing keeps it that way, so it is complete by diligence
    and the next skill added is the one that breaks it silently, in the file
    most readers meet first.

    MEMBERSHIP only. The purpose column is hand-written prose with room for
    sentences the byte-capped directory cannot afford, and generating it from
    `owns` would make the README worse to make it derived. So this gate asks
    the one question a machine can answer without flattening it: is every
    skill named, and is every skill it names real.

    Absence of the README is tolerated, exactly as the placement map's is --
    a tree that does not publish one has nothing to reconcile.
    """
    readme = root.parent / "README.md"
    if not readme.exists():
        return []

    prefix = str(readme)
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError as e:
        return [f"::error file={prefix}::could not read {readme}: {e}"]

    linked = set(README_SKILL_LINK_RE.findall(text))
    on_disk = {d.name for d in skill_dirs}

    errors: list[str] = []
    missing = sorted(on_disk - linked)
    if missing:
        errors.append(
            f"::error file={prefix}::the README does not link "
            f"skills/<name>/SKILL.md for: {', '.join(missing)}. It is the first "
            "listing most readers meet, and a skill missing from it reads as a "
            "skill that does not exist -- which is what somebody then writes "
            "again. Add a row to the table."
        )
    stale = sorted(linked - on_disk)
    if stale:
        errors.append(
            f"::error file={prefix}::the README links skills/<name>/SKILL.md for "
            f"dir(s) that do not exist: {', '.join(stale)}. A dead row sends a "
            "reader to a 404 and counts toward a completeness nobody has."
        )
    return errors


def directory_errors(root: Path, placement_map_path: Path) -> list[str]:
    """The generated catalog directory must equal what the generator renders.

    This is the half that makes drift unrepresentable rather than merely
    reconciled. The 1:1 reconcile above catches a skill that never got a map
    entry; this catches the entry that exists and the DIRECTORY that was not
    regenerated -- which is the same class of defect one level down, and the
    one a hand-kept skill body would have reintroduced.

    Runs only when the directory skill is present. Its absence is not an error
    HERE: this function's rules have to hold for any tree the gate is pointed
    at, including the tmp trees the suite drives it over, and "a directory
    exists" is a fact about THIS repo rather than about trees in general.
    Deleting the skill alone is already red (the map keeps an entry for a dir
    that no longer exists); deleting the entry as well is caught by
    `tests/test_gen_skill_directory.py::test_this_catalog_publishes_a_directory`,
    which owns that fact and reddens the PR that removes it. One owner, and it
    is named here so the next reader does not conclude nothing owns it.

    Presence WITHOUT a usable source is always an error -- an unverifiable
    directory reads exactly like a verified one.
    """
    path = root / gen_skill_directory.DIRECTORY_SLUG / "SKILL.md"
    if not path.exists():
        return []

    prefix = str(path)
    try:
        rendered = gen_skill_directory.render(root, placement_map_path)
    except SystemExit as e:
        return [
            f"::error file={prefix}::the directory cannot be rendered, so it cannot be "
            f"verified -- and an unverifiable directory reads exactly like a current "
            f"one to the agent holding it: {e}"
        ]

    size = gen_skill_directory.size_error(rendered)
    if size:
        return [f"::error file={prefix}::{size}"]

    content = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(content)
    if not m:
        # The per-skill loop already filed "missing YAML frontmatter"; adding a
        # second annotation for the same defect would only make the count lie.
        return []

    if content[m.end():] != rendered:
        return [
            f"::error file={prefix}::this body is GENERATED and no longer matches what "
            "docs/placement-map.json plus the skills/ tree render. Either a skill was "
            "added, removed or re-described without regenerating, or the body was "
            "hand-edited -- and a directory that has quietly stopped listing a skill is "
            "read as evidence that skill does not exist. Run "
            "`python3 .github/scripts/gen_skill_directory.py --write` and commit the "
            "result; edit the prose in the generator, never here."
        ]
    return []


def coverage_errors(root: Path, validated: int) -> list[str]:
    """Assert the run actually saw the tree it claims to have validated.

    `ROOT` is cwd-relative. A clean list of errors is only evidence if it was
    produced against real skills -- a run that walked an empty or wrong tree
    reports zero errors just as loudly as one that walked 48 correct skills.
    So the clean path is gated on: `validated` is non-zero, AND it equals the
    number of SKILL.md files actually on disk under `root`.

    Returns the `::error::` lines (empty list == the pass is evidence).
    """
    on_disk = len(list(root.glob("*/SKILL.md")))
    errors: list[str] = []

    if validated == 0:
        errors.append(
            f"::error::coverage guard: 0 skills validated under '{root}'. This gate is "
            "cwd-relative, so a run from the wrong directory validates nothing and "
            "would otherwise report success -- green CI over zero coverage. Run it "
            "from the repo root."
        )

    if validated != on_disk:
        errors.append(
            f"::error::coverage guard: validated {validated} skill dir(s) but '{root}' "
            f"holds {on_disk} SKILL.md file(s). The counts must agree or the pass is "
            "not evidence about the skills on disk."
        )

    return errors


def main() -> int:
    errors = run(ROOT)

    if errors:
        for e in errors:
            print(e)
        print(f"::error::{len(errors)} skill validation errors")
        return 1

    validated = len(_skill_dirs(ROOT))
    guard = coverage_errors(ROOT, validated)
    if guard:
        for e in guard:
            print(e)
        return 1

    print(f"OK: {validated} skills validated cleanly.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
