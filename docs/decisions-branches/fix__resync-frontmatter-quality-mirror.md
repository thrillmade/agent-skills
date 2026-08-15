← back to [docs/timeline.md](../timeline.md)

## 2026-08-15 07:55 - Resync the skill-frontmatter-quality mirror, and record that clud-bug-collaboration's divergence is by design

**Reasoning:** The copy at .claude/skills/skill-frontmatter-quality/SKILL.md had drifted from its catalog source in three places. Two were cosmetic — a description mentioning review_mode and a review_mode: dedicated field, both referring to a schema key this repo deliberately removed. The third was not: rule 6 had been REPLACED. The catalog teaches that a kind value must match what the skill judges, which SPEC 2.2 makes load-bearing because only a rule skill may be the sole citation for a finding about code behaviour. The mirror taught a review_mode presence check instead. So the copy did not merely carry a stale field, it omitted a live rule and substituted a retired one. Resynced byte-for-byte from the catalog rather than hand-patched, so the two cannot disagree about anything.

**Alternatives considered:** Delete the mirror instead of resyncing, since it is absent from .clud-bug.json's installed array and the resolved review plan names only four skills; hand-patch the three differences

**Implications:**
- clud-bug-collaboration also differs between catalog and mirror, by 224 lines, and that one is NOT drift. The mirror is 5,538 bytes, the catalog 8,719, and the catalog before #206 was 11,510 — so the mirror is neither the current nor the previous catalog version. It is clud-bug's own leaner baseline, which that project ships and owns; notify-clud-bug.yml exists to tell them when ours changes. Two artifacts sharing a name, not one that drifted
- That kills byte-identity as the rule for the planned mirror-integrity gate. A gate requiring identical bytes would be permanently red on clud-bug-collaboration, which is a legitimate state. The gate must scope to non-baseline mirrors, or compare only against skills whose authoring home is the catalog
- skill-frontmatter-quality is a mirror with a catalog counterpart that is absent from .clud-bug.json's installed array, and the resolved review plan names four skills without it. So it was not actively teaching reviewers the wrong rule — it was dead weight that looked like it was. The gate should flag an undeclared mirror for that reason

---

