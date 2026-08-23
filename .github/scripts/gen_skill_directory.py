#!/usr/bin/env python3
"""Render `skills/finding-a-catalog-skill/SKILL.md`'s body from the catalog.

The catalog's directory has to be a SKILL, because a skill is the only
artifact that travels: a subscriber installs into `.claude/skills/` and
README.md stays behind (#229). An agent that cannot see what the catalog
covers concludes the coverage is absent and writes the guidance again.

It travels only once someone adds it, though. `npx skills update` refreshes
what a repo already has and never adds anything, so the directory reaches a
consumer repo on a per-repo `npx skills add` and not before -- and the skills
CLI resolves this catalog's default branch, so it becomes installable at the
dev -> main promotion, not at the merge into `dev`. Distribution is `opt-in`
in docs/placement-map.json, which is the accurate word.

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

WHAT THE GATE COVERS, stated precisely because the difference matters to the
agent holding the file. MEMBERSHIP is unrepresentable-to-drift: add, rename or
delete a skill without regenerating and `validate-skills` fails on the byte
comparison. MEANING is not: `owns` is editorial text with one owner in the
map, and a skill's body can be rewritten from top to bottom without anything
requiring its fragment to be restated. The rendered header says so, rather
than letting a reader infer a freshness guarantee the gate does not make. The
one instance of that class which IS gated is retirement -- `validate_skills`
requires a skill whose description opens `SUPERSEDED` to sit in the
`deprecated` family, because a directory that routes to a retired skill causes
the duplication it exists to prevent.

THE BYTE BUDGET, which is the whole reason the format looks like this.
`validate_skills.SIZE_LIMIT` caps a skill body at 8192 bytes, and this body is
the one artifact in the catalog that grows every time the catalog does.

No ceiling is recited here. `ceiling()` MEASURES it, by rendering the real tree
with synthetic skills appended at today's observed density (skills per family,
mean name length, worst-case `owns`) until the reserve binds -- so every number
this tool prints is a measurement of the tree in front of you, and no rung can
go stale between the arithmetic and the catalog. Run the generator with no
arguments to see today's:

    python3 .github/scripts/gen_skill_directory.py

What the source could NOT be, measured over the catalog on `dev`:

    README purpose column  sum 8515 B  -- over the whole cap before a single
                                          name or bullet is added. This is the
                                          text #229 proposed reusing.
    frontmatter description sum 27363 B -- 3.3x the cap, and a trigger surface
                                          ("Use when about to...") rather than
                                          a statement of what a skill owns.

The per-skill fragment costs roughly half the ceiling -- `levers()` measures
exactly how much, on demand. It is paid anyway, because the fragment is the
part that answers the question #229 is about: an agent reading `visual-polish`
and `token-frugal-tooling` as bare names still cannot tell whether either
covers what it is about to write, and a shortlist you cannot narrow is a list.

One number outside this file's control, for the record: clud-bug's shipped
workflow TEMPLATE overrides its skill cap down to 4000 (validate_skills.py:83,
clud-bug#301). Against this body, that cap cuts the listing off partway and
takes every section after the cut with it -- "Deliberately not here" included,
which is the part that stops a reader concluding coverage is absent. The
header's "not seeing a skill is not evidence that none exists" survives,
because it sits in the first paragraph. Exactly how many rows are lost is one
command against the rendered body, and it moves whenever the prose does, so it
is not written down here. That is an argument with clud-bug, not a budget this
catalog's own gate applies.

CLI:

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

# The family a superseded skill belongs in. `validate_skills` cross-checks it
# against the skills themselves: a description opening `SUPERSEDED` filed
# outside this family is a routing error the byte comparison cannot see,
# because both sides of that comparison agree with each other.
DEPRECATED_FAMILY = "deprecated"

# `owns` is a fragment, not a sentence. It is paid once per skill, so it sets
# the ceiling: a row costs 10 bytes of markup + the name + this. Raising it is
# a decision about how many skills the directory can hold, not a formatting
# preference -- `ceiling()` measures what today's value buys and `levers()`
# measures what changing it would.
OWNS_MAX_BYTES = 32

# The generator refuses over this rather than over SIZE_LIMIT itself. The
# reserve is what stops the NEXT skill added from being the one that discovers
# the cap in CI: 8192 - 7900 = 292 bytes is room for several more rows.
SIZE_LIMIT = 8192
MAX_BODY_BYTES = 7900

# --- the prose. Edit here; the file is generated. --------------------------

HEADER = """
# Finding a catalog skill

Every skill in the **thrillmade/agent-skills** catalog, grouped by what it
owns. Generated from `docs/placement-map.json` and gated: add, rename or
delete a skill without regenerating and `validate-skills` fails, so this list
cannot go quietly incomplete the way a hand-kept table does.

**Read it before you write a rule.** Before authoring a convention, a
checklist, a house standard or a "how we do X" doc -- and before saying
"nothing covers this". The catalog is bigger than the set installed in any one
repo, so *not seeing* a skill is not evidence that none exists. Check here
first; that check is one read, and writing the guidance again is not.

**What a line is.** The fragment after each name says what that skill *owns*,
not what it says -- editorial text, gated for presence and length but not for
freshness against that skill's own body. Enough to shortlist two or three;
then open them. A skill you do not have yet:

```
npx skills add https://github.com/thrillmade/agent-skills --skill <name>
```

**What this is not.** Not a listing of your `.claude/skills/` -- a repo holds
only what it subscribed to, plus anything it authored locally -- and not a
view of the wider skills.sh ecosystem. This indexes one catalog.
"""

NOT_HERE_INTRO = """
## Deliberately not here

A map showing only what is inside teaches you the outside does not exist,
which is the same mistake inverted. These are gaps this catalog knows it has.
Each count is re-measured whenever this file is generated, over every skill's
name and frontmatter description -- the surface that decides whether an agent
finds it. A gap that had since been filled would refuse to render rather than
go on advertising itself:
"""

NOT_HERE_OUTRO = """
Not being named above is not evidence of absence either. Search `skills/`
before concluding a second time -- and control the search against a term you
know is there, the way the counts above are controlled.
"""

# Each probe: the phrase, and what it stands for. `render()` counts the skills
# whose TRIGGER SURFACE matches it and REFUSES to render if a count is no
# longer zero -- the claim is measured at generation time, not typed once and
# left to rot, which is the exact defect #229 filed against the README table.
NOT_HERE_PROBES = [
    (
        "red before green",
        "**TDD mechanics** -- red before green, one failing test at a time. In "
        "the `superpowers` plugin, not here",
    ),
    ("test-driven", "**The same discipline under its other name**"),
    # Closed 2026-08-18 (#225): `composing-a-screen` now names both gulfs in its
    # trigger surface and carries a checkable step for each (DOET rev. ed. 2013
    # ch. 1), so `gulf of execution` stopped matching 0 and the probe was
    # removed rather than narrowed -- nothing in this pair is still uncovered.
    # Norman's constraints, forcing functions and natural mapping remain a real
    # gap (declared in `empirical-design-principles`, not probed here because
    # that skill's own disclaimer text would make the matcher self-trigger).
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
  <https://github.com/thrillmade/agent-skills/tree/main/skills/curating-a-skill-catalog>
"""


def _trigger_surface(md: Path, name: str) -> str:
    """A skill's name plus its raw frontmatter block -- NOT its body.

    The difference is load-bearing in both directions.

    Outward: the probe scan used to read whole bodies, so one cross-reference
    in one skill ("`superpowers:test-driven-development` owns that") reddened
    the whole gate, with the error filed against THIS file, on a PR that never
    touched it -- including a foreign release-sync PR for one of the nine
    `repo-mirrored` skills. That is the same hazard the design rejected a
    required frontmatter key to avoid, walking in the other door.

    Inward: a skill "covers" a topic when its trigger surface says so, because
    the trigger surface is what decides whether an agent ever loads it. A body
    that mentions a phrase in passing is a pointer, not coverage. Read as raw
    text rather than parsed YAML because this file is stdlib-only, and a
    folded scalar's bytes are exactly what we want to search anyway.
    """
    text = md.read_text(encoding="utf-8")
    front = ""
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        if end != -1:
            front = text[4:end]
    return f"{name}\n{front}"


def _matching_files(root: Path, phrase: str) -> list[str]:
    """Skill names whose trigger surface contains `phrase`, case-insensitively.

    The directory itself is excluded: it is a map of coverage, not coverage --
    a name printed here is not a skill that owns the topic. (The control is
    what stops this exclusion from silently becoming "match nothing at all".)
    """
    needle = phrase.lower()
    hits = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        if d.name == DIRECTORY_SLUG:
            continue
        md = d / "SKILL.md"
        if md.exists() and needle in _trigger_surface(md, d.name).lower():
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
            "probes now match the trigger surface of skills in this catalog: "
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

    Refuses rather than degrades, and the reason is the same one the whole
    file has: a directory rendered from a map that failed to load is a SHORT
    directory, and a short directory reads exactly like a complete one to the
    agent holding it.
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


def _row(slug: str, owns: object, bare: bool = False) -> str:
    """One listing row, and the single owner of the row format: `ceiling()`
    prices growth by rendering through this, so the price and the page cannot
    be computed two different ways.
    """
    return f"- `{slug}`" if bare else f"- `{slug}` — {owns}"


def _body(
    dirs: list[str],
    families: list,
    skills: dict,
    not_here_text: str,
    bare: bool = False,
) -> str:
    """The document, from inputs already validated by `_inputs()`."""
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
            parts.append(_row(slug, skills[slug].get("owns"), bare))
        parts.append("")

    parts.append(not_here_text)
    parts.append("")
    parts.append(SOURCES.strip())
    return "\n".join(parts) + "\n"


def _inputs(
    root: Path = ROOT, map_path: Path = PLACEMENT_MAP
) -> tuple[list[str], list, dict, str]:
    """`(dirs, families, skills, not_here_text)` -- every input to the body,
    each already refused-on if unusable. Shared by `render()` and by the
    growth measurement, so both price the same document.
    """
    dirs = sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []
    if not dirs:
        raise SystemExit(
            f"Refusing to build a directory from zero skills under '{root}'. This "
            "script is cwd-relative; a run from the wrong directory renders an empty "
            "list and nothing about it looks wrong. Run it from the repo root."
        )

    families, skills = load_map(root, map_path)

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

    return dirs, families, skills, not_here(root)


def render(root: Path = ROOT, map_path: Path = PLACEMENT_MAP) -> str:
    """The rendered SKILL.md body -- everything after the frontmatter's `---`.

    A pure function of the tree plus the map, with `root` a parameter so tests
    drive it over a tmp_path. It reads no git history at all, which is why the
    gate can compare the WHOLE body rather than one recomputable field.
    """
    return _body(*_inputs(root, map_path))


# --- growth, measured rather than modelled ---------------------------------


def _scaled(families: list, route_scale: float) -> list:
    """`families` with each routing line cut to `route_scale` of its length."""
    if route_scale >= 1.0:
        return families
    out = []
    for fam in families:
        g = dict(fam)
        routes = str(fam.get("routes", ""))
        g["routes"] = routes[: max(1, int(len(routes) * route_scale))]
        out.append(g)
    return out


def _grown(
    dirs: list[str],
    families: list,
    skills: dict,
    extra: int,
    *,
    owns_max: int = OWNS_MAX_BYTES,
    route_scale: float = 1.0,
) -> tuple[list[str], list, dict]:
    """The same catalog with `extra` more skills, at TODAY'S shape.

    Every parameter of a synthetic row is measured off the real tree -- mean
    name length, mean family title and routing-line length, and skills per
    family, so new families are paid for at the density the catalog actually
    has rather than at one that flatters the answer. `owns` is worst-case (the
    full cap), because a ceiling is a promise and a promise is made at the
    worst case.
    """
    fams = _scaled(families, route_scale)
    shown = [
        f for f in fams if any(skills.get(s, {}).get("family") == f.get("id") for s in dirs)
    ] or fams
    per_family = max(1, round(len(dirs) / len(shown)))
    name_len = max(2, round(sum(len(d.encode("utf-8")) for d in dirs) / max(1, len(dirs))))
    title_len = max(
        1, round(sum(len(str(f.get("title", "")).encode("utf-8")) for f in shown) / len(shown))
    )
    routes_len = max(
        1, round(sum(len(str(f.get("routes", "")).encode("utf-8")) for f in shown) / len(shown))
    )

    owns = "x" * owns_max
    d2, s2, f2 = list(dirs), dict(skills), list(fams)
    fid = ""
    for k in range(extra):
        if k % per_family == 0:
            fid = f"synthetic-{k // per_family}"
            f2.append({"id": fid, "title": "T" * title_len, "routes": "R" * routes_len})
        name = f"s{k:0{max(1, name_len - 1)}d}"
        d2.append(name)
        s2[name] = {"family": fid, "owns": owns}
    return d2, f2, s2


def ceiling(
    dirs: list[str],
    families: list,
    skills: dict,
    not_here_text: str,
    *,
    limit: int = MAX_BODY_BYTES,
    owns_max: int = OWNS_MAX_BYTES,
    bare: bool = False,
    route_scale: float = 1.0,
    stop: int = 400,
) -> int:
    """How many skills this format holds before `limit` binds.

    Not a model with constants somebody typed: each candidate size is actually
    rendered through `_body()` and weighed. Returns the largest catalog size
    that still fits -- or `len(dirs)` when the tree is ALREADY over, in which
    case there is no headroom to report and the caller is printing a refusal
    anyway.
    """

    def fits(extra: int) -> bool:
        d2, f2, s2 = _grown(
            dirs, families, skills, extra, owns_max=owns_max, route_scale=route_scale
        )
        return len(_body(d2, f2, s2, not_here_text, bare).encode("utf-8")) <= limit

    if not fits(0):
        return len(dirs)
    extra = 0
    while extra < stop and fits(extra + 1):
        extra += 1
    return len(dirs) + extra


def levers(root: Path = ROOT, map_path: Path = PLACEMENT_MAP) -> str:
    """What each size lever is worth, measured on the tree in front of you.

    Returns "" rather than raising: this is decoration on a refusal that has
    already been decided, and a measurement that cannot be taken must not
    replace the refusal with a traceback.
    """
    try:
        dirs, families, skills, nh = _inputs(root, map_path)
    except SystemExit:
        return ""
    return (
        f"{len(dirs)} skills today, and this format holds "
        f"{ceiling(dirs, families, skills, nh)}; "
        f"with `owns` capped at 24 bytes, "
        f"{ceiling(dirs, families, skills, nh, owns_max=24)}; "
        f"with the family routing lines halved as well, "
        f"{ceiling(dirs, families, skills, nh, owns_max=24, route_scale=0.5)}; "
        f"with bare names and no fragment at all, "
        f"{ceiling(dirs, families, skills, nh, bare=True)}."
    )


def size_error(body: str) -> str | None:
    """The refusal message when the rendered body no longer fits, or None.

    Names the levers and NOT their worth. Every number in it is derived from
    the body and the two limits; what a lever buys is measured by `levers()`
    at the moment it is asked, because a rung's value typed into prose is
    exactly the hand-kept number this whole change exists to delete.
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
        "The levers, cheapest first: "
        "(1) cut OWNS_MAX_BYTES in .github/scripts/gen_skill_directory.py, which "
        "is paid back once per skill; "
        "(2) shorten the family `routes` sentences in docs/placement-map.json -- "
        "one sentence is paid once and covers a whole family; "
        "(3) drop the per-skill fragment and list bare names, which costs the "
        "column that does the work, so spend it last; "
        "(4) retire skills. At this size the cap is information about the "
        "CATALOG rather than about the directory, and `curating-a-skill-catalog` "
        "already owns demotion. "
        "Run `python3 .github/scripts/gen_skill_directory.py` for what each lever "
        "is worth, measured on this tree rather than recited. "
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


def _report(n: int) -> str:
    """The one report line, with the headroom measured rather than asserted."""
    try:
        dirs, families, skills, nh = _inputs()
    except SystemExit:
        return f"{n} body bytes, {MAX_BODY_BYTES - n} under the reserve"
    room = ceiling(dirs, families, skills, nh) - len(dirs)
    return (
        f"{n} body bytes, {MAX_BODY_BYTES - n} under the reserve; "
        f"room for {room} more skills at today's density"
    )


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
        measured = levers()
        if measured:
            print(f"measured just now: {measured}")
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
        print(f"OK: {path} is current ({_report(n)}).")
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
