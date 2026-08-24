← back to [docs/timeline.md](../timeline.md)

## 2026-08-24 14:42 - The logmind skill taught agents a route the binary now refuses

**Reasoning:** Reported by the logmind lane and verified against our own dev before acting. Three defects in skills/logmind/SKILL.md, all of which an agent reads and acts on. (1) It listed git.enforce_commits:false as an escape hatch beside [skip-logmind] and LOGMIND_ALLOW_GIT_COMMIT=1 -- but as of logmind#346 the binary REFUSES an agent that asks for it, per SPEC 1.6. So the skill taught the one route that is now blocked, and named no alternative. (2) It said logmind warp 'Never stages or commits'. warp.go says it DELIBERATELY STAGES, and the staging is the point -- it is why a plain git commit then works. (3) The remedy line gave 'git checkout origin/main -- docs/timeline.md docs/file-structure.md', which restores the moving TIP where 3.3 requires the merge-base, and omits docs/timeline-archive.md entirely. Found while fixing: the gate paragraph said a diff touching 'either derived doc' when the paragraph above it names THREE.

**Alternatives considered:** File it back to logmind and wait. Rejected: this is our copy in our catalog, it is what agents actually read, and a skill that teaches a blocked route is worse than one that says nothing. Cut a whole section to make room. Rejected: every section here is load-bearing; the bytes came from compressing my own new prose and one genuine restatement instead.

**Implications:**
- 8193 bytes at one point -- ONE over the 8192 cap. The bytes were earned rather than shaved off meaning: the removed clause ('branch edits cause exactly the cross-PR conflicts this design eliminates') restates the section heading and its opening paragraph, and 'straight from source' lost one word. I briefly dropped a full stop to buy a byte and put it back -- buying a byte with bad grammar is not a trade. Final headroom 8 bytes, which makes this skill among the tightest in the catalog and worth watching. The warp caveat now also carries logmind#362's finding: commit what warp staged, because git commit -a sweeps in the unstaged tip copies and CI rejects it.

---

