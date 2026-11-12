← back to [docs/timeline.md](../timeline.md)

## 2026-11-11 23:20 - The census survives a stale repository name, names what it could not read, and raises an alarm when it stops

**Reasoning:** The weekly census failed four scheduled runs in a row and nobody noticed: one renamed repository in the token request's list made GitHub refuse the whole request, and the census is the thing that files issues, so a census that stops files nothing (#313). A repository the token cannot see also answers 404, which the counters read as 'no lock file', so it was counted as read with zero subscriptions. Two per-verdict issue lookups still read a failed lookup as 'nothing filed' (#264).

**Alternatives considered:** Request a token for every repository the App can see: rejected, it widens what a leaked token could read. Keep the hand-kept list in the workflow and add an equality test against the script's list: rejected, a renamed repository would still stop the run. Fail the run whenever any repository is unread: rejected, one stale name would again cost the whole census. A workflow_run notifier instead of the watchdog: rejected, it cannot see a census that never started.

**Implications:**
- The token request's list is computed at run time from CONSUMER_REPOS and what the App installation can see. An empty list would widen the token to the whole installation, so it is impossible by construction and guarded a second time in the workflow. A partial census is green with warnings and a banner at the top of the digest; the run is red only when no consumer was read. A failed scheduled run files one issue under the key skill-census, and a Tuesday watchdog files into the same issue when no scheduled run has succeeded for 14 days. A failed per-verdict lookup holds that verdict back for the cycle instead of risking a duplicate. Both the census and the watchdog stop if GitHub disables scheduled workflows after 60 days without repository activity.

---

## 2026-11-11 23:44 - Review round on the census change: the alarm cannot be captured, the token fails closed, and a partial census reports nothing about repositories it did not read

**Reasoning:** An independent review found that a stranger's comment carrying the alarm's marker on another bot-filed issue would capture both alarms; that the guard on the token step stopped only a literally empty list, while the pinned action reads whitespace or a lone separator as every repository; and that an unread repository's missing data still surfaced as coverage gaps and missing subscriptions, which the panel could turn into filed verdicts.

**Alternatives considered:** Keep searching comments for the marker and filter harder: rejected, the genuine marker is only ever in the issue body. Keep the owner input on the token step and validate the list in bash: rejected, without that input the action itself falls back to this repository alone. Run the panel on a partial census with a caveat in its prompt: rejected, a verdict about data nobody read would still be filed in public.

**Implications:**
- The alarm issue is matched by bot author, exact title and the marker in the body. The script tries to revoke the lookup token as soon as the listing is done (best effort: if that request fails the token lives until it expires, up to an hour), and the action's end-of-job revoke is skipped for it, because it would run after the third-party install it is meant to protect against and would warn on every healthy run. Every name this catalog has had is listed in CATALOG_NAMES, and a test fails in CI while the repository's current name is missing from it, so the next rename cannot forget it. On a partial census the panel does not run and the digest is filed alone; its placement section names the repositories whose declarations were not checked instead of printing an all-clear. A skill whose only subscriber was not read can still appear under the coverage-gap heading, which says the census is partial.

---

