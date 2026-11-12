← back to [docs/timeline.md](../timeline.md)

## 2026-11-12 00:43 - Two tooling fixes: the validator stops enforcing source values, and the sync pull request into clud-bug targets dev

**Reasoning:** validate_skills.py rejected any SKILL.md whose source value was outside a fixed list, citing a spec section that no longer defines the field (#261). notify-clud-bug.yml opened its sync pull request against main and cut its branch from the default branch, while every pull request in the org targets dev (#275).

**Alternatives considered:** Keep the source list as a warning: rejected, a rule with no owner reads as true until it quietly is not. Remove the leftover source line from the one skill that still carries it: rejected, it would change that skill's digest for no gain. Hash a whole skill folder in the census (#237) in the same change: backed out after review, because the lock-writing tool sorts and frames files differently from what was built, and changed its construction again in its newer lock format; that needs its own design.

**Implications:**
- An arbitrary source value now validates like any other key the validator has no rule for. The next sync pull request into clud-bug is cut from and opened against dev. #237 stays open with the measured construction of both lock formats.

---

