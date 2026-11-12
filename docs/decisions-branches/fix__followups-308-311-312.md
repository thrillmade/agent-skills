← back to [docs/timeline.md](../timeline.md)

## 2026-11-11 23:01 - Three follow-ups: the ungated-row count is computed from the rows, a lock sourced under the catalog's former name stays drift-checkable, and the decision-artifacts description describes the page its body describes

**Reasoning:** history_rows_ungated was rows minus live skills, which undercounts whenever a live skill has no row for its current digest and went negative on a small catalog (#308). The rename made CATALOG_SOURCE the new name, so every subscriber lock written before it was dropped from the drift check as a foreign catalog and the census would have reported nothing to check. The description of making-decision-artifacts still described the row-table moves page its body replaced (#311).

**Alternatives considered:** Clamp the count at zero: rejected, a clamp reports 0 where the true number is positive. Rewrite subscribers' locks to the new name: rejected, the old name redirects for good and the locks live in other repositories. Make the prose gate demand an exact word count (#312): rejected, the count is documented as a floor and the reported under-count pass was a stale-base measurement.

**Implications:**
- The committed index's ungated count moves from 182 to 192: regeneration added nine rows the last squash merge left out, which the corrected count absorbs (182 was already nine short), and the restamped skill's new version has no row until it merges. The catalog's former name is a permanent alias in census_counters.py. The trigger-description eval asked for in #311 was not run, so the new description is unmeasured: the harness is skill-creator's, which lives outside this repo. #311 stays open for it.

---

