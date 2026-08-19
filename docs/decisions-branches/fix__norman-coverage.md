← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 12:35 - Close #225: give composing-a-screen Norman's two gulfs, both in trigger surface and as a checkable verification step

**Reasoning:** The two gulfs (execution: can the next action be found; evaluation: can its result be read) were the only Norman concept in DOET with zero trigger-surface coverage across the catalog -- forcing functions, constraints and natural mapping already had at least a declared-absence mention. composing-a-screen is the prescriptive design spine with a numbered Verification section, so a 6th check (DOET rev. ed. 2013 ch. 1) fits its existing shape; empirical-design-principles explicitly scopes itself to falsifiable predictions and had already declared the gulfs out of its own scope, so covering them there would have fought the file's own stated boundary.

**Alternatives considered:** usability-heuristics already discusses the same DOET ch.1 material (affordances, signifiers, constraints, mappings, feedback, conceptual model) and would have put the gulfs beside their bridging concepts, but it had only 12 bytes of body headroom against the 8192 cap -- not enough for a real addition without a trim large enough to look like cutting content to fit the gate, which #213 was opened against.

**Implications:**
- empirical-design-principles' frontmatter and its 'When NOT to use' bullet no longer claim the gulfs are covered nowhere -- they now point at composing-a-screen, and the gulf-of-execution phrasing was dropped from its DOET citation list (ch.4 constraints/forcing-functions, ch.1/3 mapping stand alone now). The NOT_HERE_PROBES entry for 'gulf of execution' in gen_skill_directory.py was removed rather than narrowed, since coverage is now complete, not partial; forcing functions/constraints/natural mapping remain a real, undeclared-by-probe gap. Regenerated stamps, skill-versions.json and the directory body in that order, twice (gen_skill_directory.py rewrites its own file after the first stamp pass, which stales that one stamp).

---

