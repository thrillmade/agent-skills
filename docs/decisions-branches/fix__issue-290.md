← back to [docs/timeline.md](../timeline.md)

## 2026-11-02 22:14 - Version history admits only published rows; the check gets two tiers

**Reasoning:** A squash merge discards branch commits, so rows written on branches cited ghosts (91 on dev); review proved the prune could eat a shared-digest published row and the check could red innocent PRs, so admission now requires a publishing-ref carrier (origin/dev + origin/main, one definition in published_reachable) and --check fails only never-published digests, warning on repairable stale pointers

**Alternatives considered:** Hard ancestry check against the PR head: rejected, it reds every PR that branched before an unrelated merge; exemption list for the 28 unrepairable rows: rejected, unpublished rows are artifacts not history, so they are pruned

**Implications:**
- Branch regens record no in-flight rows, so squash orphans cannot enter the file again; a post-merge auto-regen becomes freshness, not correctness, and is filed as a follow-up

---

