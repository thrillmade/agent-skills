← back to [docs/timeline.md](../timeline.md)

## 2026-07-25 15:42 - F2 docs truth pass: correct the sRGB doctrine, repair the dead catalog→clud-bug sync, make the census comment instead of re-filing, and reconcile four skills against current source

**Reasoning:** Three load-bearing docs described behavior that does not exist: notify-clud-bug.yml sed'd lib/skills.js (deleted in clud-bug's v0.7.0 TS migration, so the advertised auto-sync hard-failed on every run), the onboarding guide opened with npx skdd init (skdd has no implementation), and chroma-harmonization + oklch-color-space taught an sRGB-default that agent-skills#170's locked ruling bans from computation. The census had also re-filed identical verdicts for three consecutive cycles because nothing gave a verdict a stable identity.

**Alternatives considered:** Re-pull each skill from its authoring home instead of reconciling. Rejected after verification: the catalog logmind skill's 'retired' surfaces (skill audit, skill suggest, LOGMIND_QUIET, the merge driver) are all live on origin/main — a re-pull would have deleted four working surfaces to remove one dead one (skill bench, which turned out to still be live too). Also rejected: trimming skills/logmind/SKILL.md to a 250-line budget that nothing in CI enforces.

**Implications:**
- The catalog→clud-bug sync now targets src/cli/skills.ts and fails loudly on a path-miss rather than silently. Census verdicts carry a stable census-key and comment on the live issue instead of duplicating it — the search must be in:body,comments, since the four canonical seeds carry their marker in a comment. Three review rounds were needed: builders introduced two HIGH defects the adversarial pass caught, and the fix round introduced a third (skill push listed under a blanket 'never auto-PR' claim while skill_push.go opens a real PR with no confirmation). Five facts in the original brief were false and the builders refused all five; two came from reading a stale local branch. skills/logmind/SKILL.md is deliberately left at 267 lines against a catalog median of 81 — splitting it is a catalog decision for the census, not a trim.

---

