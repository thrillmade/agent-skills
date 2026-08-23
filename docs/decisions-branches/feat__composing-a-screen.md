← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 02:04 - Add composing-a-screen: the prescriptive spine the design catalog never had

**Reasoning:** Measured coverage against the seven basics a free Figma resource page covers: contrast 12 skills, accessibility 12, consistency 3, hierarchy 1, alignment 1, proximity 0, progressive disclosure 0 (control: zorkmid 0, design 24). The catalog grew out of design-critic needing citable lenses, so depth accumulated exactly where a finding can be argued numerically and nowhere near where design judgement lives. Every design skill was review-framed; nothing told an agent how to compose a screen. The CEO's test was that a ten-second Google search covered our four zeros.

**Alternatives considered:** Extend designing-elite-ui, or grow empirical-design-principles into the spine. Rejected: the first is the visual bar and this is structure, and the second explicitly scopes itself to falsifiable prediction and disclaims usability heuristics including progressive disclosure. A third option, doing nothing on the grounds that the depth already exists, fails because depth an agent cannot route to is not coverage.

**Implications:**
- L1 and opt-in, diverging from the other three dispatchers' catalog-only: catalog-only makes a subscribing repo raise a placement verdict, which would make this skill un-installable by the repos it is written for. Deliberately absent from census_counters STRUCTURAL_L0, so zero subscriptions reads as a real gap rather than by-design. A refute-first panel caught three defects that would have shipped guidance making screens worse: Fitts stated backwards, a hierarchy rule forbidding redundant coding, and a proximity metric that scored an inverted layout as ideal. The skill's own severability grep then caught that the body contained zero instances of 'progressive disclosure' — it would have scored 0 on the very census query that established the gap, the same defect PR #233 has. Body 8097 bytes, 95 headroom. Whether an agent actually designs better with it is untested and stated as a hypothesis, not a result; the behavioural diff has not been run.

---

