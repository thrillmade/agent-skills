← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 04:51 - Document the fourth handoff posture: a subscribed repo that leaves the org

**Reasoning:** arlyn-delivery leaves the org 20 Aug; docs/integrating-with-agent-skills.md documented Subscribed/Published/Local but no posture covers a repo that was subscribed and becomes a frozen copy outside org reach (#215)

**Alternatives considered:** leave it undocumented and let each departing repo improvise; the guide's 'Questions this guide will absorb answers to' section already exists for exactly this kind of gap, so silence wasn't chosen deliberately, just not yet written

**Implications:**
- departing repos now have a named posture to point to, know skills-lock.json stays committed as provenance not a live pointer, and know they can self-verify currency via stdlib hashlib + curl against the public repo even with zero org access; open questions from #215 (hash vs version pin, tag/release concept, the three under-length stub skills, design-principles scope) are explicitly out of scope for this doc-only fix and remain for the maintainer

---

