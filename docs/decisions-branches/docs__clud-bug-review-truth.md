← back to [docs/timeline.md](../timeline.md)

## 2026-11-03 17:57 - AGENTS.md: replace the frozen clud-bug outage claim with the measured three-era history

**Reasoning:** The frozen claim said every PR since 188 concludes neutral-unavailable; measured 2026-11-03 it is false twice over: 274 and 277 concluded success (notarized), and 293-296 carry no check-run at all because the App stopped posting after the 117 workflow removal

**Alternatives considered:** Deleting the section entirely — rejected: the live-check command and the control-test discipline are the durable part; only the frozen measurement rotted

**Implications:**
- While the check is absent the per-change review gate is carried entirely by local panels, now said explicitly

---

