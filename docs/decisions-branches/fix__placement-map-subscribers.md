← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 04:57 - Add skdd to the four default-on review-discipline subscriber arrays in placement-map.json

**Reasoning:** skdd's feat/skills-lock branch (PR thrillmade/skdd#32) commits a skills-lock.json whose four skill hashes match agent-skills @ 2dc8360 byte-for-byte (git blob SHA-1 and sha256 both verified), proving skdd holds critical-issues-only, evidence-based-review, respect-existing-conventions, and clud-bug-collaboration -- but the map's subscribers arrays for those four omitted it, making the map wrong about the harness it names as ground truth (issue #189)

**Alternatives considered:** Do a full reconciliation of every consumer's skills-lock.json against every skill's subscribers array -- rejected for this change: most skills carry an empty subscribers array by design (opt-in, untracked), and the GitHub issue's own ask is scoped to these four default-on entries; a broader sweep belongs to its own issue with its own evidence

**Implications:**
- The map still doesn't track opt-in installs (e.g. arlyn-working's 23 installed skills, tokenomics' non-default-on installs) -- those remain unreconciled and are not claimed fixed here

---

