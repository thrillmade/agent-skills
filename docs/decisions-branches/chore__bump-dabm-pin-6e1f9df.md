← back to [docs/timeline.md](../timeline.md)

## 2026-06-10 11:46 - Bump dependabot-auto-merge caller pin to 6e1f9df

**Reasoning:** Picks up thrillmade/.github PR #3 which drops the major-bump early-stop step. CI gates breakage; trust the bots.

**Alternatives considered:** Stay on b208d22 and continue blocking major bumps from auto-merge — rejected, contradicts org direction 2026-06-10

**Implications:**
- Major dependabot bumps in this repo will now auto-merge on required-CI pass like patch/minor already do

---

