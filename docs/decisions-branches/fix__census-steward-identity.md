← back to [docs/timeline.md](../timeline.md)

## 2026-08-23 20:06 - File census issues as the steward App, not github-actions[bot] (#183)

**Reasoning:** The App has held Issues: write since 2026-07-17; the real blocker was the App token's hardcoded repositories list omitting agent-skills, not a missing grant — verified via gh api /apps/skdd-steward and the repo scope in skill-census.yml itself, both corrected in the issue thread before this fix

**Alternatives considered:** Grant something new to the App (nothing to grant) or leave GH_TOKEN on github.token permanently (keeps every census issue misattributed to github-actions[bot], which is the conformance gap #183 exists to close and blocks skdd#9's cross-repo notification)

**Implications:**
- Removed issues: write from the job-level permissions block since nothing uses github.token for issues anymore (only checkout remains, needing contents:read); the App token step sets no permission-<x> inputs so it inherits the installation's full permission set by default (no permission-issues: write input needed); added a token-failure test proving the filing step still fails loud rather than silently filing nothing when the token can't write, since that shape (#250) is this file's most-repeated defect

---

