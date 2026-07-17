← back to [docs/timeline.md](../timeline.md)

## 2026-07-17 00:21 - deps: bump actions/checkout 6→7 and actions/setup-node 6→7 across workflows

**Reasoning:** Dependabot proposed both bumps separately (#127, #134); #150 recreates them as one PR so CI churns once. Both are major-version Action bumps with no workflow-input changes needed here.

**Alternatives considered:** Merge the two dependabot PRs individually (rejected: two CI cycles + two review passes for one logical change). Use the [skip-logmind] title override instead of a decision entry (attempted — the template-v2 override is broken, see logmind#212; this entry is the compliant path).

**Implications:**
- Dependabot will auto-close #127/#134 once main carries the bumps (or they get closed as superseded). check-decisions passes on decision-entry grounds rather than the broken title override.

---

