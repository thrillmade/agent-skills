← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 11:45 - skill-census closes prior digests when it files a new one

**Reasoning:** Weekly digest issues were superseded by construction but never closed; four sat open at once (W31-W34) and only the newest was current, training the tracker to be ignored

**Alternatives considered:** leave the backlog open and rely on humans to prune

**Implications:**
- the File issues step now closes every OTHER open census-labeled issue whose title matches the exact 'census <ISO-week> digest' format and carries no other census-scheme label, commenting a forward link to the new digest first; verdict issues (always carry a second label) are untouched, and the run stays idempotent since the current cycle's own title is excluded from the close set

---

