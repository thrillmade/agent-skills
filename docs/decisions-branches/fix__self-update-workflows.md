← back to [docs/timeline.md](../timeline.md)

## 2026-07-28 01:38 - Fix two self-update workflows red for six weeks, and make future failures visible

**Reasoning:** Both scheduled workflows have failed every weekly run since early June and nobody noticed, because a scheduled workflow that fails notifies no one. Two distinct root causes, each confirmed from the actual run logs rather than from reading the YAML. logmind-self-update strips the v prefix for a string comparison and then passes the bare version straight to setup-logmind, whose resolver only accepts latest, vMAJOR, or vMAJOR.MINOR.PATCH -- so it errors on 1.2.0. It only surfaced once installed and latest diverged; before that the compare step short-circuited and never reached the bug. clud-bug-self-update is rejected by GitHub itself: GITHUB_TOKEN may never push changes to .github/workflows, and clud-bug update always refreshes those files. That is not grantable through the permissions block -- the repo already solved the identical problem for logmind-self-update with a PAT plus a graceful skip, and this workflow never got that treatment.

**Alternatives considered:** Fix only the version prefix and leave the clud-bug push failing -- rejected, it would stay red and keep training everyone to ignore red. Grant a workflows permission in the permissions block -- not possible; no such GITHUB_TOKEN scope exists. File an issue and defer -- rejected, six weeks of silence is the argument against deferring.

**Implications:**
- Both now go green or skip deliberately. The failure-visibility step matters more than either fix: it opens one issue per workflow and comments on it thereafter, so the next six-week silence cannot happen. I added an AUTHOR FILTER to that dedupe search that the original did not have -- gh issue list --search matches any issue carrying the marker and anyone can open one, so without it an outsider redirects every future failure notice onto an issue they control. Same defect class as the census marker laundering closed in #178, found because I went looking for it. Upstream caveat: the buggy bodies may still ship in the logmind and clud-bug template sources, so a future successful self-update could reintroduce both bugs -- filing that separately.

---

