← back to [docs/timeline.md](../timeline.md)

## 2026-07-17 20:15 - skill engine W1: drift detection, placement-map ground truth, §1.10.1 validator, six-kind taxonomy

**Reasoning:** The engine detected-and-filed but had no live-connection verify, an under-enforcing validator, no committed placement ground truth, and a rubric whose verdict-kinds block contradicted its own panel. W1 lands: subscription drift detection in census_counters (source-scoped to this catalog, per-skill lineage proof required before any drift assertion — the lock hash algorithm proved EXTERNAL after ~40 candidates x full git history matched nothing, so status stays honestly indeterminate until skills.sh's normalization is mirrored); docs/placement-map.json (46 skills, authoring-home/distribution/subscribers) with a real CI gate; validate-skills enforcing the §1.10.1 enums + shapes with unknown-key tolerance; usage[] read wired (no consumer emits it yet); six-kind taxonomy reconciled with the label mapping stated.

**Alternatives considered:** Assert drift on plain sha256 mismatch (rejected: proven false-drift on EOL/foreign-catalog/unproven-algo cases — never report drift you cannot prove). '.'-prefix requirement on applies_to.extensions (rejected: my own brief error — clud-bug suffix-matches; test-discipline's _test.py entries are deliberate).

**Implications:**
- Flipping CATALOG_HASH_ALGO alone can no longer mis-flag (lineage-proof gate). The placement map is signal-1 ground truth the census cross-checks; divergence files placement verdicts. W2 (process-verdict actuator + notify-subscribers fan-out) builds on these seams. census_panel should read the three new signal keys — noted for W2.

---

