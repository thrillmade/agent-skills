← back to [docs/timeline.md](../timeline.md)

## 2026-11-13 11:23 - Census: catalog-only skills are graced, the digest says what the model review did, a failure that needs a person fails the run, and nothing the SDK emits reaches the public log (#191)

**Reasoning:** The model-review step failed authentication on every weekly run for weeks while the run stayed green and the digest said nothing. A process cannot police everything written to its own streams (the SDK's logging, warnings, finalisers, asyncio's reporter, output at import), so the boundary is the workflow step: the script's stdout and stderr go to /dev/null, the runner's file-command variables are removed from its environment, and only panel_status.json crosses. Every step that prints or uploads from that record first runs panel_record.sh, which checks each field against a closed vocabulary and prints only words from that vocabulary. The guarantee is against an honest or buggy dependency. A deliberately malicious one holds the API key and can open a network connection, so nothing in this workflow can contain it; that threat is answered by pinning the install by hash, which is a separate change.

**Alternatives considered:** Sanitise exception text inside the Python process. Tried for four review rounds; each round found another channel (output at import, a finaliser, the logging module, asyncio)., Fail the run on every model-review failure. A provider timeout, rate limit or 5xx passes by itself and would page a person for nothing., Keep catalog-only skills in the coverage-gap list. They reappeared every week with nothing to act on (#191).

**Implications:**
- Green only for: ran, off (no key), held back (partial census), timeout, connection error, 429, 5xx, an unusable answer, and a background error in a run that completed (with a warning). Red for any other HTTP 4xx, an unlisted exception class, a blank key, a missing SDK package, a non-zero exit, and a missing, non-regular or malformed record. When the guard step finds no key at all, the model-review step and the health step are skipped and no record is written.
- The digest and artifacts are written before the red exit, so a failed run still files its digest.
- A scheduled census that succeeds closes every open alarm issue it filed.
- A catalog-only skill is listed under grace with its reason and is no longer a coverage gap.
- Not in this change: pinning the SDK install by hash.

---

