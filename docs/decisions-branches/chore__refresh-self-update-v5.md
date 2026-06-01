## 2026-06-01 19:26 - chore: refresh logmind-self-update.yml to v5 (bootstrap PAT-based workflow push)

**Reasoning:** v0.6.11 self-update template uses LOGMIND_AUTO_REGEN_PAT for workflow-file pushes. `logmind agents update --apply` only does pin bumps; the v5 marker bump requires full `logmind init` refresh — caught by clud-bug-review on tokenomics PR #52.

**Implications:**
- Next auto-propagation cycle on this repo can finally work cleanly for workflow-file refreshes (assuming LOGMIND_AUTO_REGEN_PAT secret is configured).

---
