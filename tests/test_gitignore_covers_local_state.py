"""Guard for #221: logmind's `file-structure --write` walks the working
directory and honours .gitignore, but NOT .git/info/exclude (which is
per-clone and untracked). Machine-local agent/runtime state that is kept out
of git only via .git/info/exclude therefore leaks into the tracked, shared
docs/file-structure.md on every regen.

Fix on our side: mirror those patterns into the tracked .gitignore, which the
generator *does* respect. This test pins that mirror so it can't silently
drift back out of sync.

Reproduction (see issue #221):
    $ touch .claude/scheduled_tasks.lock
    $ git check-ignore -v .claude/scheduled_tasks.lock
    .git/info/exclude:8:**/.claude/scheduled_tasks.lock ...
    $ logmind file-structure --write docs/file-structure.md
    $ grep scheduled_tasks docs/file-structure.md
    │   ├── scheduled_tasks.lock          <- leaked
"""
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Mirrors the machine-local patterns historically kept only in
# .git/info/exclude (per-clone, untracked -> invisible to the generator).
# Keep in sync with .git/info/exclude if that file gains new entries.
LOCAL_STATE_PATTERNS = [
    ".claude/scheduled_tasks.lock",
    ".claude/scheduled_tasks.json",
    ".claude/routines/.state/",
    ".claude/worktrees/",
    ".claude/checkpoints/",
    ".claude/mailbox/",
    ".claude/agent-registry.json",
    ".claude/agent-memory-local",
    ".claude/first-run",
    ".claude/assistant-daemon-state.json",
]


def _gitignore_text():
    return (REPO_ROOT / ".gitignore").read_text()


def test_gitignore_covers_known_local_state_patterns():
    text = _gitignore_text()
    missing = [p for p in LOCAL_STATE_PATTERNS if p not in text]
    assert not missing, (
        "docs/file-structure.md leaks these paths (issue #221) because "
        f".gitignore is missing them: {missing}"
    )


def test_control_a_tracked_pattern_is_found_by_the_same_check():
    # Control: prove the assertion above can actually fail by checking a
    # pattern we know IS present (the existing .logmind/cache/ entry).
    text = _gitignore_text()
    assert ".logmind/cache/" in text
