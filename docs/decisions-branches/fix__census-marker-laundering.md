← back to [docs/timeline.md](../timeline.md)

## 2026-07-28 00:33 - Close the census marker-laundering chain at both boundaries, and stop the sync from assigning versions

**Reasoning:** census_panel.py runs weekly on main and its ingestion path is exploitable today. The issue templates auto-apply the census label at creation, so fetch_docket()'s label filter is not an allowlist -- any outsider can put text in the docket. render_docket() then quoted up to 1500 chars of that body verbatim into the model's context, and _sanitize_body() defanged @ but never stripped HTML comments. So an attacker-planted census-key marker could ride through a machine-authored issue and win a downstream head -1 extraction, invisibly, because HTML comments do not render in GitHub's UI. _neutralize_markers() now breaks the comment delimiters at both the ingestion and emission boundaries, after stripping zero-width characters that would defeat a naive match. Separately, notify-clud-bug.yml was shipping version 0.7.NaN into clud-bug's main: it parsed a version like 0.7.0-rc.26 with split('.').map(Number), so Number('0-rc') gave NaN. Version assignment is the publisher's act, not the sync's, so it is removed rather than patched.

**Alternatives considered:** Filter the attacker text more aggressively rather than neutralizing delimiters -- rejected: three prior security rounds each closed real defects and each surfaced a new class, which is evidence about the design, not the code. Breaking the delimiter removes the capability instead of enumerating its abuses. Or anchor only the consumer to the last non-blank line -- necessary but not sufficient, since it leaves the poisoned text in the model's context.

**Implications:**
- The laundering chain is closed at both ends and the order invariant holds: the sanitizer runs before the filing step appends the genuine marker, so the real marker is untouched. Known cosmetic cost, accepted deliberately rather than passed silently: an arrow in ordinary prose becomes '-- >'. This branch deliberately EXCLUDES the F3 actuator workflows -- they failed four adversarial rounds and must not reach main.

---

