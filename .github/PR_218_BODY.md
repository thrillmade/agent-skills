Closes the class in #213, with the two conditions you set: mutation-tested with the mutation committed, and an escape hatch that is explicit and cheap.

## What it detects

Normalise markdown skill links back to their link text, then compare word **multisets**, not sequences. A rewrap, reorder or moved paragraph scores exactly zero by construction — a sequence diff would report a move as a delete here plus an insert there.

**Normalisation is load-bearing, not decorative.** Measured on the real sweep (`pytest tests/test_check_prose_retention.py -k without_normalisation -q`, and directly against the fixtures):

```
web-interface-guidelines-review   normalised  13   raw  -41
clud-bug-collaboration            normalised  44   raw   35
session-heartbeat                 normalised  49   raw   40
```

Un-normalised, the sharpest case reads as a **41-word gain** — the gate would have gone green on the very file that lost the cross-skill routing rule. That is now a committed test.

## The threshold is measured, not chosen

Replayed over every commit reachable from any ref that touches a `SKILL.md` — **61 commits** by git's default history simplification, **62** with `--full-history` (`git log --all --format=%H -- 'skills/*/SKILL.md' | sort -u | wc -l`, and the same with `--full-history` added).

The floor is **not** a single number. It is measured **per scope**, because frontmatter, prose and fenced code each have their own word economy:

```
FLOOR = {"prose": 2, "frontmatter": 3, "code": 3}   # .github/scripts/check_prose_retention.py:171-175
```

**The band above each floor and below the smallest real removal is empty** in every scope — prose has nothing between 3 and 12, frontmatter nothing between 4 and 11, code nothing between 4 and 58 (`.github/scripts/check_prose_retention.py:138-170` carries the full distribution and the replay command). Each floor sits at 4x margin or better below the smallest genuine removal in its scope.

Fires on **15** of the reachable file-revisions, unchanged before and after this round's fixes — re-confirmed with a script that replays `Loss()` over `git log --all -m -- 'skills/*/SKILL.md'` (every commit touching a `SKILL.md`, diffed against every parent it has) and counts how many exceed a floor.

## The escape hatch is a row you paste

The failure prints the exact row for `docs/prose-removals.md`. Rules keep it from becoming the blanket exemption you deliberately removed from the size gate:

- **Only a row your own change adds counts.** A row already on the base is somebody else's declaration about somebody else's deletion. Inheriting them rebuilds the `limitBytes` failure — one line, exempts everything, silently.
- **The count must cover what the gate measured.** It cannot be written blind, and it puts the magnitude of the cut in the diff where a reviewer reads it. It is a floor, not an exact match: a later commit in the same PR that adds words back does not invalidate an already-correct row.
- **The unedited placeholder is rejected.** Deciding the words are safe to lose is the one part that cannot be automated.
- **Rows are counted by `(skill, words)`, not by the reason text.** Editing an inherited row's wording — a typo fix, a trailing full stop — must not manufacture a fresh declaration for an unrelated cut of the same size; what has to grow between the two ledgers is the count of rows at that size.

The failure text names what is actually free under this metric — rewrap, reorder, an in-scope move, a similar-length reword — and says plainly that a genuine tightening is a declared removal like any other and costs one row: the word-multiset metric this gate uses makes "the same thing in fewer words" fewer words, by construction, so the message no longer tells an author to do the one thing that will fail again on the re-push.

## Proof it can fail

**25 mutation tests** (`pytest tests/test_prose_retention_mutations.py -q --collect-only | grep -c test_mutation_turns_the_suite_red`). Each applies one textual mutation, asserts it matched the source **exactly once** (so a rename cannot silently turn it into a no-op that "proves" the suite works by testing an unmodified file), runs the real suite in a subprocess, and asserts red. A control asserts the unmutated suite is green in the same harness — without it, every red is equally explained by a broken harness.

Each mutation is caught by the test that is *about* that behaviour, not incidentally by an unrelated one:

```
prose_floor_off_by_one       -> test_three_words_lost_from_prose_fires
ledger_count_ignored         -> test_a_row_that_understates_the_cut_does_not_count
ledger_placeholder_accepted  -> test_the_printed_row_pasted_unedited_does_not_count
gains_ignored                -> test_rewording_at_similar_length_is_free
```

## Verified against real commits, both directions

```
8b4e1c8 -> 42f881c   exit 1   names all three files, quotes what went
8b4e1c8 -> a2a562c   exit 0   21 files, carrying the full link conversion
8b4e1c8 -> 8b4e1c8   exit 0   no-op
235 tests pass (pytest tests/ -q)
```

No synthetic data — the fixtures are the real before/after pairs with a `PROVENANCE.md`.

## Fixed in review

An independent panel found five defects after the first draft; all but one (explicitly deferred, see below) are fixed in this PR's later commits and recorded in `docs/decisions-branches/feat__prose-retention-gate.md`:

- The failure message told an author whose file was over budget to "rewrite the section tighter... a rewrite that says the same thing in fewer words scores zero here" — false of a word-multiset metric. Rewritten to say what genuinely scores zero (rewrap, reorder, an in-scope move, a similar-length reword) and that a real tightening is a declared removal like any other cut.
- A ledger row's reason could be edited — a typo fix, a trailing full stop — and Counter subtraction read the edit alone as a fresh declaration, covering an unrelated cut to the same skill nobody wrote a reason for. Rows now count by `(skill, words)`, dropping the reason from the matching key while still requiring one to be present.
- The workflow claimed the org ruleset requires `test` by name and knows nothing about this workflow. Measured directly: neither `main` nor `dev` (the branch this PR targets) carries a `required_status_checks` rule at all, so nothing here is a merge condition today, `test` included.
- The local default only ever tried `main`, but every branch in this repository forks from and targets `dev` — so a branch cut from `dev` could see a real loss read as a net gain against `main`'s older snapshot. The default now tries `dev` first.
- An invalid UTF-8 byte in a `SKILL.md` crashed the process with a bare, unannotated stack trace. It still fails closed, now with a proper `::error file=...::` annotation.
- **Deferred, not fixed:** when the same words that vanished from one scope reappear verbatim in another (e.g. a clause wrapped in a code fence), the message says "Gone", which is false. Historically zero occurrences and the correct fix touches the `Loss` class's core data model, so it is left for a follow-up rather than rushed into this PR.

## Known limits, stated rather than papered over

- **The workflow has never executed on GitHub Actions.** YAML validated, shape asserted in tests, revision resolution run locally against real commits — but the PR path and the `push` fallback are untested in the real runner. This is the biggest unverified thing in the PR.
- **It is not a required status check, and neither is anything else on this repository today.** No ruleset on `main` or `dev` names `required_status_checks`. Making this (or `test`) a merge condition is an org-ruleset change, out of this PR's scope.
- **Whole-file additions and deletions are out of scope** by choice — deleting an entire skill is a visible, reviewable act; this gate is about content vanishing *inside* a file that still looks fine.
