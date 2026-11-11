← back to [docs/timeline.md](../timeline.md)

## 2026-11-11 15:27 - The catalog calls the design-token project udts: every live mention of tokenomics is renamed

**Reasoning:** The repository the catalog called tokenomics no longer exists under that name; the project is thrillmade/udts. The stale name was not only wording. The weekly census requests an access token for a list of repositories by name, GitHub rejects the whole request when one name does not resolve, and the census failed on four consecutive scheduled runs (2026-10-19 to 2026-11-09) at that step. The owner ruled: use udts everywhere, and linking it is allowed.

**Alternatives considered:** Drop it as a subscriber and write 'the UDTS project's own repository': rejected by the owner in favour of the plain name, Keep surveying the old repository: rejected, it is dormant and its name no longer resolves in a token request

**Implications:**
- thrillmade/udts carries no skills-lock.json today, so the next census reports it as declared-but-not-observed for the seven skills whose placement lists it, until it installs them
- The census's App installation must be able to see thrillmade/udts, or the token request fails the same way
- Dated records keep the old name: decision entries, census reports, fixtures and merged ledger rows

---

