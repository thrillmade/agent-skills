← back to [docs/timeline.md](../timeline.md)

## 2026-08-23 16:14 - Replace the marketing-genre carve-out with the system-exists test, and make design-system-consistency's re-implementation rule cover the substrate gap

**Reasoning:** Issue #252: five skills (web-interface-guidelines-review, spacing-system, component-sizing-principles, line-height-grid, oklch-color-space) stood down on surface genre ('marketing') when the real test is whether a token layer exists on disk -- a marketing page built inside a token-driven system is in the system, and a studio whose whole deliverable is marketing pages was getting five skills standing down at once. design-system-consistency already had the correct test ('No system on disk'); ported it to each skill's own voice. Separately, design-system-consistency rule 6 only flagged a hand-rolled control 'where a system component exists', missing the substrate-disciplined case where the violation stands even when the system lacks the part -- amended rule 6 to cover both branches (propose upstream, don't hand-roll, regardless of whether the part exists yet).

**Alternatives considered:** Add a new skill for the substrate rule instead of amending design-system-consistency -- rejected per the issue's own instruction: it already owns the adjacent rule., Move the carve-out fixes to references/ subdirectories for more room -- rejected: references/ is blocked pending clud-bug#305 and unread by the CI reviewer anyway.

**Implications:**
- web-interface-guidelines-review now has 18 bytes of headroom against the 8192-byte body cap, and design-system-consistency has 3 -- any future edit to either file needs to cut before it adds.
- The shared phrase 'No token layer on disk' now opens the carve-out bullet in all six design skills that gate on system existence, which is worth keeping consistent if any of them changes wording again.

---

