← back to [docs/timeline.md](../timeline.md)

## 2026-08-23 16:16 - Reconcile placement-map.json subscribers against real skills-lock.json files: add arlyn-working and arlyn-delivery, the two largest real consumers, to every skill entry their locks actually pin

**Reasoning:** docs/placement-map.json declared 8 subscribers but the census cannot see arlyn-working (23 pinned skills, committed on main) or arlyn-delivery (17 pinned skills, committed+pushed on dev) at all; every downstream fan-out (weekly census, future placement checks) was silently skipping the two largest real consumers

**Alternatives considered:** leave the map as-is and treat the 8-repo census scope as the whole picture -- rejected, the map's job is to describe reality that other tooling reads, and it was already blind to 40 real subscriptions across 23 skill entries

**Implications:**
- the 17 dispatcher/lens entries that carried 'subscribers: []' with a note saying a repo shouldn't need to subscribe directly (design-dispatchers, clud-bug#243 lens notes) now show arlyn repos subscribed anyway, because that's what their locks say -- the notes describe expected behavior, not a ceiling on it. Left census_counters.py's CONSUMER_REPOS and the App token's repositories: allowlist in skill-census.yml untouched: adding arlyn-working/arlyn-delivery there without also widening the GitHub App's repo grant would just turn into a weekly permission-error row, so that's a separate, coupled change

---

