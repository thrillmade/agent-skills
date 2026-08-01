← back to [docs/timeline.md](../timeline.md)

## 2026-07-31 23:06 - Reconcile the three toolchain skills against SPEC 2.0

**Reasoning:** An agent reads AGENTS.md, follows it to a skill, and acts on what the skill says before it ever opens an issue. All three skills that teach this toolchain were behind the contract that merged today, so that path taught the old rules. The logmind skill described docs/decisions.md, a twenty-entry cap and an archive — all deleted. clud-bug-collaboration described a green check with no certification, a fork PR going green, and told a reader how to switch strict mode off. orchestrating-agent-delegation predated the roster having a path, a schema, or an effort field, so it described dispatch as prose rather than as a file on disk.

**Alternatives considered:** File issues and let each lane update its own skill; wait until the tools ship the behaviour before updating what teaches it

**Implications:**
- The frontmatter drops review_mode from all three. Composition moved to review.passes in a repository's own config, because a subscribed skill's grouping was decided by whoever wrote it and a subscriber is forbidden to edit its copy.
- clud-bug-collaboration now tells an agent it MUST NOT change strict mode rather than how to switch it off. That setting decides whether something blocks, and SPEC 1.6 makes that class a person's to set.
- orchestrating-agent-delegation gains the rule that a brief names a role rather than restating it — if the same framing is being pasted into every dispatch, it belongs in the role file where the next agent inherits it. And that model and effort are separate knobs, with effort raised where being wrong is expensive and hard to notice.

---

## 2026-07-31 23:22 - Drop review_mode from the skill schema across the catalog, and stop validating it

**Reasoning:** Reviewing my own previous commit surfaced two defects and one omission. The commit swept in derived documents, which SPEC 3.3 forbids on a non-default branch and which would have red-lit this pull request exactly as it did protocol#75 an hour earlier — restored from main. It also carried an unrelated validator change with no mention in its message; that change is correct and is now named here. And the omission: review_mode was removed from three skills while fifteen others still carried it, which is worse than either extreme because a reader cannot tell which is right. Removed from all forty-six and dropped from the validator.

**Alternatives considered:** Leave the field on the other fifteen since unrecognised keys round-trip harmlessly; keep validating a field the contract no longer defines

**Implications:**
- How a repository groups skills into passes is review.passes in its own review config, per SPEC 2.2. A subscribed skill's grouping was decided by whoever wrote it, and 5.1 forbids a subscriber editing its copy — so the field could never be changed by the repository it governed.
- The validator's kind enum also moves from rule|voice|design to rule|writing|design, and voice_scope validation goes with it. That change had been sitting uncommitted since this morning and is recorded here rather than riding in silently.
- All 46 skills re-validated against the updated schema before commit: names match directories, slugs match the pattern, kind and source values are in range, every description present.

---

