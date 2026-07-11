← back to [docs/timeline.md](../timeline.md)

## 2026-06-27 16:25 - Wave 4e.4 — conventions-template skill (review like me)

**Reasoning:** Catalog scaffold for the 'review like me' feature shipped via SPEC v0.5.1 + clud-bug rc.6. Template skill at skills/conventions-template/SKILL.md demonstrates the applies_to.author frontmatter field. Maintainers copy + customize into their repo's .claude/skills/conventions-<gh-login>/SKILL.md to capture their personal review conventions; the bot loads the skill ONLY on PRs they open.

**Alternatives considered:** Ship a complete worked example with concrete conventions (rather than a template with placeholder sections) — rejected: every maintainer's conventions are different; a template forces them to think about their actual rules instead of inheriting someone else's defaults

**Implications:**
- kind: rule (not voice) per the user clarification — conventions are review-content rules, not tone modifiers
- Body includes 4 placeholder sections: What I always flag / What I always ignore / Structural preferences / How I phrase findings
- README table entry added with the SPEC v0.5.1 applies_to.author reference + the .claude/skills/conventions-<gh-login>/ naming convention

---

