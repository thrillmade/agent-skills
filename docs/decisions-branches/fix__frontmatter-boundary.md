← back to [docs/timeline.md](../timeline.md)

## 2026-08-24 10:41 - Anchor the frontmatter closing delimiter: a line that merely STARTS with dashes was closing the block

**Reasoning:** protocol#103's fifth-pass panel found it, in already-merged code. SPEC 2.1 step 2 now says the block 'closes at the first subsequent line that is EXACTLY ---'. FRONTMATTER_RE was rb'^---\\n(.*?)\\n---' with nothing requiring the closing --- to be followed by a newline or EOF, so it also matched the leading three characters of ---- or '--- not a close', ending the block one character early. An identity line after such a line then sits in what this module treats as body, is not elided, and the digest moves -- so this implementation and one written from the SPEC prose compute DIFFERENT digests from IDENTICAL bytes. Reproduced before fixing: spec-faithful 92dfcd7a1f8c vs reference 03a00b6b4edb on the same input.

**Alternatives considered:** Leave it and file an issue, since no real skill triggers it today (verified: 0 of 56). Rejected -- the catalog already contains a file carrying four bare --- lines, so the shape is one plausible edit away, and digest is the subscriber-facing identity: the failure is silent and the wrong answer is indistinguishable from the right one. Also considered consuming the newline rather than a lookahead: rejected, m.end() is used by callers to slice the file, and consuming would move a byte across that seam for every conforming file.

**Implications:**
- A LOOKAHEAD, so m.end() stays exactly where it was and conforming files are byte-for-byte unaffected: 0 of 56 published digests moved, checked against origin/dev's skill-versions.json. Two regression tests assert through digest() rather than by matching the pattern -- a test on the regex passes its own mutation and still goes green when the bug ships again. Mutation-tested: restoring the unanchored pattern, grepped in the tree at line 90, turns both red; restored byte-identical, 342 green. The deeper lesson is that the SPEC was verified against this implementation and still did not catch it, because both were read by the same pair of eyes -- the divergence only surfaced when a panel wrote a third implementation from the prose alone.

---

