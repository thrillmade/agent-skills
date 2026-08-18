← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 09:09 - Fix clud-bug self-update: make version compare semver-aware, stop attempting downgrades

**Reasoning:** Scheduled workflow failed weekly since 2026-08-10 (last success 2026-08-03). Root cause: the compare step used a plain `!=` between installed and npm's latest dist-tag. This repo's installed version (0.7.0-rc.20) is a 0.7.x prerelease that outranks npm's latest tag (0.6.34, an older release line); the naive check misread that as an available update, generated a downgrade PR (#187), which the CEO explicitly closed as a downgrade. Every week since, the workflow re-tried the same downgrade, regenerated the same deterministic branch name (clud-bug/self-update-0.6.34), and collided with the closed PR's undeleted remote branch, failing the git push outright.

**Alternatives considered:** Delete the stale remote branch instead: would silence the immediate push failure but leaves the workflow attempting the same rejected downgrade weekly, filing a fresh failure-issue comment every time push happens to collide again, or worse, actually landing a downgrade PR once the branch collision itself is gone. Fixing only the symptom, not the class of bug (direction-blind version compare).

**Implications:**
- The naive compare lives in clud-bug's self-update workflow template upstream (thrillmade/clud-bug) and this exact template is what `npx clud-bug@X update` re-renders into this file on every real release; a future genuine self-update PR that merges will overwrite this local fix with the naive check again. This is a local mitigation, not a permanent one — the same class of bug should be reported/fixed in the upstream clud-bug template so it survives the next regen. The stale remote branch clud-bug/self-update-0.6.34 is now inert (future runs skip before reaching it) but was left un-deleted since this task has no push access from its worktree; it's harmless to leave, or can be deleted by whoever has push access.

---

