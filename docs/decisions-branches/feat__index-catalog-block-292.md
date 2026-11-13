← back to [docs/timeline.md](../timeline.md)

## 2026-11-12 22:00 - The version index stays complete without a bot, and publishes the catalog's own names

**Reasoning:** After every squash merge into dev the newest version of a changed skill had no history row until someone regenerated in a full clone (#292). A bot pushing onto pull request branches has bitten this repository before, so the index is now regenerated on the promotion branch and a lag check runs only on pull requests into main, failing with the repair command when a row is missing. The index also gains a catalog block (repository and former_names) generated from the one list of names the catalog keeps, so a subscriber's tool can tell which installed copies claim this catalog, including copies installed before the rename.

**Alternatives considered:** A bot that regenerates on every merge (pushes onto protected or pull request branches). Computing the index where it is read (every reader would need a full clone). Hard-coding the catalog's former names in the reader (a second copy of the list).

**Implications:**
- dev's copy of the index may lag between promotions; the promotion branch then differs from dev in docs/skill-versions.json only. A skill changed on the promotion branch itself gets a named warning, not a row: do not change a skill there. The promotion procedure is written once, in AGENTS.md. This repository's dependabot.yml now targets dev (checker exit 1 before, 0 after). The mutation tests in test_skill_directory_mutations.py now assert which test their mutation breaks, so a broken harness can no longer make them pass.

---

