← back to [docs/timeline.md](../timeline.md)

## 2026-11-03 13:51 - Unblock the dev→main promotion: declare the five batch-level prose nets; true the required-check headers

**Reasoning:** The promotion PR's prose gate compares against main's August tip, where cross-PR masking surfaces five undeclared nets the per-PR runs could not see; and both workflow headers still claim no check is required, which the org CI-must-pass ruleset made false

**Alternatives considered:** Bypass-merge the promotion past the red gate, or loosen the gate to net-only scoring — both discard exactly the honesty the ledger exists for

**Implications:**
- PR #294 goes green once this lands on dev; the headers carry the measured ruleset state and name each other for the next re-measurement

---

