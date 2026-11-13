← back to [docs/timeline.md](../timeline.md)

## 2026-11-12 03:09 - Follow-ups from making skill-smith generic: say who owns house rules, stop restating a threshold, and five clarity fixes in the agent definition

**Reasoning:** After the skill-smith agent became generic, two places still said it owns this catalog's house rules (the superseded skillforge skill's description and its placement-map note); AGENTS.md restated a line-count threshold that the decisions check owns; and the agent definition said it files changes upstream, named an eval script with no word on where it lives, offered renaming an installed skill's directory as a way to measure a baseline, and had no instruction for a catalog with no siblings or for an agent with no skill-loading tool (#306).

**Alternatives considered:** Leave the skillforge description alone because the skill is superseded: rejected, a description is the text a router reads, and it sent readers to the wrong owner. Keep the threshold number in AGENTS.md with a pointer: rejected, one owner per fact. Change the state of #273 in the same pass: not done, the literal it objects to is still true at the other tool's newest tag.

**Implications:**
- skillforge moves to 1.0.1 for a description-only change; its body is untouched and the new description is unmeasured, since no trigger eval was run. No rule in the agent definition is loosened: it still never commits, pushes, opens a pull request or edits an installed copy. What remains on #306 belongs to the logmind lane.

---

