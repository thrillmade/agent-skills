← back to [docs/timeline.md](../timeline.md)

## 2026-08-17 17:46 - Per-skill content versioning: a stamp a subscriber can recompute, an index they can look it up in

**Reasoning:** npx skills add copies SKILL.md wholesale and records a computedHash from the CLI's own normalisation that nobody outside it can reproduce; the lock stores no version, ref, commit or date. So a subscriber could not answer 'am I current?' at all. The digest is sha256 of the file with its own version: line elided, first 12 hex -- elision makes it a fixed point, so the expected value is the same whether the stamp is right, wrong, malformed or absent.

**Alternatives considered:** A one-line body footer carrying the route home: rejected on measurement. Every footer breaks the tightest skills (test-discipline has 1 byte of headroom) and 84-322 bytes of body prose would have to come out across 4-8 skills, each needing a docs/prose-removals.md row -- which is the exact defect that gate was built for. The frontmatter is not charged by the size cap, so the route home ships there at zero body cost and zero prose deleted., Making version: REQUIRED: protocol SPEC 2.1 already marks source REQUIRED against 0 of 49 adopters, so a second unratified requirement widens that divergence. Enforced-when-present instead., A 'versions_enumerated never decreases' ratchet: unsatisfiable across machines because remote branches come and go. The generator is append-only instead, which makes the loss unrepresentable rather than detected afterwards.

**Implications:**
- The index's history rows are derived from git and validate-skills.yml checks out at depth 1, so CI cannot gate them. The index states this in its own verification block rather than leaving it implied.
- Every skill edit now needs gen_skill_versions.py --write in a full clone, or the currency gate fails the PR.
- Stamping changes every subscriber's computedHash. The algorithm is sha256(relpath || raw) over sorted files -- verified 40/42 across four locks with three controls at zero -- so census_counters.py CATALOG_HASH_ALGO could now be retired; not done here, because compute_catalog_hash takes a single file path and every catalog skill happens to be single-file today.

---

