← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 04:56 - Mirror .git/info/exclude machine-local patterns into .gitignore (#221)

**Reasoning:** logmind's file-structure --write generator honours .gitignore but not .git/info/exclude (per-clone, untracked), so agent/runtime scratch state (scheduled_tasks.lock, worktrees/, mailbox/, etc.) leaked into the tracked docs/file-structure.md every time the generator ran. Also confirmed logmind's matcher ignores **/-prefixed doublestar globs even though git honours them, so the mirror must use plain repo-relative paths, not a literal copy of the exclude file.

**Alternatives considered:** Patch logmind's generator directly — refused per the issue's own scope note: logmind is heads-down on 2.0.0 and this is explicitly not worth interrupting; also this repo does not own that binary's source.

**Implications:**
- The worktree-root-name bug (rebase renaming the tree root to the worktree's basename) is untouched by this fix and remains fully upstream — no repo-local mitigation exists for it since the generator derives the label from cwd inside logmind's own code.

---

