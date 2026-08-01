---
name: critical-issues-only
description: PR review discipline - flag only correctness, security, and performance issues. Skip nits.
---

# Critical issues only

When reviewing a pull request, only surface issues that fall into one of these buckets:

1. **Correctness bugs** — the code does the wrong thing, mishandles a case, or breaks an existing contract.
2. **Security vulnerabilities** — injection, auth bypass, secret exposure, unsafe deserialization, SSRF, etc.
3. **Performance problems** — algorithmic blowups, N+1 queries, memory leaks, blocking calls in hot paths.
4. **Missing or broken test coverage** for new code paths that meaningfully change behavior.

## Do not surface

- Style preferences, formatting, naming preferences.
- Architectural rewrites unless the existing approach is actively broken.
- "You could also..." suggestions that aren't bugs.
- Nitpicks the author can fix in 30 seconds and don't change behavior.

## How to phrase findings

- One concrete issue per comment. No bundling unrelated nits.
- Quote the specific line or block being criticized.
- Say what's wrong, then what to do about it. Skip the throat-clearing.

If the diff has no issues in the four buckets above, post a single short comment confirming that — don't invent problems.
