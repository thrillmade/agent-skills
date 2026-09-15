← back to [docs/timeline.md](../timeline.md)

## 2026-09-15 14:56 - Implement protocol SPEC §2.4/§5.1's agent roster: 15 roles from ~/.claude/agents into .claude/agents/, an agents/ namespace in the placement map, and a validate_agents.py gate

**Reasoning:** SPEC §2.4 defines a role as a versioned file at .claude/agents/<name>.md and §5.1 puts it on the same distribution path as a skill, but 15 real definitions existed ungoverned on one laptop -- same risk class agent-skills#180 named for the studio skills, same fix: bring them under the catalog and its gate.

**Alternatives considered:** Extend validate_skills.py's per-skill loop to also validate .claude/agents/*.md, Stamp version/digest/origin on roles the way skills carry them, Mark every new role distribution: default-on

**Implications:**
- validate_skills.py needed a minimal, surgical carve-out (AGENTS_PREFIX) so an agents/-namespaced placement-map key stops being rejected by the skills/-dirs 1:1 reconcile and the family/owns requirement -- the exact blocker #180's own comments name and reproduce
- Roles have no version/digest/origin stamp: SPEC §2.4's own frontmatter table lists exactly 7 fields, none of them identity stamps, so a consumer's staleness signal is the subscriber's own skills-lock.json content hash (SPEC §5.2) once the harness exists, not an in-file field invented ahead of ratification
- Every new role is distribution: catalog-only, matching SPEC §5.1's own "agents/simplifier" example verbatim -- nothing seeds default-on until skdd's installer (skdd#6) exists to seed it, and skill-smith specifically is excluded from default-on by SPEC §5.2's own carve-out ("a role that maintains this toolchain itself")

---

