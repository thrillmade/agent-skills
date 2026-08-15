← back to [docs/timeline.md](../timeline.md)

## 2026-08-15 08:25 - Establish a dev staging branch for agent-skills, and state what batching costs here

**Reasoning:** The CEO asked for the same arrangement protocol has: work lands on dev, an independent adversarial panel is the bar to get in, and promotion to main happens in batches when ready. The convention itself is stated once in protocol's docs/the-dev-branch.md rather than duplicated — one owner per fact — so this section records only what differs in this repository. What differs is that batching costs less here, because more of the gates are per-tree. test, validate skills and check-links each judge the tree they are handed, so six changes checked once is the same assertion as six checked six times. check-derived-docs runs template v4, which regenerates and auto-fixes rather than asking who touched what. Only check-decisions is diluted, and in the same named way as protocol: it sets decision_touched as a presence flag, so one entry satisfies a whole batch, and it only fires above 20 non-docs lines so a docs-only batch never trips it at all. clud-bug-review returns NEUTRAL here, so there is nothing for batching to dilute.

**Alternatives considered:** Duplicate protocol's dev-branch document into this repository, which creates a second copy to keep true; skip the document and hold the convention in memory, which is how a convention stops being applied

**Implications:**
- Four checks hold at full strength, one is diluted in a named way, one does not run. The independent review is what covers the check-decisions gap — it is the only thing applied per change rather than per batch, which is why the bar into dev is a review and not a rubber stamp
- No forge rule protects dev — the rules endpoint returns an empty list — so every rule is a convention held by whoever is working. Acceptable while dev is somewhere work passes through; not acceptable the moment it becomes somewhere work lives
- Every figure in the new section was verified rather than carried across: 0 rules on dev, 112 tests, 49 skills validating cleanly, the presence flag at check-decisions.yml:51-57, and THRESHOLD 20

---

