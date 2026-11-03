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
import subprocess
from pathlib import Path

import pytest

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


def _info_exclude_patterns() -> list[str]:
    """The live, machine-local exclude patterns this clone actually has,
    `**/`-prefix stripped -- comparable to plain repo-relative .gitignore
    entries. `--git-common-dir` rather than `--git-dir`: in a worktree
    `.git` is a per-worktree file, but `info/exclude` lives in the ONE
    shared git directory every worktree of this checkout points back to.
    """
    common = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "--git-common-dir"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    exclude = Path(common)
    if not exclude.is_absolute():
        exclude = REPO_ROOT / exclude
    exclude = exclude / "info" / "exclude"
    if not exclude.exists():
        pytest.skip(f"no {exclude} on this checkout -- nothing to compare")
    patterns = []
    for line in exclude.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        patterns.append(line[len("**/"):] if line.startswith("**/") else line)
    return patterns


def test_gitignore_stays_in_sync_with_the_live_info_exclude():
    """The hardcoded list above pins a snapshot; this pins the INVARIANT --
    the two tests above pass unchanged even if a new pattern is added to
    `.git/info/exclude` (this clone's own, untracked, per #221) and never
    mirrored into `.gitignore`, which is exactly the leak #221 reports and
    exactly the drift the .gitignore's own comment says this file guards
    against. Reads the live file rather than a second hardcoded copy, or the
    guard would drift out of sync with the thing it is meant to catch drifting.
    """
    live = _info_exclude_patterns()
    text = _gitignore_text()
    missing = [p for p in live if p not in text]
    assert not missing, (
        "this clone's .git/info/exclude has pattern(s) .gitignore does not "
        f"mirror -- docs/file-structure.md will leak them on regen (#221): "
        f"{missing}"
    )
