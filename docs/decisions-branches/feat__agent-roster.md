← back to [docs/timeline.md](../timeline.md)

## 2026-09-15 14:56 - Implement protocol SPEC §2.4/§5.1's agent roster: 15 roles from ~/.claude/agents into .claude/agents/, an agents/ namespace in the placement map, and a validate_agents.py gate

**Reasoning:** SPEC §2.4 defines a role as a versioned file at .claude/agents/<name>.md and §5.1 puts it on the same distribution path as a skill, but 15 real definitions existed ungoverned on one laptop -- same risk class agent-skills#180 named for the studio skills, same fix: bring them under the catalog and its gate.

**Alternatives considered:** Extend validate_skills.py's per-skill loop to also validate .claude/agents/*.md, Stamp version/digest/origin on roles the way skills carry them, Mark every new role distribution: default-on

**Implications:**
- validate_skills.py needed a minimal, surgical carve-out (AGENTS_PREFIX) so an agents/-namespaced placement-map key stops being rejected by the skills/-dirs 1:1 reconcile and the family/owns requirement -- the exact blocker #180's own comments name and reproduce
- Roles have no version/digest/origin stamp: SPEC §2.4's own frontmatter table lists exactly 7 fields, none of them identity stamps, so a consumer's staleness signal is the subscriber's own skills-lock.json content hash (SPEC §5.2) once the harness exists, not an in-file field invented ahead of ratification
- Every new role is distribution: catalog-only, matching SPEC §5.1's own "agents/simplifier" example verbatim -- nothing seeds default-on until skdd's installer (skdd#6) exists to seed it, and skill-smith specifically is excluded from default-on by SPEC §5.2's own carve-out ("a role that maintains this toolchain itself")

---

## 2026-09-15 18:26 - Pin the agents/-namespace dead-family escape a panel found in PR #276, plus its own mutation self-test and a control-tested crash guard in validate_agents.py

**Reasoning:** The AGENTS_PREFIX carve-out was applied to map_names but not to the used-family set feeding the dead-family check, so an agents/ entry carrying a family key counted as live use and hid a family declared by no real skill -- the fix landed but the regression test it was demonstrated with was never committed. Running the full suite to confirm also surfaced a mutation-harness entry (test_skill_directory_mutations.py) whose exact-match string broke when the fix reshaped the used comprehension across three lines, and a panel-flagged crash (IsADirectoryError from validate_agents.py's read_bytes() with no is_file() guard, pre-existing and identical to validate_skills.py:712) cheap enough to close in the one file I was permitted to touch

**Alternatives considered:** Left the mutation harness broken and reported it instead of fixing it -- rejected: it is in tests/, which this lane owns, and a broken self-test that nobody notices for a cycle is a worse outcome than a two-line correction with its reasoning attached. Adding a matching mutation-harness row for the agents/-prefix filter itself -- rejected for now: this harness's SUITES list does not include test_validate_skills_agents_namespace.py, so wiring it in is a wider change than this fix should carry; filed as a finding instead

**Implications:**
- The dead-family check is now proven to fail on the exact escape a panel found (red before green, mutation landed by grep, reverted and confirmed clean); validate_agents.py can no longer be crashed by a directory named *.md under .claude/agents/; and the full suite (1291 passed, 1 skipped) is green again after the harness fix, so 'pytest tests/ -q' stays true as a gate rather than something that silently stopped proving what it claims to

---

