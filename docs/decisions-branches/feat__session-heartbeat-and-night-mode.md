← back to [docs/timeline.md](../timeline.md)

## 2026-08-14 17:31 - Add session-heartbeat and night-mode as two separate skills — mechanism and policy have different trigger surfaces

**Reasoning:** A skill's description decides when it loads. Heartbeat applies to any long autonomous run; night-mode only after a human explicitly hands over unattended operation. Fusing them makes both load at the wrong times, so night-mode references heartbeat as REQUIRED BACKGROUND instead of restating it.

**Alternatives considered:** One skill with a night-mode section (agent-skills#174's fallback) — rejected: one description cannot carry two distinct triggers, Fold both into orchestrating-agent-delegation — rejected: it is grandfathered at its exact byte cap (10150), so it cannot grow

**Implications:**
- orchestrating-agent-delegation has zero headroom, so the reciprocal back-link needs a compensating cut and is left as a maintainer call
- Thresholds are derived (largest-dispatch headroom) rather than copied as a flat 90%, and the cache-TTL numbers are traceable to Anthropic's prompt-caching docs

---

