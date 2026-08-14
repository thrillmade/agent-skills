← back to [docs/timeline.md](../timeline.md)

## 2026-08-14 16:47 - Gate skill size with a shrink-only ratchet, and deprecate skillforge into the three skills that own its job

**Reasoning:** A consuming project installed 23 skills this week and found the catalog had no size discipline at all. The gate: a skill absent from skills/skill-size-budget.json must have a body at or under the limit; one listed there may shrink but never grow; once back under budget its entry MUST be deleted; entries are never added. That makes the budget file a shrinking list rather than a permanent excuse. All three paths were mutation-tested and proven to fire, with a clean tree before and after each — a check that has never failed is not proven. skillforge is deprecated rather than deleted: a SUPERSEDED notice on the description with the body kept, following the design-token-naming precedent, because three skills now own its job better — skill-creator owns measurement, superpowers:writing-skills owns wording form, and skill-smith owns house rules. Its one sharper heuristic, forge when you have done the same sequence two or three times, migrated rather than being lost.

**Alternatives considered:** Set a hard cap with no grandfather list, which fails 4 of 46 skills on arrival at the chosen 8192 and would have failed 20 of 20 house-structured skills at the 4000 first attempted, either way teaching everyone to bypass the gate; delete skillforge outright, which would strand its inbound references

**Implications:**
- The limit is 8192, not 4000. The first version used 4000, which is a clud-bug TEMPLATE override rather than the library value — verified at clud-bug src/core/prompt-builder.ts:55, DEFAULT_MAX_SKILL_BYTES = 8192, citing SPEC section 1.10. At 4000 every skill carrying the full house structure was over budget, 20 of 20, which is the convention fighting the gate rather than the skills being wrong. At 8192 the grandfather list is 4. Verify which layer a constant comes from before building a gate on it
- The budget file initially told authors to move detail into references/ because those load on demand. That is false for clud-bug: references/ returns zero hits across its src/ and templates/, and its CI reads SKILL.md and nothing else — control-tested, the same grep for SKILL.md returns three files. A policy file must not assert a remedy that does not work for the consumer the policy exists to serve
- skillforge's metadata.spec pointing at agentskills.io is legitimate and not the reason for deprecation — Anthropic's own spec repo now points there. It was retired for duplication, not provenance

---

