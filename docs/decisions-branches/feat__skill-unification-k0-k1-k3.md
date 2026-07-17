← back to [docs/timeline.md](../timeline.md)

## 2026-07-16 22:44 - skill unification: three-layer design catalog — K0 splits/stubs/promotions, K1 dispatchers, K3 abstraction

**Reasoning:** SKILL-UNIFICATION-SPEC.md (CDO-locked) makes agent-skills the canonical reservoir; L0 skills were teaching UDTS opinions as universal principles, no entry point told agents which skills fit which task, and the elite-UI worked example was Burning-Man-specific. Split the mixed skills (token-naming-conventions, component-sizing-principles extracted; spacing-system, dtcg-format, semver-design-tokens, type-scale, web-interface-guidelines-review cleaned in place), stubbed 8 udts-* L2 parity markers, promoted the 4 clud-bug design-critic lenses + orchestrating-elite-agent-qa, authored the 3 L1 dispatchers, abstracted designing-elite-ui to an admin-dashboard example, and seeded docs/skill-census/ with the first org census.

**Alternatives considered:** Author full udts-* L2 content now (rejected: tokenomics Phase R is rewriting the tier model — content would be stale on arrival; stubs stay model-agnostic). Rename cleaned skills to new slugs (rejected: a rename is a major per semver-design-tokens' own policy — slug churn punishes consumers for zero content win).

**Implications:**
- design-token-naming and component-sizing carry SUPERSEDED markers until tokenomics K2 lands their successors, then get deleted. clud-bug integration mechanism + design-4 authoring home decided via coordination issue. The two promoted templates needed strict-YAML description fixes — clud-bug's bundled copies would fail any strict parser (flagged upstream). Census reports in docs/skill-census/ seed the weekly editorial cycle.

---

