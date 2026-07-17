← back to [docs/timeline.md](../timeline.md)

## 2026-07-16 23:04 - integration guide + retire SKILL-UNIFICATION-SPEC.md post-execution

**Reasoning:** Every thrillmade repo needs one canonical how-to for integrating with the reservoir (new-repo setup, existing-repo adjustment, org rules, what the steward automates later) — docs/integrating-with-agent-skills.md plus a README summary section. The handoff spec is retired per CDO direction after a 6-auditor conformance run (60 requirements: 57 conform, 3 user-ruled deviations, 0 nonconformant; protocol-SPEC alignment audit clean on frontmatter + locked-rule checks).

**Alternatives considered:** Move the spec to docs/ instead of deleting (rejected: it's a handoff artifact whose surviving contracts are now owned by living docs — the README catalog legend, the integration guide, and protocol#39, which absorbed the 5 de-facto contracts by comment before deletion). Put the whole guide in README only (rejected: too long; README carries the summary + link).

**Implications:**
- All spec references re-pointed (8 stubs + 2 deprecation markers → README design-catalog section; README legend → PR #136 + decision log + protocol#39). reviewing-design-work corrected per the protocol audit: design pass fires only on design.enabled:true + PR trigger (SPEC §12.3), and lens order reframed as within-session guidance, not a cross-pass constraint (§12.2). token-frugal-tooling finally has a README row.

---

