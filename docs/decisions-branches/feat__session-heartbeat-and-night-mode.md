← back to [docs/timeline.md](../timeline.md)

## 2026-08-14 17:31 - Add session-heartbeat and night-mode as two separate skills — mechanism and policy have different trigger surfaces

**Reasoning:** A skill's description decides when it loads. Heartbeat applies to any long autonomous run; night-mode only after a human explicitly hands over unattended operation. Fusing them makes both load at the wrong times, so night-mode references heartbeat as REQUIRED BACKGROUND instead of restating it.

**Alternatives considered:** One skill with a night-mode section (agent-skills#174's fallback) — rejected: one description cannot carry two distinct triggers, Fold both into orchestrating-agent-delegation — rejected: it is grandfathered at its exact byte cap (10150), so it cannot grow

**Implications:**
- orchestrating-agent-delegation has zero headroom, so the reciprocal back-link needs a compensating cut and is left as a maintainer call
- Thresholds are derived (largest-dispatch headroom) rather than copied as a flat 90%, and the cache-TTL numbers are traceable to Anthropic's prompt-caching docs

---

## 2026-08-14 17:32 - night-mode verification asks the remote, not local refs — the local-ref check silently lies in a shallow/single-branch clone

**Reasoning:** Control-testing the shipped command showed git log --branches --not --remotes still listing a commit that had just been pushed, because gh repo clone --depth implies --single-branch and the remote-tracking ref was never created. git ls-remote --heads origin control-tested cleanly in both directions.

**Alternatives considered:** Keep the local-ref command with a caveat — rejected: a verification step that can report a false 'nothing was pushed' is worse than none in an unattended window

**Implications:**
- The failure is now encoded in the skill itself, not just fixed

---

## 2026-08-14 17:40 - Rename night-mode to unattended-operation — the mode's own rule is that the clock never starts it

**Reasoning:** CEO ruling on the open question filed in PR #207. #174 states the mode is 'never inferred from time of day', so naming it after the night contradicts its own trigger condition. It also pairs correctly with the sibling (session-heartbeat = mechanism, unattended-operation = policy) and removes the collision with dark-mode / UI night themes in a catalog that also holds designing-elite-ui.

**Alternatives considered:** Keep night-mode with a description-level disclaimer — rejected: a name that contradicts the skill's own trigger rule keeps costing attention on every read, Rename the branch to match — rejected: the PR head ref cannot change without opening a new PR, so the branch and its derived decision filename keep the old slug

**Implications:**
- Prior decision entries are left intact as the historical record; this entry supersedes rather than rewrites them
- The 10150 figure in the first entry is BODY bytes as validate-skills.yml measures them, not whole-file bytes (11311 = 1161 frontmatter + 10150 body) — headroom on orchestrating-agent-delegation is genuinely zero

---

