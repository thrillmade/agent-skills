← back to [docs/timeline.md](../timeline.md)

## 2026-08-24 08:36 - Ship a three-field skill identity format (version/digest/origin), replacing the single version: field that held a digest and hid its route home in a YAML comment

**Reasoning:** version answered only 'same or different', never 'newer'; the origin URL lived in a comment yaml.safe_load discards before any program sees it. Splitting into an ordered human semver, a recomputable digest, and a real machine-readable origin field fixes both, per CEO ruling on the exact shape and the MAJOR/MINOR/author-decision, PATCH/stamper-auto-bump semver rule

**Alternatives considered:** keep the single digest-only field and add a separate lockfile-style pin elsewhere; rejected because it does not fix the origin-in-a-comment defect and adds a second artifact to keep in sync, hand-assign each of the 56 skills an initial semver from their commit history; rejected in favor of a reproducible, code-only rule: any file with no valid MAJOR.MINOR.PATCH claim (missing, or the old scheme's digest-shaped value, which SEMVER_RE never matches) seeds 1.0.0 -- identical for a brand-new file and for all 56 migrated ones, not hand-picked

**Implications:**
- all three identity lines (not just version:) must now be elided before hashing, or stamping would move the digest it is supposed to hold stable -- verified: stamping the whole catalog left every one of the 56 digests byte-identical to what dev published before this change
- stamp() is no longer a pure function of content alone for the version field: it reads its own file's prior version/digest claim to decide whether to bump PATCH, seed 1.0.0, or leave the semver untouched -- documented as the one deliberate exception in skill_version.py's module docstring
- validate_skills.py now gates the three fields together: naming one without the other two is a new error class (opted-in-but-incomplete), not silently tolerated as one-third done
- docs/skill-versions.json gains a version key alongside current at both the per-skill and per-history-row level, appended without disturbing the append-only current/v history the existing gate depends on; history rows from before this format existed read version: null, which is not fillable retroactively (no semver ever existed for those commits)

---

