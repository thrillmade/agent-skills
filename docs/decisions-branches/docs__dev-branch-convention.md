← back to [docs/timeline.md](../timeline.md)

## 2026-08-15 08:25 - Establish a dev staging branch for agent-skills, and state what batching costs here

**Reasoning:** The CEO asked for the same arrangement protocol has: work lands on dev, an independent adversarial panel is the bar to get in, and promotion to main happens in batches when ready. The convention itself is stated once in protocol's docs/the-dev-branch.md rather than duplicated — one owner per fact — so this section records only what differs in this repository. What differs is that batching costs less here, because more of the gates are per-tree. test, validate skills and check-links each judge the tree they are handed, so six changes checked once is the same assertion as six checked six times. check-derived-docs runs template v4, which regenerates and auto-fixes rather than asking who touched what. Only check-decisions is diluted, and in the same named way as protocol: it sets decision_touched as a presence flag, so one entry satisfies a whole batch, and it only fires above 20 non-docs lines so a docs-only batch never trips it at all. clud-bug-review returns NEUTRAL here, so there is nothing for batching to dilute.

**Alternatives considered:** Duplicate protocol's dev-branch document into this repository, which creates a second copy to keep true; skip the document and hold the convention in memory, which is how a convention stops being applied

**Implications:**
- Four checks hold at full strength, one is diluted in a named way, one does not run. The independent review is what covers the check-decisions gap — it is the only thing applied per change rather than per batch, which is why the bar into dev is a review and not a rubber stamp
- No forge rule protects dev — the rules endpoint returns an empty list — so every rule is a convention held by whoever is working. Acceptable while dev is somewhere work passes through; not acceptable the moment it becomes somewhere work lives
- Every figure in the new section was verified rather than carried across: 0 rules on dev, 112 tests, 49 skills validating cleanly, the presence flag at check-decisions.yml:51-57, and THRESHOLD 20

---

## 2026-08-15 08:40 - Fix four defects the panel found in the dev-branch section, including a 404 on the doc it defers to

**Reasoning:** The panel refuted four claims. First and blocking: the section defers to protocol's docs/the-dev-branch.md as the single authoritative statement and linked it at blob/main, where the file does not exist — it lives on protocol's dev, because protocol batches too and this is the first document to cite it. So an arriving agent following the link got a 404 and no statement of the rules at all. Nothing in CI would ever catch it: logmind check-links validates relative links only, so an absolute URL to another repository is never checked, and the job passed green with the dead link in it. Second: I wrote fires above 20 non-docs lines; check-decisions.yml:65 uses >= not >, so exactly 20 trips it. Third: I answered the check-decisions row as Yes, the same way as protocol while protocol's own doc answers Both ways, and neither is the simple story — same workflow, same lines, no repo difference to justify diverging, on a section whose stated job is recording only what differs. Fourth: I claimed four checks hold at full strength while omitting that none of them gates a merge — agent-skills has no required_status_checks rule and no classic protection, so they are signal rather than gate, which protocol's doc treats as the decisive clause.

**Alternatives considered:** Hold the section until protocol promotes its document to main, which blocks a true statement on someone else's batching schedule

**Implications:**
- The link points at protocol's dev with a note to repoint when it promotes, and states that CI cannot catch this class — an absolute cross-repository URL is unchecked by construction, so the note is the only guard
- The batching claim is narrowed to what the evidence supports. The advantage is two per-tree gates protocol lacks, test and validate skills, not a general statement about four rows: check-derived-docs is a wash because protocol's v11 is also a property of the tree, and check-decisions is identically diluted in both
- I claimed in the PR body that every figure was measured in this pass. The >= was not — it was carried across from the workflow's own header comment, which says >20 and is itself wrong. Reciting a number from a comment is the failure this repo keeps finding, and I did it while asserting the opposite

---

