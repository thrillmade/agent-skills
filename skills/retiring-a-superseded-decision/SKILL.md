---
version: "1.0.0"
digest: "5c55077b9a1f"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: retiring-a-superseded-decision
description: Use when a decision reverses an earlier one — a typeface, colour, route, vendor, threshold, page type, API name or file location replaced — and a README, plan doc, ADR, spec, comment, fixture or generated page may still assert the old value. Also when an approval or review outcome landed in conversation and is not yet in the plan of record, or when an audit has just declared a document clean.
---

# Retiring a superseded decision

A reversal is not landed when the new value is in place. It is landed when every
place still asserting the old one has been found and classified. Until then the
document reads as true to the next reader, who cannot tell which of its
sentences you were thinking about.

Divergence is the predicted result of a second copy. DRY, as Hunt & Thomas state
it, demands "a single, unambiguous, authoritative representation" per piece of
knowledge — docs and the build, not only code. It says don't make the copy; it
is silent on a repo that has them.

## When to use

- A decision replaces an earlier one: typeface, colour, route, vendor,
  threshold, file location.
- You are about to edit a document that others derive from or quote.
- An approval, gate outcome or review verdict happened in conversation only.
- An audit reported a document clean and edits have landed since.

## When NOT to use

- The decision is new and replaces nothing — no old value to hunt.
- You are tuning a value *inside* a recorded decision: one colour in a palette
  that ships as one locked decision amends that record, it does not reverse it.
- Your plan of record lives in a wiki, not the tree — none of these searches
  run. Move it into version control, or use a format carrying supersession as
  data (`adr-tools -s` flips the old record's status as it writes the new).

## Search the old value, not the new one

The step that gets skipped, and skipping it is invisible. The new value is
already where you put it; grepping it returns your own edit and reads as
confirmation. Only the **old** value shows where the tree disagrees.

The pull toward the wrong search is documented, not sloppiness: Klayman & Ha's
*positive test strategy* — testing cases expected to have the property, not those
expected to lack it. They defend it as usually a good heuristic, so claim only
the narrow thing: here it is uninformative **by construction** — the instances
it returns are the ones you just made.

```sh
git grep -nIi -- 'OldValue'   # whole repo: code, comments, fixtures, config
```

Scope it to the repo, not `docs/` — stale prose hides in READMEs and comments
under code. Ratol & Robillard measured this at rename scale: over half their
identifiers left comments naming the old one, invisible to compilers.

**Never write the count into the document.** A file stating "the search finds
five" that contains the searched string makes itself the sixth on commit — both
counts in an earlier draft of this skill did. Give the command, not the number.

Fluri et al. measured 97% of comment changes landing in the same revision as
their code change — the commonest route to staleness is a location nobody
touched. Enumerate locations; do not only re-search.

## A grep is a list of candidates, not a verdict

Read every hit and classify it. Four kinds come back.

1. **A live claim** — present tense, describes the system now. Correct it.
2. **A historical record** — dated or marked superseded. Leave it. Nygard's ADR
   rule keeps a reversed decision and marks it superseded, because "it's still
   relevant to know that it *was* the decision, but is *no longer* the decision."
3. **An unrelated use of the same string** — the old typeface named by a page
   that really does render in it. Deleting it breaks something, retires nothing.
4. **The old statement is right and the new value is wrong.** iComment triaged 60
   true positives (of 98 reports, two comment topics) into **33 code bugs** and 27
   bad comments, but calls that split "much more difficult" and had 12 confirmed.
   Where both sides are prose, resolve against the record.

Type 2 reads as type 1 in a hurry, and deleting one destroys the record that
stops the old decision returning.

## Correct the item; delete only what nothing depends on

Never strike a line and move on; ask what remains.

**If work remains, the remainder becomes the item.** Worked example: an interlink
rule outlived its anchor and was kept, annotated "the target has no such anchor
now; this rule needs a real destination." The reader learns the rule is blocked
and on what; struck, they learn nothing; left alone, they build the wrong link.
Lethbridge et al. found out-of-date docs "remain useful in many circumstances" —
destroying a stale statement costs the reader; correcting it does not.

**If nothing remains, delete it** — version control records what was built; a
plan padded with finished history is not something to build against.

**Refusals stay, and so does the reason a thing is absent.** Absence has no
author: a routes list missing a redirect cannot say whether that was decided or
forgotten, so leave a marker at the site — `// redirect removed: the target is a
real page now, so this would shadow it`.

**If someone holds a copy that contradicts you, the reversal is content** — it
belongs in the live document, stated as a change, because the circulated version
says the opposite. Otherwise file it as history.

**Do not invent a record to close a gap.** A log with one outcome visibly blank
beats one with a plausible outcome written in. The gap is findable; the
fabrication is not.

## An audit does not inoculate the document

Corrective work is itself a change, made with attention on the change rather
than on what it contradicts. Yin et al. sampled fixes for post-release bugs in
large OS codebases: at least 14.8–24.4% were themselves incorrect, 27% of those
by developers who had never touched the files. That is code, not prose — take
the direction. A morning's cleanup does not protect a document from that
afternoon's edits: one audit's same-day edits produced six of the eight found
that evening.

So **run the old-value search on the edit, not on the document**; Google's
docguide names the enforcement point — "change your documentation in the same CL
as the code change." Two more half-landings:

- **A decision existing only in conversation does not exist.** "The client
  approved X" is incomplete until the plan of record says so, in the same pass.
- **A generated copy is not corrected by correcting its source.** Rerun the
  build and diff the published artefact.

**Where the claim is machine-checkable, make it a check.** doctest, Go examples
and rustdoc doc-tests exist for this class: a documented claim that runs cannot
go stale. Most decisions are not runnable; a CI assertion that the old value
appears zero times outside the history section is.

## Verification

Before claiming it landed:

1. Grep the **old** value across the whole repo, control-tested against a hit
   you know exists — [proving-an-absence](../proving-an-absence/SKILL.md).
2. Classify every hit — live claim / historical record / unrelated / new value
   wrong — and say which; report found and changed as separate counts.
3. Rebuild any generated copy, diff it against the published one, and confirm the
   plan of record states the decision and what it replaced.

## Cross-references

- [proving-an-absence](../proving-an-absence/SKILL.md) — control-testing a grep
  that finds nothing.
- [guarding-a-regression](../guarding-a-regression/SKILL.md) — making that search
  a check that fails when the old value returns.
- [semver-design-tokens](../semver-design-tokens/SKILL.md) — the versioned form
  for tokens: deprecate, keep resolvable, remove on major.

## Sources

- Hunt & Thomas, *Pragmatic Programmer* Tip 15, pragprog.com/tips/ · Nygard,
  "Documenting Architecture Decisions" 2011,
  cognitect.com/blog/2011/11/15/documenting-architecture-decisions · adr-tools
  `-s`, github.com/npryce/adr-tools
- Klayman & Ha, *Psych. Review* 94(2) 1987, doi:10.1037/0033-295X.94.2.211
- Code/comment drift — Ratol & Robillard, ASE 2017, doi:10.1109/ASE.2017.8115624;
  Fluri et al., WCRE 2007, doi:10.1109/WCRE.2007.21; Tan et al. (iComment), SOSP
  2007, doi:10.1145/1294261.1294276 · Lethbridge et al., IEEE Software 2003,
  doi:10.1109/MS.2003.1241364; Yin et al., ESEC/FSE 2011,
  doi:10.1145/2025113.2025121
- Google docguide, google.github.io/styleguide/docguide/best_practices.html ·
  executable docs — doctest, go.dev/blog/examples, rustdoc doc-tests
