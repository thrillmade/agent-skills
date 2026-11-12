← back to [docs/timeline.md](../timeline.md)

## 2026-11-11 23:20 - The census survives a stale repository name, names what it could not read, and raises an alarm when it stops

**Reasoning:** The weekly census failed four scheduled runs in a row and nobody noticed: one renamed repository in the token request's list made GitHub refuse the whole request, and the census is the thing that files issues, so a census that stops files nothing (#313). A repository the token cannot see also answers 404, which the counters read as 'no lock file', so it was counted as read with zero subscriptions. Two per-verdict issue lookups still read a failed lookup as 'nothing filed' (#264).

**Alternatives considered:** Request a token for every repository the App can see: rejected, it widens what a leaked token could read. Keep the hand-kept list in the workflow and add an equality test against the script's list: rejected, a renamed repository would still stop the run. Fail the run whenever any repository is unread: rejected, one stale name would again cost the whole census. A workflow_run notifier instead of the watchdog: rejected, it cannot see a census that never started.

**Implications:**
- The token request's list is computed at run time from CONSUMER_REPOS and what the App installation can see. An empty list would widen the token to the whole installation, so it is impossible by construction and guarded a second time in the workflow. A partial census is green with warnings and a banner at the top of the digest; the run is red only when no consumer was read. A failed scheduled run files one issue under the key skill-census, and a Tuesday watchdog files into the same issue when no scheduled run has succeeded for 14 days. A failed per-verdict lookup holds that verdict back for the cycle instead of risking a duplicate. Both the census and the watchdog stop if GitHub disables scheduled workflows after 60 days without repository activity.

---

