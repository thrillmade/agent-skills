← back to [docs/timeline.md](../timeline.md)

## 2026-08-17 17:46 - Per-skill content versioning: a stamp a subscriber can recompute, an index they can look it up in

**Reasoning:** npx skills add copies SKILL.md wholesale and records a computedHash from the CLI's own normalisation that nobody outside it can reproduce; the lock stores no version, ref, commit or date. So a subscriber could not answer 'am I current?' at all. The digest is sha256 of the file with its own version: line elided, first 12 hex -- elision makes it a fixed point, so the expected value is the same whether the stamp is right, wrong, malformed or absent.

**Alternatives considered:** A one-line body footer carrying the route home: rejected on measurement. Every footer breaks the tightest skills (test-discipline has 1 byte of headroom) and 84-322 bytes of body prose would have to come out across 4-8 skills, each needing a docs/prose-removals.md row -- which is the exact defect that gate was built for. The frontmatter is not charged by the size cap, so the route home ships there at zero body cost and zero prose deleted., Making version: REQUIRED: protocol SPEC 2.1 already marks source REQUIRED against 0 of 49 adopters, so a second unratified requirement widens that divergence. Enforced-when-present instead., A 'versions_enumerated never decreases' ratchet: unsatisfiable across machines because remote branches come and go. The generator is append-only instead, which makes the loss unrepresentable rather than detected afterwards.

**Implications:**
- The index's history rows are derived from git and validate-skills.yml checks out at depth 1, so CI cannot gate them. The index states this in its own verification block rather than leaving it implied.
- Every skill edit now needs gen_skill_versions.py --write in a full clone, or the currency gate fails the PR.
- Stamping changes every subscriber's computedHash. The algorithm is sha256(relpath || raw) over sorted files -- verified 40/42 across four locks with three controls at zero -- so census_counters.py CATALOG_HASH_ALGO could now be retired; not done here, because compute_catalog_hash takes a single file path and every catalog skill happens to be single-file today.

---

## 2026-08-18 03:14 - Apply the panel's five fixes to PR #238: byte-identity, mirror ordering, exit-code parity, history-order pinning, and the index-absence gate

**Reasoning:** an adversarial panel ruled MERGE WITH FIX with five reproduced, controlled defects: validate_skills.py digested decoded text while every other tool digests bytes, making the printed remedy a no-op on a lone-CR file; skills_current.py's repo-mirrored branch sat below the history branch and told an authoring repo to overwrite its own source from a mirror; its exit-code table promised 1 for stale-or-diverged while the code silently returned 0 for retired; gen_skill_versions.py's three sort sites had no test pinning ascending chronological order, so a reverse=True mutation passed 361/361; and validate_skills.py's 'if versions_path.exists()' turned a deleted index into a silent pass. A sixth item (stamp_versions.py's deleted fixed-point assertion) rested on a false comment: a persistent unquoting regression in skill_version.version_line is accepted by every surviving assertion

**Alternatives considered:** leave the exit-code and index-absence questions to a follow-up PR rather than deciding them here, auto-provision docs/skill-versions.json globally via a session-scoped autouse fixture instead of lazily inside SkillTree.validate()

**Implications:**
- SkillTree.validate() now auto-provisions a matching docs/skill-versions.json when a test hasn't written its own, computed fresh at call time so a post-creation mutation is still reflected -- a test that wants the gate with zero scaffolding calls validate_skills.run() directly instead (see test_an_absent_index_is_rejected)
- retired now exits 1 from skills_current.py; test_a_retired_skill_never_produces_an_install_instruction and the module docstring were updated to match, and unpublished is pinned to stay at exit 0 by a new end-to-end test

---

