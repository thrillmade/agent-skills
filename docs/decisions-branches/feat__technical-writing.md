← back to [docs/timeline.md](../timeline.md)

## 2026-08-24 16:14 - Add technical-writing skill: doc/changelog gate for additions (agent-skills#137)

**Reasoning:** check-doc-links.yml proves links resolve and check-prose-retention.yml stops prose disappearing, but neither asks whether a new env var, CLI flag or export has a matching doc/changelog line -- the clud-bug seed (CLUD_BUG_NOTARY_URL, --bundle) and this repo's own bd1b554/8f7fdbb F2 pass are two independent occurrences of exactly that gap

**Alternatives considered:** Fold this into retiring-a-superseded-decision, Fold this into api-contract-enforcement

**Implications:**
- kind: writing, so per SPEC 2.2 it must not solo-cite a code-behavior finding -- pairs with api-contract-enforcement when a finding also touches behavior

---

