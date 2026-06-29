---
description: Review the current branch's open PR locally, in this Claude Code session
argument-hint: "[pr-number]"
---

<!-- clud-bug-local-version: v1 -->

You are running **clud-bug** as a local code review — inside this Claude Code
session, using this session's own model tokens (Max or API, whatever you have).
No hosted App, no extra auth: you already have `gh`, `git`, and file access.

## 1. Find the PR

PR number: `$ARGUMENTS`

If `$ARGUMENTS` is empty, detect the current branch's open PR:

```bash
gh pr list --head "$(git branch --show-current)" --state open --json number --jq '.[0].number'
```

If there is no open PR, stop and tell the user to open one (or pass a PR number).

## 2. Load the review skills

Read the manifest and every referenced skill body from the checkout:

- `.claude/skills/.clud-bug.json` — which skills are installed, plus `strictMode`.
- For each installed skill, `.claude/skills/<name>/SKILL.md` — the discipline to apply.

Load skills **before** the diff. At minimum the baseline set applies:
**critical-issues-only** (flag only correctness / security / performance — skip
nits), **evidence-based-review** (quote the exact line you criticize — no
hand-waving), **respect-existing-conventions** (don't fight the codebase's
established patterns).

## 3. Fetch the diff

```bash
gh pr diff <PR_NUMBER>
```

## 4. Review

Review the diff against every loaded skill. For each finding record: `file`,
`line`, `severity` (`critical` | `minor` | `preexisting`), the `skill` that
motivated it, and a one-line `summary`. Apply the skills strictly — especially
critical-issues-only (no nits) and evidence-based-review (quote the code).

## 5. Render the review comment

Build the body in clud-bug's standard shape (omit any empty findings section):

```
## 🐛 Clud Bug review — <clean | critical findings>

**This round:** N critical · N minor · N resolved from prior · N still open

Found: N 🔴 / N 🟡 / N 🟣

### Per-skill scan
- [<skill>]: <one line on what it scanned + found>

### Critical findings
🔴 [<skill>]: <summary> (<file>:<line>).

### Minor findings
🟡 [<skill>]: <summary> (<file>:<line>).

### Pre-existing findings
🟣 [<skill>]: <summary> (<file>:<line>).

Skills referenced: [<skill>, <skill>]

<!-- written-by: @<your-gh-login> (clud-bug local-mode) -->
<!-- review-sha: <HEAD_SHA> -->
```

Get your gh login with `gh api user --jq .login` and the head sha with
`git rev-parse HEAD`. The `written-by` marker **MUST** end with
`(clud-bug local-mode)` so the bot's auto-resolve never mistakes this for a
`clud-bug[bot]` comment.

## 6. Post (or update) the comment

Look for an existing local-mode comment and edit it in place (one rolling review
comment), otherwise post a fresh one. Use the **REST** issues-comments endpoint
for the lookup — its `.id` is the **integer** comment id the PATCH endpoint needs.
(Do NOT use `gh pr view --json comments`; that returns GraphQL node IDs, which
404 on the REST PATCH and cause duplicate comments.) `gh` fills `{owner}/{repo}`.

```bash
# existing local-mode comment id (integer), if any:
EXISTING_ID=$(gh api --paginate "repos/{owner}/{repo}/issues/<PR_NUMBER>/comments" \
  --jq '[.[] | select(.body | test("written-by: @.* \\(clud-bug local-mode\\)"))] | first | .id // empty')
```

- `$EXISTING_ID` empty → `gh pr comment <PR_NUMBER> --body-file <body.md>`
- `$EXISTING_ID` set → `gh api "repos/{owner}/{repo}/issues/comments/$EXISTING_ID" -X PATCH -F body=@<body.md>`

## 7. Summarize

Print one line:
`clud-bug local-review: N critical · N minor · N preexisting — <PASS | FAIL (strictMode) | advisory>`

If `.clud-bug.json` has `strictMode: true` and there are critical findings, say
**FAIL** and tell the user to fix them before merging.

---

_Optional: if the `clud-bug-mcp` MCP server is connected, you may use its
structured tools (`load_skills_from_pr_base`, `fetch_pr_diff`,
`partition_findings_by_severity`, `emit_review_comment`) in place of the raw
`gh`/`git` calls above — same flow, with the base-ref skill read and the exact
review rendering done for you._
