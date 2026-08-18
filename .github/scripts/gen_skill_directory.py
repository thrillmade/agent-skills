#!/usr/bin/env python3
"""Render `skills/finding-a-catalog-skill/SKILL.md`'s body from the catalog.

The catalog's directory has to be a SKILL, because a skill is the only
artifact that travels: a subscriber installs into `.claude/skills/` and
README.md stays behind (#229). An agent that cannot see what the catalog
covers concludes the coverage is absent and writes the guidance again.

The body is DERIVED, never hand-edited. Its inputs are:

  * the `skills/` directory walk -- the same walk `validate_skills._skill_dirs`
    does, so the directory and the existing gates cannot disagree about which
    skills exist; and
  * `docs/placement-map.json`, which already carries one entry per skill,
    already reconciled 1:1 against those directory names by `validate_skills`.
    Two keys per entry feed this file: `family` (which group the skill is
    listed under) and `owns` (the one fragment naming what it owns).

Putting the editorial text in the placement map rather than in each skill's
frontmatter is deliberate, and there are three reasons:

  1. The map is ALREADY reconciled 1:1 against `skills/`. A skill added
     without an `owns` fails the gate the day it is added -- which is the
     property the README table has never had -- and it costs no new
     reconciliation machinery.
  2. Nine of the catalog's skills are `repo-mirrored` (logmind, the eight
     `udts-*` stubs): authored elsewhere and PR'd here by release automation.
     A required FRONTMATTER key would turn a foreign sync PR red over a field
     the mirror source never agreed to carry. Editorial copy about a skill in
     this catalog belongs to this catalog.
  3. Frontmatter is outside the 8192-byte body cap, so a field there is free
     -- but so is a field here, and here it is one file to review instead of
     fifty.

THE BYTE BUDGET, which is the whole reason the format looks like this.
`validate_skills.SIZE_LIMIT` caps a skill body at 8192 bytes, and this body is
the one artifact in the catalog that grows every time the catalog does. So the
ceiling is stated here, measured, rather than discovered in CI later.

What the source could NOT be, measured over the 49 skills on `dev`:

    README purpose column  sum 8515 B  -- over the whole cap before a single
                                          name or bullet is added. This is the
                                          text #229 proposed reusing.
    frontmatter description sum 27363 B -- 3.3x the cap, and a trigger surface
                                          ("Use when about to...") rather than
                                          a statement of what a skill owns.

What the format costs, MEASURED by rendering real and synthetic trees rather
than modelled (`n` counts the directory itself; synthetic skills carry the
measured mean name length and a WORST-CASE 32-byte `owns`):

    n     body    vs 7900 reserve   vs 8192 cap
    50    6262        +1638            +1930    today
    55    6592        +1308            +1600    after PR #233's five
    74    7846          +54             +346    the last n inside the reserve
    75    7912          -12             +280    first refusal
    79    8176         -276              +16    the last n inside the cap
    100   9562        -1662            -1370    over

Decomposed at n=50: rows 2876 (57.5 B/skill), family headings + routing lines
854, chrome 2532. Marginal cost is 66 B per skill, plus a new family roughly
every 11.

SO THE CEILING IS 74, and that is a choice, not an accident. The alternative
was measured on the same trees: drop the per-skill fragment, list bare names
under each family, and the body is 4625 B at n=50 and 6075 at n=100, reaching
about 155. It was rejected because the fragment is the part that answers the
question #229 is about -- an agent reading `visual-polish` and
`token-frugal-tooling` as bare names still cannot tell whether either covers
what it is about to write, and a shortlist you cannot narrow is a list. Eighty
skills of headroom is the price of the column that does the work; `size_error()`
names every rung of the ladder, each with the value measured here, for the day
it binds.

One number outside this file's control, for the record: clud-bug's shipped
workflow TEMPLATE overrides its skill cap down to 4000 (validate_skills.py:83,
clud-bug#301). A repo on an unmodified template truncates this body inside the
listing. That is an argument with clud-bug, not a budget this catalog's own
gate applies.

CLI (same three modes as `stamp_versions.py`):

    python3 .github/scripts/gen_skill_directory.py            # report, write nothing
    python3 .github/scripts/gen_skill_directory.py --write    # write the SKILL.md
    python3 .github/scripts/gen_skill_directory.py --check    # exit 1 if stale

Stdlib only. Run from the repo root; both paths are cwd-relative, exactly as
`validate_skills.py` resolves them.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path("skills")
PLACEMENT_MAP = Path("docs/placement-map.json")

# The one named constant that keeps the directory out of nothing and into
# everything: it is a skill like any other, so it appears in its own listing
# and is reconciled like any other. There is no exemption list, because
# `validate_skills.py:73-80` already ruled that a one-line escape hatch is
# worse than a visible per-item one.
DIRECTORY_SLUG = "finding-a-catalog-skill"

# `owns` is a fragment, not a sentence. It is paid once per skill, so it sets
# the ceiling: a row costs 10 bytes of markup + the name (mean 19.8) + this.
# Raising it is a decision about how many skills the directory can hold, not a
# formatting preference -- the docstring above has the arithmetic and
# `size_error()` has the ladder.
OWNS_MAX_BYTES = 32

# The generator refuses over this rather than over SIZE_LIMIT itself. The
# reserve is what stops the NEXT skill added from being the one that discovers
# the cap in CI: 8192 - 7900 = 292 bytes is room for four more rows at the
# measured 66 bytes per skill.
SIZE_LIMIT = 8192
MAX_BODY_BYTES = 7900

# --- the prose. Edit here; the file is generated. --------------------------

HEADER = """
# Finding a catalog skill

Every skill in the **thrillmade/agent-skills** catalog, grouped by what it
owns. Generated from `docs/placement-map.json` -- a copy that drifts from the
`skills/` tree fails the `validate-skills` gate, so this list cannot go quietly
stale the way a hand-kept table does.

**Read it before you write a rule.** Before authoring a convention, a
checklist, a house standard or a "how we do X" doc -- and before saying
"nothing covers this". The catalog is bigger than the set installed in any one
repo, so *not seeing* a skill is not evidence that none exists. Check here
first; that check is one read, and writing the guidance again is not.

**What a line is.** The fragment after each name says what that skill *owns*,
not what it says. It is enough to shortlist two or three and no more -- open
them. A skill you do not have yet:

```
npx skills add https://github.com/thrillmade/agent-skills --skill <name>
```

**What this is not.** Not a listing of your `.claude/skills/`: a repo holds
only the skills it subscribed to, plus any it authored locally that will never
appear below. And not a view of the wider skills.sh ecosystem -- this indexes
one catalog.
"""

NOT_HERE_INTRO = """
## Deliberately not here

A map showing only what is inside teaches you the outside does not exist,
which is the same mistake inverted. These are gaps this catalog knows it has.
The counts are re-measured every time this file is generated -- if one stopped
being zero, the generator would refuse to write this section rather than let
it go on claiming a gap that has since been filled:
"""

NOT_HERE_OUTRO = """
Not being named above is not evidence of absence either. Search `skills/`
before concluding a second time -- and control the search against a term you
know is there, the way the counts above are controlled.
"""

# Each probe: the phrase, and what it stands for. `render()` counts the files
# under `skills/` matching it and REFUSES to render if a count is no longer
# zero -- the claim is measured at generation time, not typed once and left to
# rot, which is the exact defect #229 filed against the README table.
NOT_HERE_PROBES = [
    (
        "red before green",
        "**TDD mechanics** -- red before green, one failing test at a time. In "
        "the `superpowers` plugin, not here",
    ),
    ("test-driven", "**The same discipline under its other name**"),
    (
        "forcing function",
        "**Norman's design primitives** -- forcing functions, mapping, the two gulfs",
    ),
]

# The control. A probe set that matches nothing proves nothing unless
# something proves the matcher works at all; six agents on this project have
# been burned by an uncontrolled zero. This term MUST match, and the generator
# refuses if it does not.
NOT_HERE_CONTROL = "APCA"

SOURCES = """
## Sources

- Published by [thrillmot](https://thrillmot.com)
- The catalog: <https://github.com/thrillmade/agent-skills>
- Placement, distribution and subscribers per skill: `docs/placement-map.json`
- The census that promotes, revises and retires these:
  [`curating-a-skill-catalog`](../curating-a-skill-catalog/SKILL.md)
"""


def _matching_files(root: Path, phrase: str) -> list[str]:
    """Skill names whose SKILL.md contains `phrase`, case-insensitively.

    The directory itself is excluded, and it has to be: it NAMES the phrases
    it is claiming nothing covers, so scanning it makes every probe match
    itself on the second run and the section can never be regenerated. The
    directory is a map of coverage, not coverage -- a name printed here is not
    a skill that owns the topic. (The control below is what stops this
    exclusion from silently becoming "match nothing at all".)
    """
    needle = phrase.lower()
    hits = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if d.name == DIRECTORY_SLUG:
            continue
        md = d / "SKILL.md"
        if md.exists() and needle in md.read_text(encoding="utf-8").lower():
            hits.append(d.name)
    return hits


def not_here(root: Path) -> str:
    """The "deliberately not here" section, with its zeros measured now.

    Refuses on either failure direction. A probe that started matching means
    the catalog gained the coverage and the section is lying; a control that
    stopped matching means the matcher is broken and every zero below it is
    worthless.
    """
    control = _matching_files(root, NOT_HERE_CONTROL)
    if not control:
        raise SystemExit(
            f"Refusing to publish a 'not here' section whose control probe "
            f"({NOT_HERE_CONTROL!r}) matched 0 skills. An uncontrolled zero is not a "
            "measurement -- every 'this catalog does not cover X' line below it "
            "would be equally explained by a matcher that matches nothing."
        )

    filled = {p: _matching_files(root, p) for p, _ in NOT_HERE_PROBES}
    filled = {p: hits for p, hits in filled.items() if hits}
    if filled:
        raise SystemExit(
            "Refusing to publish a 'not here' section that is out of date. These "
            "probes now match skills in this catalog: "
            + "; ".join(f"{p!r} -> {', '.join(h)}" for p, h in filled.items())
            + ". The gap was filled. Update NOT_HERE_PROBES in "
            ".github/scripts/gen_skill_directory.py and regenerate -- a directory "
            "that tells an agent to go elsewhere for something it already holds "
            "causes the duplication it exists to prevent."
        )

    lines = [NOT_HERE_INTRO.strip(), ""]
    for phrase, gloss in NOT_HERE_PROBES:
        lines.append(f"- {gloss} -- `{phrase}` matches **0** skills.")
    lines.append("")
    lines.append(
        f"(Control: `{NOT_HERE_CONTROL}` matches {len(control)}, so the probe finds "
        "what is there.)"
    )
    lines.append("")
    lines.append(NOT_HERE_OUTRO.strip())
    return "\n".join(lines)


def load_map(root: Path = ROOT, map_path: Path = PLACEMENT_MAP) -> tuple[list, dict]:
    """`(families, skills)` from the placement map, or raise SystemExit.

    Refuses rather than degrades. `gen_skill_versions.py` sets the precedent
    and the reason is the same: a directory rendered from a map that failed to
    load is a SHORT directory, and a short directory reads exactly like a
    complete one to the agent holding it.
    """
    if not map_path.exists():
        raise SystemExit(
            f"Refusing to build a directory without {map_path}. The `family` and "
            "`owns` text lives there; without it every line would be a bare name, "
            "and a directory that silently says less is indistinguishable from one "
            "that says everything."
        )
    try:
        pm = json.loads(map_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise SystemExit(f"Refusing to build a directory: {map_path} is not valid JSON: {e}")

    families = pm.get("families")
    skills = pm.get("skills")
    if not isinstance(families, list) or not families:
        raise SystemExit(
            f"Refusing to build a directory: {map_path} has no non-empty `families` list."
        )
    if not isinstance(skills, dict) or not skills:
        raise SystemExit(
            f"Refusing to build a directory: {map_path} has no non-empty `skills` object."
        )
    return families, skills


def render(root: Path = ROOT, map_path: Path = PLACEMENT_MAP) -> str:
    """The rendered SKILL.md body -- everything after the frontmatter's `---`.

    A pure function of the tree plus the map, with `root` a parameter so tests
    drive it over a tmp_path. Unlike `gen_skill_versions.py` this reads no git
    history at all, which is why the gate can compare the WHOLE body rather
    than one recomputable field.
    """
    dirs = sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    if not dirs:
        raise SystemExit(
            f"Refusing to build a directory from zero skills under '{root}'. This "
            "script is cwd-relative; a run from the wrong directory renders an empty "
            "list and nothing about it looks wrong. Run it from the repo root."
        )

    families, skills = load_map(root, map_path)

    parts = ["", HEADER.strip(), ""]
    for fam in families:
        fid = fam.get("id")
        listed = sorted(s for s in dirs if skills.get(s, {}).get("family") == fid)
        if not listed:
            # A family with no skills is a gate failure, not a rendering
            # decision -- validate_skills reports it by name. Skipping it here
            # keeps the two from disagreeing about the same defect.
            continue
        parts.append(f"## {fam.get('title')}")
        parts.append(str(fam.get("routes")))
        parts.append("")
        for slug in listed:
            parts.append(f"- `{slug}` — {skills[slug].get('owns')}")
        parts.append("")

    # Every skill on disk must be reachable from some family, or the directory
    # is a map with a hole in it. The gate names the offenders; refusing here
    # stops a holed map being WRITTEN in the first place.
    placed = {
        s
        for fam in families
        for s in dirs
        if skills.get(s, {}).get("family") == fam.get("id")
    }
    orphans = sorted(set(dirs) - placed)
    if orphans:
        raise SystemExit(
            "Refusing to build a directory that omits skills on disk: "
            f"{', '.join(orphans)}. Give each one a `family` in "
            f"{map_path} that matches a declared family id."
        )

    parts.append(not_here(root))
    parts.append("")
    parts.append(SOURCES.strip())
    return "\n".join(parts) + "\n"


def size_error(body: str) -> str | None:
    """The refusal message when the rendered body no longer fits, or None.

    Carries the arithmetic and the ladder, in the house style of
    `validate_skills.SIZE_LIMIT`'s message: a maintainer told only a number
    files a bypass; one told what it costs and which lever is next fixes it.
    """
    n = len(body.encode("utf-8"))
    if n <= MAX_BODY_BYTES:
        return None
    return (
        f"the rendered directory is {n} bytes, past the {MAX_BODY_BYTES}-byte "
        f"reserve this generator keeps under the {SIZE_LIMIT}-byte skill cap "
        f"(by {n - MAX_BODY_BYTES}). Past the cap a consuming reviewer truncates "
        "the body, so the tail stops reaching the agent -- and the tail of a "
        "DIRECTORY is skills that then look like they do not exist, which is the "
        "failure this skill exists to prevent, reintroduced by its own size. "
        "This was expected at roughly 74 skills; the ladder, each rung with the "
        "value MEASURED when the format was chosen: "
        f"(1) cut `owns` from {OWNS_MAX_BYTES} bytes to 24 -- worth 8 bytes per "
        "skill, measured to move the ceiling from 74 to 81; "
        "(2) halve the family `routes` sentences in docs/placement-map.json -- "
        "one sentence covers five to twelve skills, and with (1) it measured a "
        "ceiling of 87; "
        "(3) drop the per-skill fragment and list bare names under each family "
        "-- worth about 32 bytes per skill: 6075 bytes at 100 skills, reaching "
        "roughly 155. A real lever that costs the column doing the work, so "
        "spend it last; "
        "(4) retire skills. At this size the cap is information about the "
        "CATALOG rather than about the directory, and `curating-a-skill-catalog` "
        "already owns demotion. "
        "Splitting the directory in two is NOT a lever: a map you must know to "
        "look in two places for is not a map, and a subscriber that installs one "
        "half gets one that lies by omission -- exactly #229's failure."
    )


def target(root: Path = ROOT) -> Path:
    return root / DIRECTORY_SLUG / "SKILL.md"


def _split(text: str) -> tuple[str, str]:
    """`(frontmatter-through-closing-fence, body)`. The frontmatter is
    hand-authored -- `description` is a trigger surface, not derived data --
    so only the body is generated and only the body is compared.
    """
    if not text.startswith("---\n"):
        raise SystemExit(f"{target()} does not start with YAML frontmatter.")
    end = text.find("\n---", 4)
    if end == -1:
        raise SystemExit(f"{target()} has an unterminated frontmatter block.")
    cut = end + len("\n---")
    return text[:cut], text[cut:]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--write", action="store_true", help="write the SKILL.md body")
    mode.add_argument("--check", action="store_true", help="exit 1 if the committed body is stale")
    args = ap.parse_args(argv)

    body = render()
    err = size_error(body)
    if err:
        print(f"::error file={target()}::{err}")
        return 1

    path = target()
    if not path.exists():
        if not args.write:
            print(f"{path} does not exist yet. Run with --write.")
            return 1
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\n---\n" + body, encoding="utf-8")
        print(f"wrote {path} ({len(body.encode('utf-8'))} body bytes)")
        return 0

    front, current = _split(path.read_text(encoding="utf-8"))
    n = len(body.encode("utf-8"))
    if current == body:
        print(f"OK: {path} is current ({n} body bytes, {MAX_BODY_BYTES - n} under the reserve).")
        return 0

    if args.check:
        print(
            f"::error file={path}::the committed directory body differs from what "
            "docs/placement-map.json and skills/ render. It is generated, not "
            "hand-kept: run `python3 .github/scripts/gen_skill_directory.py --write`."
        )
        return 1

    if args.write:
        path.write_text(front + body, encoding="utf-8")
        print(f"wrote {path} ({n} body bytes)")
        return 0

    print(f"STALE: {path} differs from the render ({n} body bytes). Run with --write.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
