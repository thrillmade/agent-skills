---
version: "878bc9780069"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: proving-an-absence
description: Use when about to report that something is missing, unbuilt, not covered, unimplemented or broken — a grep or find that returned nothing, "no test covers this", "the route/token/file does not exist", "I could not reproduce it". Also fires when stating a count, size or measurement you did not just run the command for, and when reviewing someone else's finding that something is absent.
---

# Proving an absence

An empty result has three causes, not two: the thing is absent; the probe is
broken; or it is there but out of reach — spelled differently, generated at
build time, outside the paths searched. The output distinguishes none of them.
Diagnostic PCR runs an internal control for this: without one a negative can
mean no target was present, "but it could also mean that the reaction was
inhibited."

Absence of evidence *is* evidence of absence — the biconditional falls out of
the probability axioms (Sober) — but only as strong as the chance the probe
would have hit. Establishing that chance cheaply is the job.

## When to use

- About to write "X does not exist", "nothing implements Y", "no test covers Z".
- Reproducing a reported failure — failing to reproduce is an absence claim.
- Auditing a plan or catalog for stale or unbuilt claims.
- Stating any number, or reviewing a finding that reports something absent.

## When NOT to use

Not for claims of success — "the build passes", "tests are green". That is
`superpowers:verification-before-completion`; this is its mirror, for failure
and absence.

Not for an absence that is a *decision*: "we are not building that yet" is a
refusal, and belongs in the plan of record with its argument.

## Control-test the probe

Run the same command against a case you know hits. If the control comes back
empty too, the probe is broken and the target unknown. From writing this skill:

```
find ~/.claude -maxdepth 6 -type d -name verification-before-completion  # 0
find ~/.claude -maxdepth 6 -type d -name brainstorming  # 0 ← control
```

"That skill is not installed" would be wrong: the control names one known
installed and came back empty too. At `-maxdepth 7` both return 2 — the plugin
nests skills under a *version* directory the depth cut off.

**Internal, not external** — same command, tree and flags, one substitution. A
control run somewhere clean proves the binary works, not that the condition that
broke the measurement is gone; PCR coamplifies its control in the same tube.

**At least as hard as the target** — same nesting depth, generation status,
casing risk. A control hitting a top-level string rules out gross failure and
licenses nothing about a path excluded by `.gitignore`, a nested workspace or a
minified bundle. Passing, it says the probe runs, not that it reaches *this*
target: cause three survives a clean control.

**The environment is part of the instrument.** Config branching on a platform
variable makes local and deployed builds run different configurations by
design. Artifacts carry the mode they were built in: where a framework narrows
`process.env.NODE_ENV` by mode, a dev-build directory keeps the wider type, so
the production type error never fires locally. Delete the build directory
before believing a local pass; a worktree with no installed dependencies fails
for reasons unrelated to the code. Only 32.3% of 402 published systems papers
rebuilt within 30 minutes (Collberg & Proebsting): pin tree, branch, artifacts,
dependencies and env vars before saying "it does not build". Before "not
reproducible", reproduce a failure you *know* is there — the commit before the
fix, same tree, artifacts deleted.

Probes fail silently and structurally: a depth limit; a path or glob anchored at
the repo root (`app/**`) when the app is nested at `web/app/`; a case-sensitive
match; a refactored name; a scanner opted out of detection. None error. All
read like absence. Nobody has counted this rate for code search;
evidence synthesis has — 90.5% of assessed Cochrane MEDLINE strategies held an
error, 82.5% one that could lower recall, reproduced 13 years later. Boolean
strategies, not ripgreps: take the direction, not the number.

## Grep is the wrong instrument for a derived system

Where a value is generated rather than written, searching for it finds nothing
and the value is still there — no better search fixes a wrong artifact.
Registry-, codegen-, DI- and convention-driven systems share one shape: one
declaration, many derived outputs.

Worked example — a route registry the nav derives from:

```
rg "/pricing" app/{header,footer}.tsx app/sitemap.ts  # exit 1
rg "/pricing" app/routes.ts  # every hit is here
```

"The page is not in the nav" is false. Ask what *generates* a route, token or
class before reporting it absent — and run it from the directory those paths are
relative to: from anywhere else `rg` exits **2** (error), not 1 (no match), and
a caller reading only "no output" cannot tell them apart.

Instruments have blind spots by design — static-analysis authors coined
*soundiness*, knowing no realistic whole-program analyser avoids unsound
choices on purpose. `@import "tailwindcss" source(none)` disables Tailwind's
automatic detection, so utilities live or die on an explicit `@source` list,
not on anything a grep of components shows. A green suite is the same shape:
testing is "hopelessly inadequate for showing their absence" (Dijkstra). Name
the blind list.

## Report the search, not the world

Write what you ran and where. Not "the token is unused" but "not found by
`rg 'token' packages/tokens/src` on `main`, clean tree". PRISMA 2020 item 7
demands as much of a systematic review — "the full search strategies … including
any filters and limits used" — and code adds one thing bibliographic search
never needs: the environment. Reported so, a too-narrow search gets widened
where a bare "does not exist" is retracted. Same for positive numbers: never
recite a count — measure it and show the command; plans get caught asserting
totals their own generated diagram contradicts.

**Scale the effort to the prior.** A negative's worth depends on prevalence as
much as sensitivity — "the rarer the abnormality the more sure we can be that a
negative test indicates no abnormality" (Altman & Bland). If a
plan, a stack trace or a registry says it exists, one clean probe is weak; if
nothing ever suggested it, one controlled probe nearly settles it.

**Expect most flags to die, and audit the audit.** Worked example: an audit of a
149-claim plan flagged 73; a refuter confirmed 30 and killed 43, mostly
historical statements read as present tense. 30 of 73 is a 41% hit rate, the
arithmetic of a low-prevalence search, not an obstructive panel. Nobody counted
what the audit *missed*, so "the other 119 are current" is itself an
uncontrolled absence claim.

## Verification

Answer all five; report the command and tree, not a bare "does not exist":

1. What command produced the empty result, in which directory, branch and
   artifact state?
2. What known-present case did it hit, and was that as hard as the target?
3. If the value is generated, what generates it, and did I search there?
4. What does this instrument deliberately not see?
5. Given who or what asserted it exists, is one probe proportionate?

## Cross-references

- [guarding-a-regression](../guarding-a-regression/SKILL.md) — "the mutation
  never reached the code" is an absence claim; mutation is its control.
- [retiring-a-superseded-decision](../retiring-a-superseded-decision/SKILL.md) —
  an old-value grep finding nothing.
- [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) —
  refute-first review, where an uncontrolled absence claim dies.
  `superpowers:systematic-debugging` — a failed reproduction is one.

## Sources

- Hoorfar et al., internal controls in diagnostic PCR, 2003, free at PMC309040,
  doi:10.1128/JCM.41.12.5835.2003.
- Sober, absence of evidence, 2009, doi:10.1007/s11098-008-9315-0 · Altman &
  Bland, 1995, doi:10.1136/bmj.311.7003.485; predictive values 1994,
  doi:10.1136/bmj.309.6947.102.
- Sampson & McGowan, search errors, 2006,
  doi:10.1016/j.jclinepi.2006.01.007; reproduced 2019, doi:10.5195/jmla.2019.567
  · PRISMA 2020 item 7, doi:10.1136/bmj.n71 · Collberg & Proebsting,
  repeatability, 2016, doi:10.1145/2812803.
- Livshits et al., "In Defense of Soundiness", 2015, doi:10.1145/2644805 ·
  Dijkstra, "The Humble Programmer", CACM 1972 · tailwindcss.com/docs,
  "Detecting classes in source files".
