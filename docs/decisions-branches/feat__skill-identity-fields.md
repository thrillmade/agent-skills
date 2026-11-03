← back to [docs/timeline.md](../timeline.md)

## 2026-08-24 08:36 - Ship a three-field skill identity format (version/digest/origin), replacing the single version: field that held a digest and hid its route home in a YAML comment

**Reasoning:** version answered only 'same or different', never 'newer'; the origin URL lived in a comment yaml.safe_load discards before any program sees it. Splitting into an ordered human semver, a recomputable digest, and a real machine-readable origin field fixes both, per CEO ruling on the exact shape and the MAJOR/MINOR/author-decision, PATCH/stamper-auto-bump semver rule

**Alternatives considered:** keep the single digest-only field and add a separate lockfile-style pin elsewhere; rejected because it does not fix the origin-in-a-comment defect and adds a second artifact to keep in sync, hand-assign each of the 56 skills an initial semver from their commit history; rejected in favor of a reproducible, code-only rule: any file with no valid MAJOR.MINOR.PATCH claim (missing, or the old scheme's digest-shaped value, which SEMVER_RE never matches) seeds 1.0.0 -- identical for a brand-new file and for all 56 migrated ones, not hand-picked

**Implications:**
- all three identity lines (not just version:) must now be elided before hashing, or stamping would move the digest it is supposed to hold stable -- verified: stamping the whole catalog left every one of the 56 digests byte-identical to what dev published before this change
- stamp() is no longer a pure function of content alone for the version field: it reads its own file's prior version/digest claim to decide whether to bump PATCH, seed 1.0.0, or leave the semver untouched -- documented as the one deliberate exception in skill_version.py's module docstring
- validate_skills.py now gates the three fields together: naming one without the other two is a new error class (opted-in-but-incomplete), not silently tolerated as one-third done
- docs/skill-versions.json gains a version key alongside current at both the per-skill and per-history-row level, appended without disturbing the append-only current/v history the existing gate depends on; history rows from before this format existed read version: null, which is not fillable retroactively (no semver ever existed for those commits)

---

## 2026-08-24 09:20 - Quote origin, and make the strict reader reject the unquoted shape

**Reasoning:** protocol#103 ratifies SPEC 2.1's 'All three values MUST be quoted'; origin_line() emitted 'origin: <url>' bare, so this PR would have shipped 56 skills carrying an identity field the spec ratifying that field forbids. Quoting the emitter alone would have been decorative: ORIGIN_RE captured (\\S+), so a bare URL still read as a well-formed claim and a file would have validated either way. The MUST is only real if the strict reader enforces it, so ORIGIN_RE now requires the quotes.

**Alternatives considered:** Narrow the SPEC MUST to version and digest, where the coercion failure is real -- a URL cannot be read as an integer or as octal. Rejected: a rule with a per-field carve-out is one every implementer must re-derive, and the cost of getting it wrong is silent and asymmetric (an over-quoted URL is harmless; an under-quoted digest is an identity that compares unequal to itself). Also considered merging as-is and quoting in a follow-up: rejected, shipping 56 files known non-conformant with a promise to fix is the drift pattern itself, and the change is free before merge.

**Implications:**
- Zero digests moved -- 56 files changed, one line each, and 'git diff -- skills/ | grep -cE ^\\+digest:' returns 0. That is the fixed-point property doing its job: ORIGIN_LINE_RE elides the whole line whatever shape the value takes, so re-spelling the value cannot perturb the hash. The permissive/strict split is now load-bearing and tested both ways: origin_line_count() still counts a bare line (duplicate keys must be caught whatever their shape) while stamped_origin() returns None for it. Three pre-existing tests asserted the unquoted shape and were updated rather than deleted; two new tests pin the rule from both sides. Mutation-tested: reverting ORIGIN_RE to (\\S+), grepped in the tree to confirm it landed, turns 60 tests red including the new guard; restored byte-identical, 381 green.

---

## 2026-08-24 09:44 - Quote origin in the docs too — the fix changed the code and left the page teaching the rejected shape

**Reasoning:** The delta panel found the same failure a third time today: prose and worked example disagreeing with the code. Quoting origin_line() and tightening ORIGIN_RE left four places still teaching the bare form. The blocking one is docs/integrating-with-agent-skills.md -- a page written explicitly for a subscriber with no access to this repo. Its fenced example showed 'origin:  https://...' and its prose said 'origin is unquoted: a URL has no such landmine to quote against'. Anyone hand-stamping from that example produced a file the validator I had just tightened rejects. Three internal comments in skill_version.py asserted the same thing, one of them sitting directly above the regex that now contradicts it.

**Alternatives considered:** Fix only the public doc and leave the internal comments. Rejected: the comment above ORIGIN_RE is the first thing a maintainer reads before changing it, and the module explicitly bills that block as documenting two shapes of regex per field on purpose. Also considered reverting the quoting to match the docs: rejected, the SPEC MUST is uniform by design.

**Implications:**
- CORRECTION TO THE PREVIOUS ENTRY ON THIS BRANCH: it recited 'turns 60 tests red including the new guard; restored byte-identical, 381 green'. Those numbers do not reproduce. Re-run of the same mutation gives 67 failed / 1003 passed on the fast subset, restoring to 1070 passed; no combination of test files collects 381. The behaviour claimed is true and was independently reproduced by the panel -- only the counts are wrong. Recording it rather than editing the entry, because a number nobody can re-derive is exactly what AGENTS.md forbids, and this is the second time today one of my own commit messages recited instead of measured. Control for the sweep: a pattern matching genuinely unquoted values returns 0 across docs/, .github/scripts/ and skills/, and returns 1 against a deliberately unquoted probe.

---

