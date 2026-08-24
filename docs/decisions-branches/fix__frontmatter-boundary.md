← back to [docs/timeline.md](../timeline.md)

## 2026-08-24 10:41 - Anchor the frontmatter closing delimiter: a line that merely STARTS with dashes was closing the block

**Reasoning:** protocol#103's fifth-pass panel found it, in already-merged code. SPEC 2.1 step 2 now says the block 'closes at the first subsequent line that is EXACTLY ---'. FRONTMATTER_RE was rb'^---\\n(.*?)\\n---' with nothing requiring the closing --- to be followed by a newline or EOF, so it also matched the leading three characters of ---- or '--- not a close', ending the block one character early. An identity line after such a line then sits in what this module treats as body, is not elided, and the digest moves -- so this implementation and one written from the SPEC prose compute DIFFERENT digests from IDENTICAL bytes. Reproduced before fixing: spec-faithful 92dfcd7a1f8c vs reference 03a00b6b4edb on the same input.

**Alternatives considered:** Leave it and file an issue, since no real skill triggers it today (verified: 0 of 56). Rejected -- the catalog already contains a file carrying four bare --- lines, so the shape is one plausible edit away, and digest is the subscriber-facing identity: the failure is silent and the wrong answer is indistinguishable from the right one. Also considered consuming the newline rather than a lookahead: rejected, m.end() is used by callers to slice the file, and consuming would move a byte across that seam for every conforming file.

**Implications:**
- A LOOKAHEAD, so m.end() stays exactly where it was and conforming files are byte-for-byte unaffected: 0 of 56 published digests moved, checked against origin/dev's skill-versions.json. Two regression tests assert through digest() rather than by matching the pattern -- a test on the regex passes its own mutation and still goes green when the bug ships again. Mutation-tested: restoring the unanchored pattern, grepped in the tree at line 90, turns both red; restored byte-identical, 342 green. The deeper lesson is that the SPEC was verified against this implementation and still did not catch it, because both were read by the same pair of eyes -- the divergence only surfaced when a panel wrote a third implementation from the prose alone.

---

## 2026-08-24 11:19 - Anchor all four copies of the frontmatter rule, not the one I happened to be looking at

**Reasoning:** The panel found the fix had made things WORSE in one place. skills_current.py carried its own literal copy of FRONTMATTER_RE, and tests/test_skills_current.py asserts the two copies agree on every catalog skill and on a list of awkward shapes. Before the fix both copies were identically wrong, so the invariant held. After it they disagreed on exactly the shape the fix was about -- and skills_current.py is, by its own docstring, the only artifact a subscriber actually runs. The awkward-shapes list did not include a mid-frontmatter fake close, so CI was silent. Grep found FOUR literal copies: skill_version.py, skills_current.py, check_prose_retention.py and validate_skills.py. All four are now anchored.

**Alternatives considered:** Fix only skills_current.py, since the panel graded the other two non-blocking (they were consistently stale together, so no invariant between THEM was broken). Rejected: the defect is not that a copy is stale, it is that one rule has four owners, and leaving two stale preserves the mechanism that produced this. Also considered collapsing the four into one import: rejected as too large for this PR, and filed instead -- validate_skills.py and check_prose_retention.py document their duplication as deliberate, so removing it is a design change, not a cleanup.

**Implications:**
- CORRECTING THIS BRANCH'S OWN EARLIER ENTRY AND CODE COMMENT: both said the lookahead was chosen because a consuming match would shift m.end() and move a byte across the seam callers slice on. That is FALSE -- the panel measured a consuming variant producing byte-identical digests on all 56 real skills, because front+rest reassembly is lossless whichever side the seam falls on. The real reason is a file whose frontmatter closes at EOF with NO trailing newline: a consuming pattern does not match it at all, so stamp() raises ValueError on a validly-formed file. Verified rather than asserted -- consuming matches: False, lookahead matches: True. The fix was right and the reason given for it was not. Also added: a first-not-last test, because a greedy .* variant passed all 342 existing tests while violating the other half of SPEC 2.1 step 2; it now fails. Four shapes added to the paired-copy list, including the one that broke it. 0 published digests moved; fast suite 1086.

---

