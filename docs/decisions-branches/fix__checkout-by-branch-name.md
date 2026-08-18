← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 09:06 - Check out the PR head SHA, not the branch name, in check-links and check-derived-docs

**Reasoning:** Both jobs checked out github.event.pull_request.head.ref, and delete_branch_on_merge deletes that ref the instant a PR merges — a run still in flight then dies at the checkout step with 'A branch or tag with the name ... could not be found', manufacturing a red X on a merged PR for a run that never touched the actual change. Confirmed on #216's merge (both jobs failed this way within 5s of merge) and reproduced at the git level: fetching a deleted branch by name fails (rc=128) while fetching the same commit by SHA still succeeds (rc=0). AGENTS.md's carve-out documenting this as 'an artifact, not a verdict' is replaced with a note that the mechanism is fixed, so the exception is no longer standing guidance agents must remember.

**Alternatives considered:** Guard the self-heal/auto-fix jobs' branch-existence with a live GitHub API check before running, instead of just fixing the two read-only checkouts — rejected for this change: those push-back jobs were not observed failing this way (self-heal shows 'skipping' on #216, not 'failure'), and adding untested branch-existence-check logic to a job I cannot execute here is exactly the kind of unverified guard the bar here warns against. Left as a residual noted in-line rather than a speculative fix.

**Implications:**
- This is a hand-patch on top of logmind's own generated templates (check-doc-links.yml v5, regen-timeline.yml v4) — the next 'logmind init'/template regen will overwrite it unless the same fix lands in logmind's upstream templates. Filing that forward is still owed; this commit only fixes agent-skills' checked-in copy.

---

