← back to [docs/timeline.md](../timeline.md)

## 2026-08-14 21:44 - Extract the skill validator from its heredoc and give the repo a real test job

**Reasoning:** Every gate this catalog plans is specified as mutation-tested before it ships, and that phrase had no referent. The validator was a 342-line inline python heredoc inside validate-skills.yml — not importable, not callable, impossible to run locally. test.yml's only step was 'run: true', a job that always passes and checks nothing. There were zero test files. So proving a gate worked meant breaking a file, pushing, and watching CI, which is unrepeatable and leaves no regression guard. The body is now .github/scripts/validate_skills.py exposing run(root) plus a thin main(), with 107 characterization tests locking in today's behaviour for every existing rule. Byte-identical stdout and exit status were verified against the pre-extraction heredoc across 46 fixture trees before anything else was trusted.

**Alternatives considered:** Write the new gates first and extract later, which ships six gates that cannot be proven; add tests around the heredoc without extracting, which is not possible because a heredoc cannot be imported

**Implications:**
- The suite is mutation-proven rather than asserted. Seven mutations were applied to the real file, each grepped to confirm it landed, each producing a red run, each restored and re-verified by sha256; zero survived. I re-ran one independently — raising the size limit to 9000 turns two tests red and restoring returns 107 green — because a reviewer's own claim that a suite has teeth is not evidence
- My stated reason for the coverage guard was wrong and the guard is kept anyway. I claimed the validator could print OK: 0 skills validated cleanly from a wrong directory — a green build over nothing. Control-tested, it does not: a missing skills/ exits 1 with an error, and an empty one exits 1 with a different error. Both early exits already close that path. The guard is defense in depth for a future edit to those exits and for run() now being callable with an arbitrary root, not the live bug I described
- The extraction opens a hole it also closes: .github/scripts/validate_skills.py is added to both paths filters, because without it a pull request editing only the extracted script would not run the gate it edits

---

