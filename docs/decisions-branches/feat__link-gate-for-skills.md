← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 09:14 - check-links never read skills/ -- the required merge gate reported green over the one directory the catalog exists to protect; build a relative-link resolver into validate_skills.py that actually walks the tree

**Reasoning:** issue #234 reproduced it with a control: an identical broken link resolves clean in a skill body and is caught in README.md. The mandated route (routing through check-doc-links.yml) was ruled out for two measured reasons: its Go linkchecker install hardcodes roots (linkcheck.roots is a silent no-op against its own shipped source), and its self-heal job can push commits to a PR branch that delete the very cross-reference line the gate exists to protect

**Alternatives considered:** fetch absolute http(s) links too, for full coverage -- rejected: CI network access is flaky/slow, and a reference file's absolute GitHub URL legitimately 404s until its own PR merges (issue names PR #233's three references/ links as the live case), so a fetching checker would block its own PR. Chose to count absolute links but never fetch them, and state that bound in the gate's own output every run

**Implications:**
- the CLI's stdout contract gains a 4th line ('link scope: ...'), printed on every completed run (pass or fail) but never on the two infra-fatal early exits where there is no tree yet to state a bound about; three characterization tests in test_validate_skills_cli.py were updated to match. Fenced code blocks and inline code spans are blanked (not deleted) before the link regex runs, so link-shaped documentation examples are never flagged and line numbers stay correct. Same-page anchors (#foo) are skipped -- no path component to resolve. Heading existence inside a target file's #fragment is explicitly NOT verified -- out of scope, stated in the module comment rather than silently assumed

---

